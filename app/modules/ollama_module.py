import requests
import logging

logger = logging.getLogger(__name__)

# Basic cache to avoid hitting the LLM too often
# We can refresh it periodically (e.g., hourly)
ollama_cache = {"message": "Loading AI Insight..."}

def fetch_data(config: dict, context_data: dict = None) -> dict:
    """
    Fetches a short generated response from a local Ollama instance.
    Uses 'url' and 'model' from config.
    """
    global ollama_cache

    url = config.get("url", "http://host.docker.internal:11434/api/generate")
    model = config.get("model", "llama3")
    prompt = config.get("prompt", "You are a sassy AI. Give me a 1 sentence greeting.")

    # Context data can be passed in (e.g. current weather or stats) to make the prompt dynamic
    if context_data:
         # simple string substitution if the prompt has placeholders
         try:
             prompt = prompt.format(**context_data)
         except KeyError:
             pass # ignore if prompt doesn't match context keys exactly

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
             "num_predict": 50 # Keep it short to fit on the screen
        }
    }

    try:
        logger.info(f"Prompting Ollama model {model}...")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        message = data.get("response", "").strip()
        # Clean up quotes if the model wraps the response
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
            
        ollama_cache = {"message": message}
        return ollama_cache

    except requests.RequestException as e:
         logger.error(f"Error communicating with Ollama: {e}")
         return ollama_cache
