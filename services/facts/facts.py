"""facts: returns a random question and fact about Finland for a topic, from SQLite.

Telemetry: HTTP server spans (FastAPI), DB client spans (sqlite3),
observable gauge factbot.facts.count, WARNING logs on failures.
"""
import os
import random
import sqlite3
import time
from contextlib import closing, nullcontext

import uvicorn
from fastapi import FastAPI, HTTPException
from opentelemetry import metrics, trace

from app_logging import get_logger, server_config
from finland_facts import FINLAND_FACTS

try:  # keeps one-off startup SQL from producing orphan traces
    from opentelemetry.instrumentation.utils import suppress_instrumentation
except ImportError:  # older instrumentation versions
    suppress_instrumentation = nullcontext

DB_PATH = os.environ.get("FACTS_DB", "/tmp/finland_facts.db")
ERROR_RATE = float(os.environ.get("FACTS_ERROR_RATE", "0") or 0)
SLOW_MS = int(os.environ.get("FACTS_SLOW_MS", "0") or 0)


tracer = trace.get_tracer("factbot.facts")
meter = metrics.get_meter("factbot.facts")
log = get_logger("factbot.facts")

_fact_count = 0


def init_db() -> None:
    global _fact_count
    with suppress_instrumentation(), closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS facts ("
            "id INTEGER PRIMARY KEY, topic TEXT NOT NULL, "
            "question TEXT NOT NULL, fact TEXT NOT NULL)"
        )
        cur.execute("SELECT COUNT(*) FROM facts")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO facts (topic, question, fact) VALUES (?, ?, ?)",
                [(t, q, f) for t, entries in FINLAND_FACTS.items() for q, f in entries],
            )
            conn.commit()
        cur.execute("SELECT COUNT(*) FROM facts")
        _fact_count = cur.fetchone()[0]


def _observe_fact_count(_options):
    yield metrics.Observation(_fact_count)


meter.create_observable_gauge(
    "factbot.facts.count",
    callbacks=[_observe_fact_count],
    unit="{fact}",
    description="Number of Finland questions and facts stored in the database",
)

app = FastAPI(title="facts")


@app.get("/facts/{topic}")
def get_fact(topic: str):
    topic = topic.lower()
    trace.get_current_span().set_attribute("factbot.topic", topic)

    if SLOW_MS > 0:
        with tracer.start_as_current_span("facts.simulated_delay") as span:
            span.set_attribute("factbot.delay_ms", SLOW_MS)
            time.sleep(SLOW_MS / 1000)

    if ERROR_RATE > 0 and random.random() < ERROR_RATE:
        log.warning("Injected failure for topic=%s", topic, extra={"factbot.topic": topic})
        raise HTTPException(status_code=500, detail="injected failure")

    # Use an explicit cursor: the sqlite3 instrumentation traces cursor.execute,
    # not the connection.execute shortcut.
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT question, fact FROM facts WHERE topic = ? ORDER BY RANDOM() LIMIT 1",
            (topic,),
        )
        row = cur.fetchone()

    if row is None:
        log.warning("Unknown topic=%s", topic, extra={"factbot.topic": topic})
        raise HTTPException(status_code=404, detail=f"no Finland facts about '{topic}'")

    return {"topic": topic, "question": row[0], "fact": row[1]}


@app.get("/topics")
def list_topics():
    return {"topics": sorted(FINLAND_FACTS)}


if __name__ == "__main__":
    init_db()
    uvicorn.run(app, **server_config())
