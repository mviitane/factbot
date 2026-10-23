# FactBot — OpenTelemetry GenAI demo

Three small Python microservices and a local Gemma model that produce a steady, low-volume stream of OpenTelemetry traces, metrics, and logs (about one of each per minute) for the OTel Collector running on this host.

```
ticker ─▶ frontend :8081 ─▶ orchestrator :8082 ─▶ facts :8083 (SQLite)
                                  │
                                  └─▶ ollama :11434 (factbot-gemma = gemma3:270m)
                                         ▲ traced by obi (eBPF)
```

Once a minute the ticker asks FactBot something about Finland. The frontend picks a random topic, the facts service returns a ready-made question and fact for it, and the orchestrator asks Gemma to answer the question using only that fact.

Example response:

```json
{
  "topic": "technology",
  "question": "Who invented SSH?",
  "answer": "SSH was created by Tatu Ylönen in 1995 at the Helsinki University of Technology.",
  "fact": "Tatu Ylönen created the SSH protocol in 1995 at the Helsinki University of Technology.",
  "model": "factbot-gemma"
}
```

## Web page

The frontend serves a small web page at `http://127.0.0.1:8081/` (no external assets, no RUM). Pick a topic or "Surprise me" to get an answer; the page shows the model, the round-trip time, and the trace ID (also returned in the `X-Trace-Id` response header) so you can find the request in Dynatrace. The frontend listens on all interfaces (`FRONTEND_HOST=0.0.0.0` in `.env`), so it is also reachable from the LAN at `http://<host-ip>:8081/`; set `FRONTEND_HOST=127.0.0.1` to keep it local and use an SSH tunnel instead (`ssh -L 8081:127.0.0.1:8081 <host>`). The orchestrator, facts, and Ollama always listen on 127.0.0.1 only. Each click creates one extra trace, the same as `make once`.

## Finland content

There are 23 questions across nine topics: lakes, saunas, nature, lapland, islands, history, languages, technology, and culture. They live in `services/facts/finland_facts.py` as `(question, fact)` pairs. To add your own, edit that file (and `TOPICS` in `services/frontend/frontend.py` if you add a topic), then run `make up` to rebuild. `GET http://127.0.0.1:8083/topics` lists the loaded topics.

## Requirements

Linux with Docker Engine and the Compose plugin. The containers use host networking so that `localhost:4318` reaches the Collector running as a host service; no Collector configuration change is needed. (Docker Desktop for Linux runs containers in a VM, where host networking does not reach the real host.)

Disk: about 3.5 GB for the Ollama image plus about 300 MB for the model, and roughly 200 MB per Python image.

## Start and stop

| Action | Command | Make shortcut |
|---|---|---|
| Build and start | `docker compose up -d --build` | `make up` |
| Pause (keep containers) | `docker compose stop` | `make stop` |
| Resume | `docker compose start` | `make start` |
| Stop and remove containers (model stays cached) | `docker compose down` | `make down` |
| Remove everything, including the model and images | `docker compose down -v --rmi local` | `make clean` |
| Follow logs | `docker compose logs -f` | `make logs` |
| CPU and memory per container | `docker stats` | `make stats` |
| One extra trace on demand | `curl "http://127.0.0.1:8081/fact?topic=saunas"` | `make once` |

The first start pulls the model and can take a few minutes. Containers have no restart policy, so nothing starts at boot.

## Services and what they emit

| Service | Instrumentation | Notable telemetry |
|---|---|---|
| frontend | Zero-code (FastAPI, httpx) | Serves the web page; root SERVER span; counter `factbot.requests` by `factbot.topic` and `factbot.outcome` |
| orchestrator | Zero-code (FastAPI, httpx, OpenAI v2) plus one manual span | `invoke_agent FactBot` agent span wrapping a GenAI client span for `factbot-gemma` with token usage; GenAI token usage and operation duration histograms; one INFO log per request |
| facts | Zero-code (FastAPI, sqlite3) | DB client span for the SQL lookup; observable gauge `factbot.facts.count` |
| ollama | OBI (eBPF), no code or image changes | SERVER span for `POST /v1/chat/completions`, joined to the orchestrator's trace; HTTP server RED metrics |

All services export OTLP/HTTP to `http://localhost:4318` with `OTEL_TRACES_EXPORTER`, `OTEL_METRICS_EXPORTER`, and `OTEL_LOGS_EXPORTER` set to `otlp`. `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf` is also set, because the Python SDK otherwise defaults to gRPC, which listens on 4317. `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` switches the OpenAI instrumentation to the latest GenAI semantic conventions (`gen_ai.provider.name`, `gen_ai.input.messages`, `gen_ai.output.messages`), which Dynatrace AI Observability uses. Resource attributes include `service.namespace=factbot` and `deployment.environment.name=local-demo`, which makes the demo easy to filter.

Ollama has no OpenTelemetry support of its own, so the `obi` container ([OpenTelemetry eBPF Instrumentation](https://opentelemetry.io/docs/zero-code/obi/)) instruments it from the kernel. It is scoped to Ollama only: it shares the ollama container's PID namespace, so it cannot see any other process on the host, and `obi/config.yml` limits it to `ollama serve` on the API port and excludes the `llama-server` runner, whose internal calls would add noise. OBI needs `privileged` to load eBPF programs. Set `OBI_TRACE_PRINTER=text` in `.env` to also print each captured request to `docker compose logs obi`.

## Telemetry budget

| Signal | Rate |
|---|---|
| Traces | 1 per minute, about 20 spans across four services (6 of them from OBI in ollama) |
| Metrics | 1 export per service per minute (`OTEL_METRIC_EXPORT_INTERVAL=60000`) |
| Logs | About 1 per minute from the orchestrator; frontend and facts log only warnings and errors |

Health checks, including Ollama's, use a plain TCP connect, so they produce no spans or HTTP metrics. `CAPTURE_GENAI_CONTENT` defaults to `span_only`, which records prompts and completions as attributes on the chat span; `event_only` or `span_and_event` add a few log events per request, and `no_content` turns capture off.

## Resource limits

Every container is pinned to the same logical CPU (`DEMO_CPU`, default 7), so the whole demo shares one CPU. Gemma runs with one thread, a 1K context, and at most 80 output tokens.

| Container | Memory limit | Typical use |
|---|---|---|
| ollama | 1 GB | 0.5–0.7 GB with the model loaded |
| orchestrator | 256 MB | ~100 MB |
| frontend | 160 MB | ~70 MB |
| facts | 128 MB | ~60 MB |
| obi | 768 MB | ~350 MB (eBPF maps count against the limit; 256 MB is too small) |
| ticker | 32 MB | a few MB |

Ollama keeps the model loaded for 10 minutes after the last request, so it stays warm at the one-minute cadence and frees its memory soon after you stop the ticker.

## Configuration

All settings live in `.env`: CPU index, Collector endpoint, ports, tick interval, and the fault-injection knobs. After editing `.env`, run `docker compose up -d` to apply.

Fault injection: `FACTS_ERROR_RATE=0.2` makes 20% of fact lookups return HTTP 500, which surfaces as error spans in all three services plus WARNING logs. `FACTS_SLOW_MS=3000` adds a 3-second `facts.simulated_delay` span to every lookup.

Model tuning: edit `ollama/Modelfile`, then run `FORCE_RECREATE=1 docker compose up -d` to rebuild `factbot-gemma`.

## Troubleshooting

No telemetry arriving: check that the Collector's OTLP HTTP receiver is on port 4318 (`ss -ltnp | grep 4318`) and look for exporter errors with `docker compose logs orchestrator`.

Port already in use: change `FRONTEND_PORT`, `ORCHESTRATOR_PORT`, `FACTS_PORT`, or `OLLAMA_PORT` in `.env`. Set `OLLAMA_PORT` to something like 11435 if Ollama is also installed natively.

`cpuset` error at start: `DEMO_CPU` must be a valid CPU index; `nproc` shows how many you have.

Frontend responds 504: the LLM took longer than 50 seconds, usually only on the first request while the model loads.

## Ideas for later

Point OBI at one of the Python services as well and compare its spans to the SDK spans. Add a mock LLM service for deterministic latency and token counts. Remove `OTEL_SEMCONV_STABILITY_OPT_IN` to compare the older GenAI semantic conventions with the latest ones.

## License

Apache License 2.0. See [LICENSE](LICENSE).
