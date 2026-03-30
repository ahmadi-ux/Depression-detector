import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import Dataset, concatenate_datasets
from sklearn.metrics import classification_report, confusion_matrix, hamming_loss
import csv

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

DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_PROMPT_TYPE = "emotion_multilabel"
DEFAULT_DAILY_BUDGET = 100_000_000
DEFAULT_RATE_LIMIT_SECONDS = 2.0
DEFAULT_MIN_OUTPUT_TOKENS = 4

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
    emoDep = emoDep.rename(columns={"text": "text"})

    csv_file1 = pd.read_csv(PROJECT_ROOT / "model_tuning" / "data_sets" / "training_data.csv")
    csv_file1 = csv_file1.rename(columns={"class": "label"})
    csv_file1 = csv_file1.rename(columns={"text": "text"})
    csv_file1 = csv_file1[~csv_file1["label"].isin([0, 4])]
    csv_file1 = csv_file1[csv_file1["judgment_confidence"] >= confidence_threshold]
    csv_file1["label"] = "00000000"

    common_columns = ["text", "label"]
    emoDep = emoDep[common_columns]
    csv_file1 = csv_file1[common_columns]

    csv_file1["label"] = csv_file1["label"].astype(str)
    emoDep["label"] = emoDep["label"].astype(str)

    dataset_csv1 = Dataset.from_pandas(csv_file1)
    dataset_depEmo = Dataset.from_pandas(emoDep)

    combined_dataset = concatenate_datasets([dataset_csv1, dataset_depEmo])
    split_dataset = combined_dataset.train_test_split(test_size=test_size, seed=seed)
    test_data = split_dataset["test"]
    return combined_dataset, test_data


def extract_prediction_bits(raw, expected_len=8):
    """Return parsed bits and whether a valid N-bit substring was found."""
    cleaned = str(raw).strip().replace(" ", "")
    for i in range(len(cleaned)):
        candidate = cleaned[i : i + expected_len]
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


def evaluate(
    model_name: str,
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
    combined_dataset, test_data = build_test_data(
        test_size=test_size, seed=seed, confidence_threshold=confidence_threshold
    )

    if max_samples is not None:
        test_data = test_data.select(range(min(max_samples, len(test_data))))

    print(f"Configured daily budget: {daily_budget} | Effective daily budget for {model_name}: {effective_daily_budget}")
    if effective_daily_request_budget is not None:
        print(
            f"Model {model_name} has {effective_daily_request_budget} requests-per-day limit (no preemptive cap applied)"
        )
        print(f"Requested {len(test_data)} samples - may require sleeping 24h if limit exceeded")

    all_gold = []
    all_preds = []
    raw_pairs = []
    results_arr = []
    no_bitstring_details = []
    api_errors = 0
    label_errors = 0
    no_bitstring_count = 0
    stopped_by_budget = False

    total_samples = len(test_data)
    progress_interval = 1
    start_time = time.perf_counter()
    print("Starting multilabel emotion evaluation")
    print(f"Model: {model_name}")
    print(f"Samples to evaluate: {total_samples}")

    for idx, each in enumerate(test_data):
        if idx > 0:
            time.sleep(rate_limit_seconds)

        try:
            response = analyze_with_groq(
                each["text"],
                model=model_name,
                prompt_type="emotion_multilabel",
                daily_budget_tokens=effective_daily_budget,
                calls_remaining=len(test_data) - idx,
                min_output_tokens=min_output_tokens,
            )
            analysis = response.get("analysis", {})
            # Extract the binary bits string from the analysis response
            if isinstance(analysis, dict) and "bits" in analysis:
                raw_response = analysis["bits"]
            else:
                raw_response = str(analysis).strip()
        except RateLimitError as rate_limit_err:
            print(f"\n[Sample {idx + 1}/{len(test_data)}] RateLimitError: {rate_limit_err}")
            print(f"\n{'='*80}")
            print(f"SLEEPING on rate limit at Sample {idx + 1}/{len(test_data)}")
            print(f"Sample text: {each['text'][:100]}...")
            print(f"{'='*80}\n")
            handle_rate_limit_sleep(model_name)
            api_errors += 1
            if idx % progress_interval == 0 or idx == total_samples - 1:
                elapsed = time.perf_counter() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (total_samples - idx) / rate if rate > 0 else 0
                print(
                    f"Progress: {idx + 1}/{total_samples} | "
                    f"elapsed={elapsed:.1f}s | rate={rate:.2f} samples/s | eta={eta:.1f}s | "
                    f"scored={len(all_gold)} | api_errors={api_errors} | "
                    f"label_errors={label_errors} | no_bitstring={no_bitstring_count}"
                )
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
                    print(f"\n{'='*80}")
                    print(f"SLEEPING on budget exhaustion at Sample {idx + 1}/{len(test_data)}")
                    print(f"Sample text: {each['text'][:100]}...")
                    print(
                        "Daily token budget reached. "
                        f"Sleeping for {sleep_seconds_on_cap} seconds before retrying this same sample..."
                    )
                    print(f"{'='*80}\n")
                    time.sleep(sleep_seconds_on_cap)
                    continue

                print(f"Stopped early due to daily token budget. Details: {err}")
                stopped_by_budget = True
                break

            print(f"Request failed on sample {idx + 1}: {err}")
            api_errors += 1
            if idx % progress_interval == 0 or idx == total_samples - 1:
                elapsed = time.perf_counter() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (total_samples - idx) / rate if rate > 0 else 0
                print(
                    f"Progress: {idx + 1}/{total_samples} | "
                    f"elapsed={elapsed:.1f}s | rate={rate:.2f} samples/s | eta={eta:.1f}s | "
                    f"scored={len(all_gold)} | api_errors={api_errors} | "
                    f"label_errors={label_errors} | no_bitstring={no_bitstring_count}"
                )
            continue

        try:
            gold_bits = label_to_target(each["label"])
        except ValueError as e:
            label_errors += 1
            results_arr.append(
                f"LABEL_ERROR : RawLabel: {each['label']} | Reason: {e} | Text: {each['text']} | "
            )
            if idx % progress_interval == 0 or idx == total_samples - 1:
                elapsed = time.perf_counter() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (total_samples - idx) / rate if rate > 0 else 0
                print(
                    f"Progress: {idx + 1}/{total_samples} | "
                    f"elapsed={elapsed:.1f}s | rate={rate:.2f} samples/s | eta={eta:.1f}s | "
                    f"scored={len(all_gold)} | api_errors={api_errors} | "
                    f"label_errors={label_errors} | no_bitstring={no_bitstring_count}"
                )
            continue

        pred_bits, has_valid_bitstring = extract_prediction_bits(raw_response)
        if not has_valid_bitstring:
            no_bitstring_count += 1
            no_bitstring_details.append(
                {
                    "idx": idx + 1,
                    "gold_bits": gold_bits,
                    "gold_decoded": decode_bits(gold_bits),
                    "raw_label": each["label"],
                    "text": each["text"],
                    "raw_response": raw_response,
                }
            )
            if idx % progress_interval == 0 or idx == total_samples - 1:
                elapsed = time.perf_counter() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (total_samples - idx) / rate if rate > 0 else 0
                print(
                    f"Progress: {idx + 1}/{total_samples} | "
                    f"elapsed={elapsed:.1f}s | rate={rate:.2f} samples/s | eta={eta:.1f}s | "
                    f"scored={len(all_gold)} | api_errors={api_errors} | "
                    f"label_errors={label_errors} | no_bitstring={no_bitstring_count}"
                )
            continue

        all_gold.append(bits_to_vec(gold_bits))
        all_preds.append(bits_to_vec(pred_bits))
        raw_pairs.append((gold_bits, pred_bits, each["text"], raw_response.strip()))

        if idx % progress_interval == 0 or idx == total_samples - 1:
            elapsed = time.perf_counter() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (total_samples - idx) / rate if rate > 0 else 0
            print(
                f"Progress: {idx + 1}/{total_samples} | "
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
    rows.append({"section": "summary", "metric": "Model", "value": model_name})
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
                rows.append(
                    {
                        "section": "classification_report",
                        "classification_label": label_name,
                        "precision": f"{stats.get('precision', 0.0):.4f}",
                        "recall": f"{stats.get('recall', 0.0):.4f}",
                        "f1_score": f"{stats.get('f1-score', 0.0):.4f}",
                        "support": support_val,
                    }
                )

        # Confusion matrices per emotion with structured columns
        for j, name in enumerate(EMOTION_LIST):
            cm = confusion_matrix(gold_arr[:, j], pred_arr[:, j], labels=[0, 1])
            rows.append(
                {
                    "section": "confusion_matrix",
                    "metric": name,
                    "tn": int(cm[0, 0]),
                    "fp": int(cm[0, 1]),
                    "fn": int(cm[1, 0]),
                    "tp": int(cm[1, 1]),
                }
            )
    else:
        rows.append({"section": "note", "metric": "No scorable predictions", "value": True})

    # No valid 8-bit string detail rows
    if no_bitstring_details:
        for entry in no_bitstring_details:
            rows.append(
                {
                    "section": "no_bitstring",
                    "idx": entry["idx"],
                    "gold_bits": entry["gold_bits"],
                    "gold_decoded": entry["gold_decoded"],
                    "raw_label": entry["raw_label"],
                    "text": entry["text"],
                    "raw_response": entry["raw_response"],
                }
            )
    else:
        rows.append({"section": "no_bitstring", "value": "None"})

    # Sample mistakes
    mistake_count = 0
    for gold_bits, pred_bits, text, raw_pred in raw_pairs:
        if gold_bits != pred_bits and mistake_count < 20:
            rows.append(
                {
                    "section": "mistake",
                    "gold": gold_bits,
                    "pred": pred_bits,
                    "raw_pred": raw_pred,
                    "text": text[:220],
                }
            )
            mistake_count += 1

    # Generate a datetime string for the filename and write CSV
    safe_model_name = make_safe_filename(model_name)
    dt_str = datetime.now().strftime(f"groq_{safe_model_name}_emotion_%m%d_%H%M%S")
    results_folder = PROJECT_ROOT / "model_tuning" / "testing_scripts" / "results"
    results_folder.mkdir(parents=True, exist_ok=True)
    results_filename = results_folder / f"{dt_str}.csv"

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
    print(f"Model: {model_name}")
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

    usage = get_daily_token_usage(effective_daily_budget)
    print(f"Token usage (estimated): used={usage['estimated_used']} remaining={usage['estimated_remaining']} budget={usage['budget']}")

    if stopped_by_budget:
        print("Run ended early due to token budget cap.")


def main():
    parser = argparse.ArgumentParser(description="Groq multilabel emotion classification runner")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
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
