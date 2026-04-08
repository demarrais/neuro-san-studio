#!/bin/bash
echo "Starting ChromaDB..."
chroma run --path ./ravi_chroma_db &
CHROMA_PID=$!
sleep 3

echo "Verifying ChromaDB..."
curl -s http://localhost:8000/api/v2/heartbeat && echo "✅ ChromaDB ready" || echo "❌ ChromaDB failed"

echo "Starting agent server..."
python -m run
