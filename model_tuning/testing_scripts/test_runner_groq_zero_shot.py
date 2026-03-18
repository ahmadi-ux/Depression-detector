import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from datasets import Dataset
from datasets import concatenate_datasets

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.Common.groq_handler import (
    analyze_with_groq,
    get_daily_token_usage,
    get_effective_daily_budget,
    get_effective_daily_request_budget,
    handle_rate_limit_sleep,
)
from groq import RateLimitError


DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_PROMPT_TYPE = "ollama_compare"
DEFAULT_DAILY_BUDGET = 200_000
DEFAULT_RATE_LIMIT_SECONDS = 2.0
DEFAULT_MIN_OUTPUT_TOKENS = 16


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


def build_test_data(test_size: int | float, seed: int, confidence_threshold: float):
    emoDep = pd.read_json(PROJECT_ROOT / "model_tuning" / "data_sets" / "combined.json", lines=True)
    emoDep = emoDep.rename(columns={"label_id": "label"})
    emoDep["label"] = 0

    csv_file1 = pd.read_csv(PROJECT_ROOT / "model_tuning" / "data_sets" / "training_data.csv")
    csv_file1 = csv_file1.rename(columns={"class": "label"})
    csv_file1 = csv_file1[~csv_file1["label"].isin([0, 4])]
    csv_file1 = csv_file1[csv_file1["judgment_confidence"] >= confidence_threshold]

    rmhd_1 = pd.read_csv(PROJECT_ROOT / "model_tuning" / "data_sets" / "labelled_file1.csv")
    rmhd_2 = pd.read_csv(PROJECT_ROOT / "model_tuning" / "data_sets" / "labelled_file2.csv")
    rmhd_3 = pd.read_csv(PROJECT_ROOT / "model_tuning" / "data_sets" / "labelled_file3.csv")
    rmhd_4 = pd.read_csv(PROJECT_ROOT / "model_tuning" / "data_sets" / "labelled_file4.csv")
    rmhd_1["label"] = 0
    rmhd_2["label"] = 0
    rmhd_3["label"] = 0
    rmhd_4["label"] = 0

    common_columns = ["text", "label"]
    emoDep = emoDep[common_columns]
    csv_file1 = csv_file1[common_columns]
    rmhd_1 = rmhd_1[common_columns]
    rmhd_2 = rmhd_2[common_columns]
    rmhd_3 = rmhd_3[common_columns]
    rmhd_4 = rmhd_4[common_columns]

    dataset_csv1 = Dataset.from_pandas(csv_file1)
    dataset_depEmo = Dataset.from_pandas(emoDep)
    dataset_rmhd_1 = Dataset.from_pandas(rmhd_1)
    dataset_rmhd_2 = Dataset.from_pandas(rmhd_2)
    dataset_rmhd_3 = Dataset.from_pandas(rmhd_3)
    dataset_rmhd_4 = Dataset.from_pandas(rmhd_4)

    combined_dataset = concatenate_datasets(
        [dataset_csv1, dataset_depEmo, dataset_rmhd_1, dataset_rmhd_2, dataset_rmhd_3, dataset_rmhd_4]
    )
    split_dataset = combined_dataset.train_test_split(test_size=test_size, seed=seed)
    test_data = split_dataset["test"]
    return combined_dataset, test_data


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

    if raw_pred in ["depressed", "depression"]:
        return "depressed"
    if raw_pred in ["not-depressed", "no-depression", "no depression", "not depressed", "none", "no"]:
        return "not-depressed"
    if "depress" in raw_pred and "no" not in raw_pred:
        return "depressed"
    if "not" in raw_pred and "depress" in raw_pred:
        return "not-depressed"
    return "unknown"


def evaluate(
    model_name: str,
    prompt_type: str,
    daily_budget: int,
    rate_limit_seconds: float,
    min_output_tokens: int,
    test_size: int | float,
    seed: int,
    confidence_threshold: float,
    max_samples: int | None,
    wait_on_budget_cap: bool,
    sleep_seconds_on_cap: int,
):
    effective_daily_budget = get_effective_daily_budget(model_name, daily_budget)
    effective_daily_request_budget = get_effective_daily_request_budget(model_name)
    combined_dataset, test_data = build_test_data(test_size=test_size, seed=seed, confidence_threshold=confidence_threshold)

    if max_samples is not None:
        test_data = test_data.select(range(min(max_samples, len(test_data))))

    print("Count with label 0:", combined_dataset.filter(lambda x: x["label"] == 0).num_rows)
    print(f"Configured daily budget: {daily_budget} | Effective daily budget for {model_name}: {effective_daily_budget}")
    if effective_daily_request_budget is not None:
        print(f"Model {model_name} has {effective_daily_request_budget} requests-per-day limit (no preemptive cap applied)")
        print(f"Requested {len(test_data)} samples - may require sleeping 24h if limit exceeded")

    TP = 0
    TN = 0
    FP = 0
    FN = 0
    ERROR = 0
    total_ran = 0
    results_arr = []
    stopped_by_budget = False

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
                    daily_budget_tokens=effective_daily_budget,
                    calls_remaining=len(test_data) - idx,
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
                            daily_budget_tokens=effective_daily_budget,
                            calls_remaining=len(test_data) - idx,
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
                print(f"\n[Sample {idx + 1}/{len(test_data)}] RateLimitError: {rate_limit_err}")
                handle_rate_limit_sleep(model_name)
                # After sleep, retry the same sample
                print(f"Retrying sample {idx + 1} after rate limit sleep...")
                continue
            except Exception as e:
                err = str(e)
                is_budget_error = (
                    "Daily token budget exhausted" in err
                    or "Remaining token budget is insufficient" in err
                    or "Insufficient budget for completion after prompt allocation" in err
                )
                if is_budget_error:
                    if wait_on_budget_cap:
                        print(
                            "Daily token budget reached. "
                            f"Sleeping for {sleep_seconds_on_cap} seconds before retrying this same sample..."
                        )
                        time.sleep(sleep_seconds_on_cap)
                        continue

                    print(f"Stopped early due to daily token budget. Details: {err}")
                    stopped_by_budget = True
                    break

                if retry_unknown_once and not unknown_retry_used:
                    unknown_retry_used = True
                    print(f"Retrying sample {idx + 1} after request error: {err}")
                    continue

                print(f"Request failed on sample {idx + 1}: {err}")
                predicted = "unknown"
                break

        if stopped_by_budget:
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

    usage = get_daily_token_usage(effective_daily_budget)
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
        + " Prompt: " + prompt_type
        + " DailyBudget: " + str(daily_budget)
        + " EffectiveDailyBudget: " + str(effective_daily_budget)
        + " EstimatedUsed: " + str(usage["estimated_used"])
        + " EstimatedRemaining: " + str(usage["estimated_remaining"]),
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
    print(f"Token usage (estimated): used={usage['estimated_used']} remaining={usage['estimated_remaining']} budget={usage['budget']}")

    if stopped_by_budget:
        print("Run ended early due to token budget cap.")


def main():
    parser = argparse.ArgumentParser(description="Groq zero-shot runner with Ollama-style output formatting")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--prompt", type=str, default=DEFAULT_PROMPT_TYPE)
    parser.add_argument("--daily-budget", type=int, default=DEFAULT_DAILY_BUDGET)
    parser.add_argument("--rate-limit-seconds", type=float, default=DEFAULT_RATE_LIMIT_SECONDS)
    parser.add_argument("--min-output-tokens", type=int, default=DEFAULT_MIN_OUTPUT_TOKENS)
    parser.add_argument("--test-size", type=parse_test_size, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--confidence-threshold", type=float, default=0.80)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--wait-on-budget-cap", action="store_true")
    parser.add_argument("--sleep-seconds-on-cap", type=int, default=86400)
    args = parser.parse_args()

    evaluate(
        model_name=args.model,
        prompt_type=args.prompt,
        daily_budget=args.daily_budget,
        rate_limit_seconds=args.rate_limit_seconds,
        min_output_tokens=args.min_output_tokens,
        test_size=args.test_size,
        seed=args.seed,
        confidence_threshold=args.confidence_threshold,
        max_samples=args.max_samples,
        wait_on_budget_cap=args.wait_on_budget_cap,
        sleep_seconds_on_cap=args.sleep_seconds_on_cap,
    )


if __name__ == "__main__":
    main()
