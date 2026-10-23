"""Logging setup shared by all services.

opentelemetry-instrument attaches an OTLP handler to the root logger before
the service script runs. The root logger stays at WARNING, so chatty libraries (httpx,
uvicorn) don't export INFO logs. Each service's own logger gets LOG_LEVEL,
which is how the orchestrator alone emits one INFO record per request.
"""
import logging
import os


def get_logger(name: str) -> logging.Logger:
    root = logging.getLogger()
    if not any(getattr(h, "_factbot_console", False) for h in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        console._factbot_console = True
        root.addHandler(console)

    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get("LOG_LEVEL", "WARNING").upper())
    return logger


def server_config() -> dict:
    return {
        "host": os.environ.get("SERVER_HOST", "127.0.0.1"),
        "port": int(os.environ.get("SERVER_PORT", "8080")),
        "log_level": "warning",
        "access_log": False,
    }
