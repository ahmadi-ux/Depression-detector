import requests
from datetime import datetime
import json
import csv
import os
import pandas as pd
from datasets import concatenate_datasets
from datasets import Dataset
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, hamming_loss
from time import perf_counter

OLLAMA_URL = "http://localhost:11434"
# Presets for Ollama call
REQUEST_TIMEOUT_SEC = 300
NUM_PREDICT = 2200
TEMPERATURE = 0
MODEL_NAME = "llama3.1"
#llama3.1
#gpt-oss:20b
#emollama:v1

EMOTION_LIST = [
    "anger",
    "brain dysfunction (forget)",
    "emptiness",
    "hopelessness",
    "loneliness",
    "sadness",
    "suicide intent",
    "worthlessness",
]

# Uniform mapping
# labels = 8-bit string where each bit maps to EMOTION_LIST
# text = text

# Load your CSV
emoDep = pd.read_json('data_sets/combined.json', lines=True)
emoDep = emoDep.rename(columns={"label_id": "label"}) #change column name to label
emoDep = emoDep.rename(columns={"text": "text"}) #no-op command can change

csv_file1 = pd.read_csv('data_sets/training_data.csv')
csv_file1 = csv_file1.rename(columns={"class": "label"}) #change column name to label
csv_file1 = csv_file1.rename(columns={"text": "text"}) #no-op command can change
#remove rows with label value 0 or 4. 0 = depressed, 4 = anxiety
#Also filter out low-confidence samples to improve data quality
csv_file1 = csv_file1[~csv_file1["label"].isin([0, 4])]
csv_file1 = csv_file1[csv_file1["judgment_confidence"] >= .80]
csv_file1["label"] = "00000000"

#combine datasets by shared columns (text and label)
common_columns = ["text", "label"]
emoDep = emoDep[common_columns]
csv_file1 = csv_file1[common_columns]

# Ensure label columns are strings to avoid features alignment issues
csv_file1["label"] = csv_file1["label"].astype(str)
emoDep["label"] = emoDep["label"].astype(str)

#combine datasets and create test split
dataset_csv1 = Dataset.from_pandas(csv_file1)
dataset_depEmo = Dataset.from_pandas(emoDep)

# Match the training split source used in tune_driver_emoDepres.py
combined_dataset = concatenate_datasets([dataset_csv1, dataset_depEmo])
split_dataset = combined_dataset.train_test_split(test_size=0.1, seed=42) #remember seed so we can pull out training data.
test_data = split_dataset["test"]

# Allow limiting the number of test samples via env var SAMPLE_LIMIT for quick runs
sample_limit = int(os.getenv("SAMPLE_LIMIT", "0"))
if sample_limit > 0:
    try:
        test_len = len(test_data)
        select_n = min(sample_limit, test_len)
        test_data = test_data.select(range(select_n))
    except Exception:
        # Fallback to slicing if select isn't available
        test_data = test_data[:sample_limit]

#Essay data set option! 14 samples total, 8 depressed (label 0) and 6 not-depressed.
"""essay_data = essay_data.rename(columns={"Label": "label"})
essay_data = essay_data.rename(columns={"Text": "text"})
essay_data = essay_data[common_columns]
dataset_essay = Dataset.from_pandas(essay_data)
combined_dataset = concatenate_datasets([dataset_essay])
test_data = combined_dataset"""


def extract_prediction_bits(raw, expected_len=8):
    """Return parsed bits and whether a valid N-bit substring was found."""
    cleaned = str(raw).strip().replace(" ", "")
    for i in range(len(cleaned)):
        candidate = cleaned[i:i + expected_len]
        if len(candidate) == expected_len and all(c in "01" for c in candidate):
            return candidate, True
    return None, False


def label_to_target(label, expected_len=8):
    """Normalize dataset labels into fixed-length binary strings."""
    value = str(label).strip()
    if all(c in "01" for c in value) and len(value) <= expected_len:
        return value.zfill(expected_len)
    if value.isdigit():
        as_int = int(value)
        if 0 <= as_int <= (2 ** expected_len) - 1:
            return format(as_int, f"0{expected_len}b")
    raise ValueError(f"Invalid multilabel target: {label}")


def bits_to_vec(bit_str):
    return [int(c) for c in bit_str]


def decode_bits(bit_str):
    active = [EMOTION_LIST[i] for i, b in enumerate(bit_str) if b == "1"]
    return ", ".join(active) if active else "none"


def build_prompt(text):
    return (
        "Classify whether the following text indicates depression. "
        "If depression is detected, indicate which of these emotions are present: "
        "emotion_list = ['anger', 'brain dysfunction (forget)', 'emptiness', 'hopelessness', "
        "'loneliness', 'sadness', 'suicide intent', 'worthlessness']"
        "Respond with ONLY a binary string that cooralates to which emotions are present.\n"
        "OUTPUT EXAMPLES:\n['emptiness', 'hopelessness'] -> 00110000\n['anger'] -> 10000000\n"
        "['anger', 'brain dysfunction (forget)', 'emptiness', 'hopelessness', 'loneliness', "
        "'sadness', 'suicide intent', 'worthlessness'] -> 11111111\n\n"
        f"TEXT:\n{text}\n\nLABEL:"
    )


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

all_gold = []
all_preds = []
raw_pairs = []
results_arr = []
no_bitstring_details = []
api_errors = 0
label_errors = 0
no_bitstring_count = 0

total_samples = len(test_data)
progress_interval = 1
start_time = perf_counter()
print("Starting multilabel evaluation")
print(f"Model: {MODEL_NAME}")
print(f"Samples to evaluate: {total_samples}")

for idx, each in enumerate(test_data, start=1):
    prompt = build_prompt(each["text"])

    response = call_ollama_api(prompt, model=MODEL_NAME, timeout=REQUEST_TIMEOUT_SEC, ollama_url=OLLAMA_URL, num_predict=NUM_PREDICT, temperature=TEMPERATURE)
    if response is None:
        api_errors += 1
        if idx % progress_interval == 0 or idx == total_samples:
            elapsed = perf_counter() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (total_samples - idx) / rate if rate > 0 else 0
            print(
                f"Progress: {idx}/{total_samples} | "
                f"elapsed={elapsed:.1f}s | rate={rate:.2f} samples/s | eta={eta:.1f}s | "
                f"scored={len(all_gold)} | api_errors={api_errors} | "
                f"label_errors={label_errors} | no_bitstring={no_bitstring_count}"
            )
        continue
    raw_response = ollama_response_to_string(response)

    try:
        gold_bits = label_to_target(each["label"])
    except ValueError as e:
        label_errors += 1
        results_arr.append(
            "LABEL_ERROR : "
            f"RawLabel: {each['label']} | "
            f"Reason: {e} | "
            f"Text: {each['text']} | "
        )
        continue

    pred_bits, has_valid_bitstring = extract_prediction_bits(raw_response)
    if not has_valid_bitstring:
        no_bitstring_count += 1
        no_bitstring_details.append(
            {
                "idx": idx,
                "gold_bits": gold_bits,
                "gold_decoded": decode_bits(gold_bits),
                "raw_label": each["label"],
                "text": each["text"],
                "raw_response": raw_response,
            }
        )
        if idx % progress_interval == 0 or idx == total_samples:
            elapsed = perf_counter() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (total_samples - idx) / rate if rate > 0 else 0
            print(
                f"Progress: {idx}/{total_samples} | "
                f"elapsed={elapsed:.1f}s | rate={rate:.2f} samples/s | eta={eta:.1f}s | "
                f"scored={len(all_gold)} | api_errors={api_errors} | "
                f"label_errors={label_errors} | no_bitstring={no_bitstring_count}"
            )
        continue

    all_gold.append(bits_to_vec(gold_bits))
    all_preds.append(bits_to_vec(pred_bits))
    raw_pairs.append((gold_bits, pred_bits, each["text"], raw_response.strip()))

    if idx % progress_interval == 0 or idx == total_samples:
        elapsed = perf_counter() - start_time
        rate = idx / elapsed if elapsed > 0 else 0
        eta = (total_samples - idx) / rate if rate > 0 else 0
        print(
            f"Progress: {idx}/{total_samples} | "
            f"elapsed={elapsed:.1f}s | rate={rate:.2f} samples/s | eta={eta:.1f}s | "
            f"scored={len(all_gold)} | api_errors={api_errors} | "
            f"label_errors={label_errors} | no_bitstring={no_bitstring_count}"
        )

metrics_available = len(all_gold) > 0

if metrics_available:
    gold_arr = np.array(all_gold)
    pred_arr = np.array(all_preds)

    exact_match_accuracy = np.all(gold_arr == pred_arr, axis=1).mean()
    h_loss = hamming_loss(gold_arr, pred_arr)
    per_emotion_accuracy = (gold_arr == pred_arr).mean(axis=0)

    # Secondary metric: binary depression detection from bit-strings.
    # 00000000 => not depressed, anything else => depressed.
    gold_dep = np.any(gold_arr == 1, axis=1)
    pred_dep = np.any(pred_arr == 1, axis=1)

    tp_dep = int(np.sum(gold_dep & pred_dep))
    tn_dep = int(np.sum((~gold_dep) & (~pred_dep)))
    fp_dep = int(np.sum((~gold_dep) & pred_dep))
    fn_dep = int(np.sum(gold_dep & (~pred_dep)))

    dep_total = len(gold_dep)
    dep_accuracy = (tp_dep + tn_dep) / dep_total if dep_total else 0.0
    dep_precision = tp_dep / (tp_dep + fp_dep) if (tp_dep + fp_dep) else 0.0
    dep_recall = tp_dep / (tp_dep + fn_dep) if (tp_dep + fn_dep) else 0.0
    dep_f1 = (
        2 * dep_precision * dep_recall / (dep_precision + dep_recall)
        if (dep_precision + dep_recall)
        else 0.0
    )

    classification_dict = classification_report(
        gold_arr,
        pred_arr,
        target_names=EMOTION_LIST,
        zero_division=0,
        output_dict=True,
    )

rows = []

# Summary rows
rows.append({"section": "summary", "metric": "Model", "value": MODEL_NAME})
rows.append({"section": "summary", "metric": "Evaluated samples", "value": f"{len(all_gold)} / {len(test_data)}"})
rows.append({"section": "summary", "metric": "API errors", "value": api_errors})
rows.append({"section": "summary", "metric": "Label parse errors", "value": label_errors})
rows.append({"section": "summary", "metric": "No valid 8-bit string", "value": no_bitstring_count})

if metrics_available:
    rows.append({"section": "metrics", "metric": "Exact Match Accuracy", "value": f"{exact_match_accuracy:.4f}"})
    rows.append({"section": "metrics", "metric": "Hamming Loss", "value": f"{h_loss:.4f}"})

    # Binary depression metrics
    rows.append({"section": "binary_depression", "metric": "TP", "value": tp_dep})
    rows.append({"section": "binary_depression", "metric": "FP", "value": fp_dep})
    rows.append({"section": "binary_depression", "metric": "TN", "value": tn_dep})
    rows.append({"section": "binary_depression", "metric": "FN", "value": fn_dep})
    rows.append({"section": "binary_depression", "metric": "Accuracy", "value": f"{dep_accuracy:.4f}"})
    rows.append({"section": "binary_depression", "metric": "Precision", "value": f"{dep_precision:.4f}"})
    rows.append({"section": "binary_depression", "metric": "Recall", "value": f"{dep_recall:.4f}"})
    rows.append({"section": "binary_depression", "metric": "F1", "value": f"{dep_f1:.4f}"})

    # Per-emotion accuracy
    for name, acc in zip(EMOTION_LIST, per_emotion_accuracy):
        rows.append({"section": "per_emotion_accuracy", "metric": name, "value": f"{acc:.4f}"})

    # Classification report rows with split metric columns
    for label_name, stats in classification_dict.items():
        if isinstance(stats, dict):
            support_val = stats.get("support", "")
            if isinstance(support_val, float) and support_val.is_integer():
                support_val = int(support_val)
            rows.append({
                "section": "classification_report",
                "classification_label": label_name,
                "precision": f"{stats.get('precision', 0.0):.4f}",
                "recall": f"{stats.get('recall', 0.0):.4f}",
                "f1_score": f"{stats.get('f1-score', 0.0):.4f}",
                "support": support_val,
            })

    # Confusion matrices per emotion with structured columns
    for j, name in enumerate(EMOTION_LIST):
        cm = confusion_matrix(gold_arr[:, j], pred_arr[:, j], labels=[0, 1])
        rows.append({
            "section": "confusion_matrix",
            "metric": name,
            "tn": int(cm[0, 0]),
            "fp": int(cm[0, 1]),
            "fn": int(cm[1, 0]),
            "tp": int(cm[1, 1]),
        })
else:
    rows.append({"section": "note", "metric": "No scorable predictions", "value": True})

# No valid 8-bit string detail rows
if no_bitstring_details:
    for entry in no_bitstring_details:
        rows.append({
            "section": "no_bitstring",
            "idx": entry["idx"],
            "gold_bits": entry["gold_bits"],
            "gold_decoded": entry["gold_decoded"],
            "raw_label": entry["raw_label"],
            "text": entry["text"],
            "raw_response": entry["raw_response"],
        })
else:
    rows.append({"section": "no_bitstring", "value": "None"})

# Sample mistakes
mistake_count = 0
for gold_bits, pred_bits, text, raw_pred in raw_pairs:
    if gold_bits != pred_bits and mistake_count < 20:
        rows.append({
            "section": "mistake",
            "gold": gold_bits,
            "pred": pred_bits,
            "raw_pred": raw_pred,
            "text": text[:220],
        })
        mistake_count += 1

# Generate a datetime string for the filename and write CSV
dt_str = datetime.now().strftime(f"model_{MODEL_NAME.replace(':', '_')}_%m%d_%H%M%S")
results_filename = f"results_{dt_str}.csv"
fieldnames = [
    "section",
    "metric",
    "value",
    "idx",
    "gold_bits",
    "gold_decoded",
    "raw_label",
    "text",
    "raw_response",
    "tn",
    "fp",
    "fn",
    "tp",
    "gold",
    "pred",
    "raw_pred",
    "classification_label",
    "precision",
    "recall",
    "f1_score",
    "support",
]
with open(results_filename, "w", encoding="utf-8", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})

print("Evaluation complete")
print(f"Model: {MODEL_NAME}")
print(f"Evaluated samples: {len(all_gold)} / {len(test_data)}")
print(f"API errors: {api_errors}")
print(f"Label parse errors: {label_errors}")
print(f"No valid 8-bit string in response: {no_bitstring_count}")

if metrics_available:
    print(f"Exact Match Accuracy: {exact_match_accuracy:.4f}")
    print(f"Hamming Loss: {h_loss:.4f}")
    print("Binary depression metrics (00000000 => not depressed):")
    print(f"  TP: {tp_dep}  FP: {fp_dep}  TN: {tn_dep}  FN: {fn_dep}")
    print(f"  Accuracy: {dep_accuracy:.4f}")
    print(f"  Precision: {dep_precision:.4f}")
    print(f"  Recall: {dep_recall:.4f}")
    print(f"  F1: {dep_f1:.4f}")
    print("Per-emotion confusion matrices:")
    for j, name in enumerate(EMOTION_LIST):
        cm = confusion_matrix(gold_arr[:, j], pred_arr[:, j], labels=[0, 1])
        print(f"  {name}: [[{cm[0, 0]}, {cm[0, 1]}], [{cm[1, 0]}, {cm[1, 1]}]]")
else:
    print("No scorable predictions available; metrics skipped.")

print(f"Saved detailed CSV report to: {results_filename}")
