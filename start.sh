#!/bin/bash

cd ~/Documents/RAG_MCP
set -o allexport
source .env 2>/dev/null
set +o allexport
uv run rag.py
