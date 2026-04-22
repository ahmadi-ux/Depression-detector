import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from datasets import Dataset

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.Common.groq_handler import analyze_with_groq
from groq import RateLimitError


DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_PROMPT_TYPE = "ollama_compare"
DEFAULT_RATE_LIMIT_SECONDS = 2.0
DEFAULT_MIN_OUTPUT_TOKENS = 32
RATE_LIMIT_SLEEP_SECONDS = 86400  # 24 hours


def parse_test_size(value: str) -> int | float:
    value = str(value).strip()

    if value.endswith("%"):
        percent = float(value[:-1].strip())
        if percent <= 0 or percent >= 100:
            raise argparse.ArgumentTypeError("Percentage test size must be between 0 and 100.")
        return percent / 100.0

    numeric = float(value)
    if 0 < numeric < 1:
        return numeric
    if numeric >= 1 and numeric.is_integer():
        return int(numeric)

    raise argparse.ArgumentTypeError(
        "test-size must be an integer count, a fraction like 0.1, or a percentage like 10%."
    )


def make_safe_filename(value: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    safe = "".join("_" if c in invalid_chars else c for c in value)
    return safe.strip(" .")


def build_test_data(test_size: int | float, seed: int):
    # Load synthetic essays CSV
    csv_file = pd.read_csv(PROJECT_ROOT / "model_tuning" / "data_sets" / "synthetic_essays.csv")
    # Normalize column names to lowercase
    csv_file.columns = csv_file.columns.str.lower()
    
    common_columns = ["text", "label"]
    csv_file = csv_file[common_columns]

    dataset = Dataset.from_pandas(csv_file)
    
    # Convert integer counts to fractions, ensuring at least 1 sample is left for training
    if isinstance(test_size, int) and test_size >= 1:
        test_size = min(test_size, len(dataset) - 1) / len(dataset)
    
    split_dataset = dataset.train_test_split(test_size=test_size, seed=seed)
    test_data = split_dataset["test"]
    return dataset, test_data


def extract_groq_prediction(response: dict, prompt_type: str) -> str:
    analysis = response.get("analysis", {}) if isinstance(response, dict) else {}

    if prompt_type == "sentence":
        raw_pred = str(analysis.get("class", "unknown")).strip().lower()
    elif prompt_type == "simple":
        prediction = analysis.get("prediction", {})
        raw_pred = str(prediction.get("class", "unknown")).strip().lower()
    else:
        prediction = analysis.get("prediction", {})
        raw_pred = str(prediction.get("class", analysis.get("class", "unknown"))).strip().lower()

    raw_pred = raw_pred.strip(" \t\n\r\"'`.,:;!?[](){}")
    
    # Debug logging
    print(f"[DEBUG] Full response: {response}")
    print(f"[DEBUG] Analysis: {analysis}")
    print(f"[DEBUG] Raw prediction: '{raw_pred}'")

    if raw_pred in ["depressed", "depression"]:
        return "depressed"
    if raw_pred in ["not-depressed", "no-depression", "no depression", "not depressed", "none", "no"]:
        return "not-depressed"
    if "depress" in raw_pred and "no" not in raw_pred:
        return "depressed"
    if "not" in raw_pred and "depress" in raw_pred:
        return "not-depressed"
    
    print(f"[DEBUG] Could not parse prediction, returning 'unknown'")
    return "unknown"


def evaluate(
    model_name: str,
    prompt_type: str,
    rate_limit_seconds: float,
    min_output_tokens: int,
    test_size: int | float,
    seed: int,
    max_samples: int | None,
):
    combined_dataset, test_data = build_test_data(test_size=test_size, seed=seed)

    if max_samples is not None:
        test_data = test_data.select(range(min(max_samples, len(test_data))))

    print("Count with label 0 (depressed):", combined_dataset.filter(lambda x: x["label"] == 0).num_rows)
    print("Count with label 1 (not depressed):", combined_dataset.filter(lambda x: x["label"] == 1).num_rows)
    print(f"Running {len(test_data)} samples...")

    TP = 0
    TN = 0
    FP = 0
    FN = 0
    ERROR = 0
    total_ran = 0
    results_arr = []

    for idx, each in enumerate(test_data):
        if idx > 0:
            time.sleep(rate_limit_seconds)

        retry_unknown_once = prompt_type == "ollama_compare"
        unknown_retry_used = False

        while True:
            try:
                response = analyze_with_groq(
                    each["text"],
                    model=model_name,
                    prompt_type=prompt_type,
                    min_output_tokens=min_output_tokens,
                )
                predicted = extract_groq_prediction(response, prompt_type)

                if predicted == "unknown" and retry_unknown_once and not unknown_retry_used:
                    unknown_retry_used = True
                    print(f"Retrying sample {idx + 1} due to empty/ambiguous label response...")
                    continue

                if predicted == "unknown" and prompt_type == "ollama_compare":
                    try:
                        fallback_response = analyze_with_groq(
                            each["text"],
                            model=model_name,
                            prompt_type="sentence",
                            min_output_tokens=max(min_output_tokens, 64),
                        )
                        fallback_pred = extract_groq_prediction(fallback_response, "sentence")
                        if fallback_pred != "unknown":
                            predicted = fallback_pred
                            print(f"Recovered sample {idx + 1} with sentence fallback: {predicted}")
                    except Exception as fallback_error:
                        print(f"Sentence fallback failed on sample {idx + 1}: {fallback_error}")

                break
            except RateLimitError as rate_limit_err:
                print(f"\n[Sample {idx + 1}/{len(test_data)}] Rate limit (429) hit: {rate_limit_err}")
                print(f"\n{'='*80}")
                print(f"SLEEPING on rate limit at Sample {idx + 1}/{len(test_data)}")
                print(f"Sample text: {each['text'][:100]}...")
                print(f"Sleeping for {RATE_LIMIT_SLEEP_SECONDS} seconds (24 hours)...")
                print(f"{'='*80}\n")
                time.sleep(RATE_LIMIT_SLEEP_SECONDS)
                # After sleep, retry the same sample
                print(f"Retrying sample {idx + 1} after rate limit sleep...")
                continue
            except Exception as e:
                err = str(e)
                print(f"Request failed on sample {idx + 1}: {err}")
                predicted = "unknown"
                break

        if each["label"] == 0 and predicted == "depressed":
            TP += 1
            total_ran += 1
            print("Successfully predicted depressed for text: " + each["text"] + "\nResponse: " + predicted)

        elif each["label"] != 0 and predicted == "depressed":
            FP += 1
            total_ran += 1
            error_result_str = (
                "FP : "
                f"Label: {each['label']} | "
                f"Predicted: {predicted} | "
                f"Text: {each['text']} | "
            )
            results_arr.append(error_result_str)
            print(error_result_str)

        elif each["label"] != 0 and predicted == "not-depressed":
            TN += 1
            total_ran += 1
            print("Successfully predicted not-depressed for text: " + each["text"] + "\nResponse: " + predicted)

        elif each["label"] == 0 and predicted == "not-depressed":
            FN += 1
            total_ran += 1
            error_result_str = (
                "FN : "
                f"Label: {each['label']} | "
                f"Predicted: {predicted} | "
                f"Text: {each['text']} | "
            )
            results_arr.append(error_result_str)
            print(error_result_str)
        else:
            total_ran += 1
            print("Received unexpected response: " + predicted)
            ERROR += 1
            print("Label = " + str(each["label"]))
            print("Total ran: " + str(idx + 1) + "/" + str(len(test_data)))
            error_result_str = (
                "ERROR : "
                f"Label: {each['label']} | "
                f"Predicted: {predicted} | "
                f"Text: {each['text']} | "
            )
            results_arr.append(error_result_str)

    denom_precision = (TP + ERROR) + FP
    denom_recall = (TP + ERROR) + FN
    denom_accuracy = TP + TN + FP + FN + ERROR
    percision = (TP + ERROR) / denom_precision if denom_precision > 0 else 0.0
    recall = (TP + ERROR) / denom_recall if denom_recall > 0 else 0.0
    accuracy = (TP + ERROR + TN) / denom_accuracy if denom_accuracy > 0 else 0.0
    denom_f1 = percision + recall
    f1_score = 2 * (percision * recall) / denom_f1 if denom_f1 > 0 else 0.0

    results_arr.insert(
        0,
        "TP: " + str(TP)
        + " FP: " + str(FP)
        + " TN: " + str(TN)
        + " FN: " + str(FN)
        + " ERROR: " + str(ERROR)
        + " Precision: " + str(percision)
        + " Recall: " + str(recall)
        + " Accuracy: " + str(accuracy)
        + " F1 Score: " + str(f1_score)
        + " Model: " + model_name
        + " Prompt: " + prompt_type,
    )

    safe_model_name = make_safe_filename(model_name)
    dt_str = datetime.now().strftime(f"groq_{safe_model_name}_{prompt_type}_%m%d_%H%M%S")
    results_folder = PROJECT_ROOT / "model_tuning" / "testing_scripts" / "results"
    results_folder.mkdir(parents=True, exist_ok=True)
    results_path = results_folder / f"{dt_str}.txt"

    with open(results_path, "w", encoding="utf-8") as f:
        for line in results_arr:
            f.write(line + "\n")

    print(f"Saved results to: {results_path}")
    print(f"Precision: {percision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1_score:.4f}")
    print("")
    print("TP:" + str(TP))
    print("FP:" + str(FP))
    print("TN:" + str(TN))
    print("FN:" + str(FN))
    print("ERROR:" + str(ERROR))


def main():
    parser = argparse.ArgumentParser(description="Simple Groq zero-shot runner with synthetic essays dataset")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--prompt", type=str, default=DEFAULT_PROMPT_TYPE)
    parser.add_argument("--rate-limit-seconds", type=float, default=DEFAULT_RATE_LIMIT_SECONDS)
    parser.add_argument("--min-output-tokens", type=int, default=DEFAULT_MIN_OUTPUT_TOKENS)
    parser.add_argument("--test-size", type=parse_test_size, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-samples", type=int, default=None)
    args = parser.parse_args()

    evaluate(
        model_name=args.model,
        prompt_type=args.prompt,
        rate_limit_seconds=args.rate_limit_seconds,
        min_output_tokens=args.min_output_tokens,
        test_size=args.test_size,
        seed=args.seed,
        max_samples=args.max_samples,
    )


if __name__ == "__main__":
    main()
