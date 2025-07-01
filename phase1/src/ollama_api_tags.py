import requests

host = "http://localhost:11434" # WSL ollama host
#host = "http://localhost:11434" # windows ollama host

response = requests.get(f"{host}/api/tags")
print(response.json())
