#!/bin/bash

# Start Ollama in the background.
ollama serve &
# Record the Process ID.
pid=$!

# Wait for a few seconds to allow Ollama to start.
sleep 5

# Pull the specified model
echo "🔴 Retrieving model llama3.1:latest..."
ollama pull llama3.1:latest
echo "🟢 Model pulled successfully!"

# Wait for Ollama server to run continuously.
wait $pid
