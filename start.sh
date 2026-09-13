#!/usr/bin/env bash
# Quickstart script for AegisClinical Multi-Agent CDSS

set -e

echo "=== AegisClinical Multi-Agent CDSS Starting ==="

# Check virtualenv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
fi
.venv/bin/pip install -q -r requirements.txt

# Build frontend if dist does not exist
if [ ! -d "frontend/dist" ]; then
    echo "Building React frontend..."
    npm --prefix frontend install
    npm --prefix frontend run build
fi

# Check Ollama
if command -v ollama &> /dev/null; then
    echo "Ollama is installed. Verifying llama3.2:3b model..."
    ollama list | grep -q "llama3.2:3b" || echo "Tip: Run 'ollama pull llama3.2:3b' for optimal on-device synthesis."
else
    echo "Notice: Ollama not found. System will run with deterministic clinical rules fallback."
fi

echo "Starting AegisClinical Server at http://localhost:8000..."
.venv/bin/python api.py
