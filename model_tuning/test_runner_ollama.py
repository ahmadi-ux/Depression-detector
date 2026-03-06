from datasets import load_dataset
import requests
from datetime import datetime
import json
import pandas as pd
from datasets import concatenate_datasets
from datasets import Dataset

OLLAMA_URL = "http://localhost:11434"
# Presets for Ollama call
REQUEST_TIMEOUT_SEC = 300
NUM_PREDICT = 2200    #Tokens max
TEMPERATURE = 0
MODEL_NAME = "gpt-oss:20b"
#llama3.1

#uniform mapping
# labels = label, 0 is depressed, all others are not-depressed
# text = text

# Load your CSV
emoDep = pd.read_json('Dataset/combined.json', lines=True)
emoDep = emoDep.rename(columns={"label_id": "label"}) #change column name to label
emoDep['label'] = 0 # Change all values in the 'label_id' column to 0 (depressed)
emoDep = emoDep.rename(columns={"text": "text"}) #no-op command can change

csv_file1 = pd.read_csv('Dataset/training_data.csv')
csv_file1 = csv_file1.rename(columns={"class": "label"}) #change column name to label
csv_file1 = csv_file1.rename(columns={"text": "text"}) #no-op command can change
#remove rows with label value 0 or 4. 0 = depressed, 4 = anxiety
#Also filter out low-confidence samples to improve data quality
csv_file1 = csv_file1[~csv_file1["label"].isin([0, 4])]
csv_file1 = csv_file1[csv_file1["judgment_confidence"] >= .80]

#combine datasets by shared columns (text and label)
common_columns = ["text", "label"]
emoDep = emoDep[common_columns]
csv_file1 = csv_file1[common_columns]

#combine datasets and create test split
dataset_csv1 = Dataset.from_pandas(csv_file1)
dataset_depEmo = Dataset.from_pandas(emoDep)
combined_dataset = concatenate_datasets([dataset_csv1, dataset_depEmo])
split_dataset = combined_dataset.train_test_split(test_size=0.01, seed=42) #remember seed so we can pull out training data.
test_data = split_dataset["test"]


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

for each in test_data:
    prompt = f"""Classify whether the following text indicates depression. 
    Respond with exactly 'depressed' or 'not-depressed'.\n\nTEXT:\n{each["text"]}\n\nLABEL:"""

    response = call_ollama_api(prompt, model=MODEL_NAME, timeout=REQUEST_TIMEOUT_SEC, ollama_url=OLLAMA_URL, num_predict=NUM_PREDICT, temperature=TEMPERATURE)
    if response is None:
        # skip this sample on failure
        continue
    response = ollama_response_to_string(response)

    # dataset uses 'label' column (0 indicates depressed)
    if each["label"] == 0 and response.strip() == "depressed":
        TP += 1
        total_ran += 1
        print("Successfully predicted depressed for text: " + each["text"] + "\nResponse: " + response)
    
    elif each["label"] != 0 and response.strip() == "depressed":
        FP += 1
        total_ran += 1
        print("Incorrectly predicted depressed for text: " + each["text"] + "\nResponse: " + response)
    
    elif each["label"] != 0 and response.strip() == "not-depressed":
        TN += 1
        total_ran += 1
        print("Successfully predicted not-depressed for text: " + each["text"] + "\nResponse: " + response)
    
    elif each["label"] == 0 and response.strip() == "not-depressed":
        FN += 1
        total_ran += 1
        print("Incorrectly predicted not-depressed for text: " + each["text"] + "\nResponse: " + response)
    
    else:
        print("Received unexpected response: " + response.strip())
        ERROR += 1
    print("Label = " + str(each["label"]))
    print ("Total ran: " + str(total_ran) + "/" + str(len(test_data)))

    result_str = (
        f"Text: {each['text']} | "
        f"Label: {each['label']} | "
        f"Predicted: {response.strip()} | "
    )
    results_arr.append(result_str)


percision = TP / (TP + FP)
recall = TP / (TP + FN)
f1_score = 2 * (percision * recall) / (percision + recall)



results_arr.insert(0, "TP: " + str(TP) + " FP: " + str(FP) + " TN: " + str(TN) + " FN: " + str(FN) + " ERROR: " + str(ERROR)
                   + " Precision: " + str(percision) + " Recall: " + str(recall) + " F1 Score: " + str(f1_score))

# Generate a datetime string for the filename
dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
results_filename = f"results_{dt_str}.txt"
with open(results_filename, "w", encoding="utf-8") as f:
    for line in results_arr:
        f.write(line + "\n")


print(f"Precision: {percision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1_score:.4f}")
print("")
print("TP:" + str(TP))
print("FP:" + str(FP))
print("TN:" + str(TN))
print("FN:" + str(FN))
print("ERROR:" + str(ERROR))
