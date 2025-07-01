# This script sends a POST request to the Ollama API with a JSON payload.
curl -v \
   -H "Content-Type: application/json" \
   -d @payload.json \
   http://localhost:11434/v1/chat/completions
