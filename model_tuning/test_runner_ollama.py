from datasets import load_dataset
import requests
from datetime import datetime
import json
import ollama

OLLAMA_URL = "http://localhost:11434"
# Presets for Ollama call
REQUEST_TIMEOUT_SEC = 300
NUM_PREDICT = 2200
TEMPERATURE = 0
MODEL_NAME = "gpt-oss:20b"
#llama3.1

dataset = load_dataset(
    "csv",
    data_files={"test": "Dataset/test1.csv"},
    delimiter=",", # no-op command can change or remove
    keep_default_na=False,
    token= None,
)

dataset_rand = dataset["test"].shuffle(seed=42)

def ollama_response_to_string(input_response):
    output = ""
    for line in input_response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            # Surface model/server-side errors instead of silently returning empty output.
            if data.get("error"):
                raise ValueError(str(data.get("error")))
            output += data.get("response", "")
    return output

def call_ollama_api(prompt, model, timeout, ollama_url, num_predict, temperature):
    payload = {
                "model": model,
                "prompt": prompt,
                # Cap generated tokens to avoid runaway output and long runtimes.
                "think": False,
                "options": {
                    "num_predict": num_predict,
                    # Keep outputs deterministic for consistency across runs.
                    "temperature": temperature
                }
            }
    try:
        # request in streaming mode since Ollama returns newline-delimited JSON
        response = requests.post(
            ollama_url + "/api/generate",
            json=payload,
            timeout=timeout,
            stream=True,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        return None

TP = 0
TN = 0
FP = 0
FN = 0
total_ran = 0
ERROR = 0
results_arr= []

for each in dataset_rand:
    prompt = f"""Classify whether the following text indicates depression. 
    Respond with exactly 'depressed' or 'not-depressed'.\n\nTEXT:\n{each["text"]}\n\nLABEL:"""

    response = call_ollama_api(prompt, model=MODEL_NAME, timeout=REQUEST_TIMEOUT_SEC, ollama_url=OLLAMA_URL, num_predict=NUM_PREDICT, temperature=TEMPERATURE)
    if response is None:
        # skip this sample on failure
        continue
    response = ollama_response_to_string(response)

    # dataset uses 'class' column for labels (0 indicates depressed)
    if each["class"] == 0 and response.strip() == "depressed":
        TP += 1
        total_ran += 1
        print("Successfully predicted depressed for text: " + each["text"] + "\nResponse: " + response)
    
    elif each["class"] != 0 and response.strip() == "depressed":
        FP += 1
        total_ran += 1
        print("Incorrectly predicted depressed for text: " + each["text"] + "\nResponse: " + response)
    
    elif each["class"] != 0 and response.strip() == "not-depressed":
        TN += 1
        total_ran += 1
        print("Successfully predicted not-depressed for text: " + each["text"] + "\nResponse: " + response)
    
    elif each["class"] == 0 and response.strip() == "not-depressed":
        FN += 1
        total_ran += 1
        print("Incorrectly predicted not-depressed for text: " + each["text"] + "\nResponse: " + response)
    
    else:
        print("Received unexpected response: " + response.strip())
        ERROR += 1
    print("Label = " + str(each["class"]))
    print ("Total ran: " + str(total_ran) + "/" + str(len(dataset_rand)))

    result_str = (
        f"Text: {each['text']} | "
        f"Label: {each['class']} | "
        f"Predicted: {response.strip()} | "
    )
    results_arr.append(result_str)



results_arr.insert(0, "TP: " + str(TP) + " FP: " + str(FP) + " TN: " + str(TN) + " FN: " + str(FN) + " ERROR: " + str(ERROR))

# Generate a datetime string for the filename
dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
results_filename = f"results_{dt_str}.txt"
with open(results_filename, "w", encoding="utf-8") as f:
    for line in results_arr:
        f.write(line + "\n")


print("TP:" + str(TP))
print("FP:" + str(FP))
print("TN:" + str(TN))
print("FN:" + str(FN))
print("ERROR:" + str(ERROR))
