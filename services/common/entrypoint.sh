#!/bin/sh
# Starts one FactBot service under OpenTelemetry auto-instrumentation.
#
# The Python SDK does not emit process.executable.name by default, and its
# optional process detector would report just "python" for every service.
# Like otel-java-simple's entrypoint.sh, set a descriptive name explicitly.
# Each service runs as its own <service>.py script, so the host Collector's
# process metrics (which see "python" for all three) can be renamed to match
# by command line.
set -e

PROCESS_EXECUTABLE_NAME="${PROCESS_EXECUTABLE_NAME:-factbot-${SERVICE}}"
case ",${OTEL_RESOURCE_ATTRIBUTES:-}," in
  *,process.executable.name=*) ;;
  *) export OTEL_RESOURCE_ATTRIBUTES="${OTEL_RESOURCE_ATTRIBUTES:+${OTEL_RESOURCE_ATTRIBUTES},}process.executable.name=${PROCESS_EXECUTABLE_NAME}" ;;
esac

exec opentelemetry-instrument python "/app/${SERVICE}.py"
