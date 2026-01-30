
import ollama
import psutil
import subprocess
import atexit
import time
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
    # Start Ollama if not running
    def is_ollama_running():
        try:
            requests.get("http://localhost:11434")
            return True
        except Exception:
            return False

    def is_ollama_process_running():
        # Windows: use tasklist to check for ollama.exe
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq ollama.exe"], capture_output=True, text=True)
        return "ollama.exe" in result.stdout

    ollama_proc = None
    if not is_ollama_running() and not is_ollama_process_running():
        ollama_proc = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Started Ollama server.")
        # Wait for Ollama to be ready
        for _ in range(20):
            if is_ollama_running():
                break
            time.sleep(0.5)
        else:
            print("Ollama did not start in time.")
            if ollama_proc:
                ollama_proc.terminate()
            return
    elif is_ollama_process_running():
        print("Ollama process already running.")

    def cleanup():
        if ollama_proc:
            print("Terminating Ollama server and all child processes...")
            try:
                parent = psutil.Process(ollama_proc.pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except Exception:
                        pass
                gone, alive = psutil.wait_procs(children, timeout=5)
                for p in alive:
                    try:
                        p.kill()
                    except Exception:
                        pass
                parent.terminate()
                try:
                    parent.wait(timeout=5)
                except Exception:
                    print("Force killing Ollama parent process...")
                    parent.kill()
            except Exception as e:
                print(f"Could not fully kill Ollama process tree: {e}")
    atexit.register(cleanup)



    models = ollama.list()
    first_model_name = None
    if models and "models" in models and models["models"]:
        first_model = models["models"][0]
        if hasattr(first_model, "model"):
            first_model_name = first_model.model
            print(f"First model name: {first_model_name}")
    
    
    while True:
        user_input = input("Chat with Ollama: ")
        if user_input.lower() in {"exit", "quit"}:
            break

        response = ollama.generate(model=first_model_name, prompt=user_input)
        print(chat_from_response(response))

    cleanup()
    
if __name__ == "__main__":
    main()