# Use the official Ollama image as the base
FROM ollama/ollama:latest

# Copy the wait script to the Docker image
COPY ./wait_for_ollama.sh /wait_for_ollama.sh

# Ensure the script is executable
RUN chmod +x /wait_for_ollama.sh

# Expose the port for the Ollama server
EXPOSE 11434

# Set the entrypoint to the wait script
ENTRYPOINT ["/bin/sh", "/wait_for_ollama.sh"]
