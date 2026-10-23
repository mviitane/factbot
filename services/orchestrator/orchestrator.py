"""orchestrator: fetches a question and fact about Finland, asks Gemma to answer.

Telemetry: HTTP server/client spans, an invoke_agent span that groups the
facts lookup and the LLM call, GenAI client spans and metrics
(opentelemetry-instrumentation-openai-v2), and the single INFO log
record per request that the demo's log budget is built around.
"""
import os

import httpx
import openai
import uvicorn
from fastapi import FastAPI, HTTPException
from opentelemetry import trace

from app_logging import get_logger, server_config

FACTS_URL = os.environ.get("FACTS_URL", "http://127.0.0.1:8083")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "factbot-gemma")
LLM_TIMEOUT_S = float(os.environ.get("LLM_TIMEOUT_S", "50"))
AGENT_NAME = "FactBot"

SYSTEM_PROMPT = (
    "You are FactBot, a friendly guide to Finland. Answer the question in one or two "
    "short sentences using only the given fact. Do not add new information."
)

log = get_logger("factbot.orchestrator")
tracer = trace.get_tracer("factbot.orchestrator")

# Clients are created after opentelemetry-instrument has patched the libraries.
facts_client = httpx.Client(timeout=10)
llm = openai.OpenAI(
    base_url=LLM_BASE_URL,
    api_key=os.environ.get("OPENAI_API_KEY", "ollama"),
    timeout=LLM_TIMEOUT_S,
    max_retries=0,  # retries would hide latency and errors from the traces
)

app = FastAPI(title="orchestrator")


@app.get("/answer")
def answer(topic: str):
    trace.get_current_span().set_attribute("factbot.topic", topic)

    # GenAI agent span (semconv invoke_agent) so the facts lookup and the
    # chat span appear as one FactBot agent run in Dynatrace AI Observability.
    with tracer.start_as_current_span(
        f"invoke_agent {AGENT_NAME}",
        kind=trace.SpanKind.INTERNAL,
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": AGENT_NAME,
            "gen_ai.provider.name": "openai",
            "gen_ai.request.model": LLM_MODEL,
            "factbot.topic": topic,
        },
    ) as agent_span:
        return _run_agent(topic, agent_span)


def _run_agent(topic: str, agent_span: trace.Span) -> dict:
    try:
        resp = facts_client.get(f"{FACTS_URL}/facts/{topic}")
    except httpx.HTTPError as exc:
        log.warning("facts unreachable: %s", exc, extra={"factbot.topic": topic})
        raise HTTPException(status_code=502, detail="facts service unreachable")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=resp.json().get("detail"))
    if resp.status_code != 200:
        log.warning("facts returned %s", resp.status_code, extra={"factbot.topic": topic})
        raise HTTPException(status_code=502, detail="facts service error")

    data = resp.json()
    question, fact = data["question"], data["fact"]

    try:
        completion = llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}\nFact: {fact}"},
            ],
            max_tokens=80,
            temperature=0.7,
        )
    except openai.APITimeoutError:
        log.warning("LLM timed out after %ss", LLM_TIMEOUT_S, extra={"factbot.topic": topic})
        raise HTTPException(status_code=504, detail="LLM timeout")
    except openai.APIError as exc:
        log.warning("LLM error: %s", exc, extra={"factbot.topic": topic})
        raise HTTPException(status_code=502, detail="LLM error")

    text = (completion.choices[0].message.content or "").strip()
    usage = completion.usage
    in_tokens = usage.prompt_tokens if usage else None
    out_tokens = usage.completion_tokens if usage else None
    agent_span.set_attribute("gen_ai.response.model", completion.model or LLM_MODEL)
    if in_tokens is not None:
        agent_span.set_attribute("gen_ai.usage.input_tokens", in_tokens)
    if out_tokens is not None:
        agent_span.set_attribute("gen_ai.usage.output_tokens", out_tokens)

    log.info(
        "Answered topic=%s input_tokens=%s output_tokens=%s",
        topic,
        in_tokens,
        out_tokens,
        extra={
            "factbot.topic": topic,
            "factbot.question": question,
            "factbot.answer_chars": len(text),
        },
    )

    return {
        "topic": topic,
        "question": question,
        "answer": text,
        "fact": fact,
        "model": LLM_MODEL,
    }


if __name__ == "__main__":
    uvicorn.run(app, **server_config())
