
import ollama
import os
import requests
import sys




def chat_from_response(response: dict) -> str:
    """
    Args:
        response (dict): The dictionary returned by ollama.generate
    Returns:
        str: The generated response string
    """
    return response.get("response", "")



def main():

    # Connect to Ollama running in Docker
    ollama_host = os.environ.get("OLLAMA_HOST", "ollama")
    ollama_port = os.environ.get("OLLAMA_PORT", "11434")
    ollama_url = f"http://{ollama_host}:{ollama_port}"
    try:
        requests.get(ollama_url)
    except Exception:
        print(f"Cannot connect to Ollama at {ollama_url}")
        sys.exit(1)


    models = ollama.list()
    first_model_name = None
    if models and "models" in models and models["models"]:
        first_model = models["models"][0]
        if hasattr(first_model, "model"):
            first_model_name = first_model.model
            print(f"First model name: {first_model_name}")

    #terminal for test environment
    if not sys.stdin.isatty():
        print("No interactive terminal detected. Exiting.")
        return

    while True:
        user_input = input("Chat with Ollama: ")
        if user_input.lower() in {"exit", "quit"}:
            break
        response = ollama.generate(model=first_model_name, prompt=user_input)
        print(chat_from_response(response))
    
if __name__ == "__main__":
    main()