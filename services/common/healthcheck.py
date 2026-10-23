"""Container healthcheck: a plain TCP connect, so it creates no spans or metrics."""
import os
import socket
import sys

port = int(os.environ.get("SERVER_PORT", "8080"))
try:
    with socket.create_connection(("127.0.0.1", port), timeout=2):
        pass
except OSError:
    sys.exit(1)
