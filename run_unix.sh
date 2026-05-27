#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "Backend iniciado en http://127.0.0.1:8000"
echo "Recuerda tener Ollama abierto y un modelo instalado, por ejemplo: ollama pull qwen2.5:7b"
uvicorn backend.main:app --host 127.0.0.1 --port 8000
