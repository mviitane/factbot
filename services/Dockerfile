# Shared image recipe for all FactBot services; SERVICE selects which one.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG SERVICE
# Read at runtime by entrypoint.sh to pick <service>.py and the process name.
ENV SERVICE=${SERVICE}
WORKDIR /app

COPY ${SERVICE}/requirements.txt ./requirements.txt
# opentelemetry-bootstrap installs instrumentation packages matching the
# libraries in requirements.txt, at versions compatible with the SDK.
RUN pip install -r requirements.txt \
 && opentelemetry-bootstrap -a install

COPY common/ ./
COPY ${SERVICE}/ ./

USER nobody
CMD ["/bin/sh", "/app/entrypoint.sh"]
