"""frontend: public entry point. Serves the FactBot web page and the /fact API,
which picks a random Finland topic (unless one is given) and asks the orchestrator.

Telemetry: root HTTP server span, HTTP client span, custom counter
factbot.requests (by topic and outcome), WARNING logs on failures.
"""
import os
import random
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from opentelemetry import metrics, trace

from app_logging import get_logger, server_config

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://127.0.0.1:8082")

# Must match the topics seeded in the facts service.
TOPICS = [
    "lakes", "saunas", "nature", "lapland", "islands",
    "history", "languages", "technology", "culture",
]

INDEX_HTML = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")

log = get_logger("factbot.frontend")
meter = metrics.get_meter("factbot.frontend")
requests_counter = meter.create_counter(
    "factbot.requests",
    unit="{request}",
    description="Fact requests handled by the frontend",
)

client = httpx.AsyncClient(timeout=58)
app = FastAPI(title="frontend")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    return INDEX_HTML


@app.get("/topics")
async def topics():
    return {"topics": TOPICS}


@app.get("/fact")
async def fact(response: Response, topic: str | None = None):
    topic = (topic or random.choice(TOPICS)).lower()
    span = trace.get_current_span()
    span.set_attribute("factbot.topic", topic)
    # Lets the web page show the trace ID, to look the request up in Dynatrace.
    trace_id = format(span.get_span_context().trace_id, "032x")
    response.headers["X-Trace-Id"] = trace_id

    try:
        resp = await client.get(f"{ORCHESTRATOR_URL}/answer", params={"topic": topic})
    except httpx.HTTPError as exc:
        requests_counter.add(1, {"factbot.topic": topic, "factbot.outcome": "error"})
        log.warning("orchestrator unreachable: %s", exc, extra={"factbot.topic": topic})
        raise HTTPException(
            status_code=502, detail="orchestrator unreachable", headers={"X-Trace-Id": trace_id}
        )

    if resp.status_code != 200:
        requests_counter.add(1, {"factbot.topic": topic, "factbot.outcome": "error"})
        log.warning(
            "orchestrator returned %s", resp.status_code, extra={"factbot.topic": topic}
        )
        try:
            detail = resp.json().get("detail")
        except ValueError:
            detail = resp.text
        raise HTTPException(
            status_code=resp.status_code, detail=detail, headers={"X-Trace-Id": trace_id}
        )

    requests_counter.add(1, {"factbot.topic": topic, "factbot.outcome": "ok"})
    return resp.json()


if __name__ == "__main__":
    uvicorn.run(app, **server_config())
