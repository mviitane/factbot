#!/bin/sh
# One-shot setup: pull Gemma and create the tuned factbot-gemma model.
set -e

if [ "${FORCE_RECREATE}" != "1" ] && ollama show factbot-gemma >/dev/null 2>&1; then
  echo "factbot-gemma already exists, skipping setup (set FORCE_RECREATE=1 to rebuild)."
  exit 0
fi

echo "Pulling gemma3:270m (about 300 MB, first run only)..."
ollama pull gemma3:270m

echo "Creating factbot-gemma from Modelfile..."
ollama create factbot-gemma -f /setup/Modelfile

echo "Model ready."
