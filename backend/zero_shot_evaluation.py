"""
Zero-shot evaluation script for depression detection models.
Tests multiple models and prompt types against a labeled dataset.

Usage:
    python -m backend.zero_shot_evaluation
    python -m backend.zero_shot_evaluation --model openai/gpt-oss-120b --prompt chain_of_thought
"""

import argparse
import csv
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.Common.groq_handler import analyze_with_groq
from backend.Common.sentence_analyzer import REQUESTS_PER_MINUTE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rate limiting
MIN_REQUEST_INTERVAL = 30.0 / REQUESTS_PER_MINUTE

# Available models on Groq
MODELS = [
    "llama-3.1-8b-instant",
    "compound-beta",
    "llama-3.3-70b-versatile",
    "moonshotai/kimi-k2-instruct-0905",
    "openai/gpt-oss-120b",
]

# Available prompt types
PROMPT_TYPES = [
    "simple",
    "structured", 
    "chain_of_thought",
    "few_shot",
    "feature_extraction",
]

# Labeled test dataset - balanced depression vs no-depression examples
# Sources: Synthetic examples based on clinical depression indicators
TEST_CASES = [
    # === DEPRESSION EXAMPLES ===
    {
        "text": "I feel completely worthless. Nothing I do matters and I can't see the point in trying anymore.",
        "label": "depression",
        "category": "worthlessness/hopelessness"
    },
    {
        "text": "I've been staying in bed all day. I don't want to see anyone or do anything. Everything feels empty.",
        "label": "depression",
        "category": "withdrawal/anhedonia"
    },
    {
        "text": "I'm such a burden to everyone around me. They'd all be better off without me dragging them down.",
        "label": "depression",
        "category": "negative self-perception"
    },
    {
        "text": "I used to love painting but now I can't even pick up a brush. Nothing brings me joy anymore.",
        "label": "depression",
        "category": "anhedonia"
    },
    {
        "text": "I can't sleep at night. I just lie there thinking about all my failures. I'm so tired but I can't rest.",
        "label": "depression",
        "category": "sleep disturbance/rumination"
    },
    {
        "text": "What's the point? Things will never get better. I've tried everything and nothing works.",
        "label": "depression",
        "category": "hopelessness"
    },
    {
        "text": "I feel so alone even when I'm surrounded by people. Nobody really understands what I'm going through.",
        "label": "depression",
        "category": "isolation"
    },
    {
        "text": "I hate myself. I look in the mirror and I see nothing but a failure staring back at me.",
        "label": "depression",
        "category": "self-loathing"
    },
    {
        "text": "Everything requires so much effort. Even getting dressed feels like climbing a mountain. I'm exhausted all the time.",
        "label": "depression",
        "category": "fatigue"
    },
    {
        "text": "I've been crying every day for no reason. I feel this heavy emptiness in my chest that won't go away.",
        "label": "depression",
        "category": "persistent sadness"
    },
    
    # === NO DEPRESSION EXAMPLES ===
    {
        "text": "Had a great day at work today! Finally finished that project I've been working on for weeks.",
        "label": "no-depression",
        "category": "positive achievement"
    },
    {
        "text": "Met up with friends for coffee this morning. It's so nice catching up and making plans for the weekend.",
        "label": "no-depression",
        "category": "social connection"
    },
    {
        "text": "This week has been challenging but I'm learning a lot. Looking forward to improving and growing.",
        "label": "no-depression",
        "category": "growth mindset"
    },
    {
        "text": "Just finished a long run and feeling energized! Exercise always helps clear my head.",
        "label": "no-depression",
        "category": "physical activity"
    },
    {
        "text": "I'm excited about my upcoming vacation. Been planning activities and can't wait to explore new places.",
        "label": "no-depression",
        "category": "future orientation"
    },
    {
        "text": "Had a minor setback at work but I'm confident I can figure it out. Everyone has off days sometimes.",
        "label": "no-depression",
        "category": "resilience"
    },
    {
        "text": "Spent the evening cooking dinner with my family. Simple moments like these make me happy.",
        "label": "no-depression",
        "category": "contentment"
    },
    {
        "text": "Started reading a new book and I'm completely hooked. Love getting lost in a good story.",
        "label": "no-depression",
        "category": "engagement/interest"
    },
    {
        "text": "Grateful for the support system I have. My friends and family have been amazing lately.",
        "label": "no-depression",
        "category": "gratitude"
    },
    {
        "text": "Work was stressful but I handled it well. Taking a relaxing bath now and feeling better already.",
        "label": "no-depression",
        "category": "coping"
    },
    
    # === AMBIGUOUS/EDGE CASES ===
    {
        "text": "Today was okay, nothing special. Just went through the motions like usual.",
        "label": "no-depression",
        "category": "neutral"
    },
    {
        "text": "Feeling a bit tired today. Probably need more sleep. Will try to go to bed earlier tonight.",
        "label": "no-depression",
        "category": "minor fatigue"
    },
]


def load_csv_test_cases(filepath: str, text_column: str = None, label_column: str = None,
                        depression_threshold: int = None, include_neutral: bool = False) -> list[dict]:
    """
    Load test cases from a CSV file.
    
    Auto-detects:
    - Delimiter (comma, semicolon, tab)
    - Text column (looks for 'text', 'content', 'message', 'input', or first column)
    - Label column (looks for 'label', 'class', 'category', 'target', or second column)
    
    Numeric label mapping (0-4 scale):
    - 4: Anxiety
    - 3: Anger
    - 2: None
    - 1: Happiness
    - 0: Sadness
    
    Or use depression_threshold: labels <= threshold = depression
    
    Args:
        filepath: Path to CSV file
        text_column: Override auto-detection for text column name
        label_column: Override auto-detection for label column name
        depression_threshold: If set, labels <= this value = depression (e.g., 1 means 0,1 = depression)
        include_neutral: If True, include label=2 entries as 'neutral' instead of skipping
        
    Returns:
        List of test case dictionaries with 'text' and 'label' keys
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    # Read file content to detect delimiter
    with open(filepath, 'r', encoding='utf-8') as f:
        sample = f.read(4096)
        f.seek(0)
        
        # Detect delimiter
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample, delimiters=',;\t|')
            delimiter = dialect.delimiter
        except csv.Error:
            # Default to comma if detection fails
            delimiter = ','
        
        logger.info(f"Detected delimiter: {repr(delimiter)}")
        
        # Read CSV
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)
    
    if not rows:
        raise ValueError(f"CSV file is empty: {filepath}")
    
    # Get column names (lowercase for matching)
    columns = list(rows[0].keys())
    columns_lower = {c.lower().strip(): c for c in columns}
    
    logger.info(f"CSV columns: {columns}")
    
    # Auto-detect text column
    text_col_candidates = ['text', 'content', 'message', 'input', 'sentence', 'post', 'tweet']
    if text_column:
        text_col = text_column
    else:
        text_col = None
        for candidate in text_col_candidates:
            if candidate in columns_lower:
                text_col = columns_lower[candidate]
                break
        if not text_col:
            text_col = columns[0]  # Default to first column
    
    # Auto-detect label column
    label_col_candidates = ['label', 'class', 'category', 'target', 'classification', 'depression']
    if label_column:
        label_col = label_column
    else:
        label_col = None
        for candidate in label_col_candidates:
            if candidate in columns_lower:
                label_col = columns_lower[candidate]
                break
        if not label_col and len(columns) > 1:
            label_col = columns[1]  # Default to second column
    
    logger.info(f"Using text column: '{text_col}', label column: '{label_col}'")
    
    # Build test cases
    test_cases = []
    skipped_neutral = 0
    
    for i, row in enumerate(rows):
        text = row.get(text_col, '').strip()
        if not text:
            logger.warning(f"Skipping empty row {i + 1}")
            continue
        
        case = {"text": text}
        
        # Get label if available
        if label_col and label_col in row:
            raw_label = row[label_col].strip()
            
            # Check if label is numeric (0-4 scale)
            if raw_label.isdigit():
                num_label = int(raw_label)
                case['original_label'] = num_label  # Keep original for reference
                
                if depression_threshold is not None:
                    # User-defined threshold: <= threshold = depression
                    case['label'] = 'depression' if num_label <= depression_threshold else 'no-depression'
                else:
                    # Default mapping for 0-4 scale:
                    # 0 = depression (clear depression indicators)
                    # 1 = no-depression (positive/healthy)
                    # 2 = neutral (skip these - usually random/unrelated)
                    # 3 = depression (moderate depression)
                    # 4 = no-depression (uncertain/mixed but leaning healthy)
                    if num_label == 2:
                        if include_neutral:
                            case['label'] = 'neutral'
                        else:
                            skipped_neutral += 1
                            continue  # Skip neutral entries
                    elif num_label in [0, 3]:
                        case['label'] = 'depression'
                    elif num_label in [1, 4]:
                        case['label'] = 'no-depression'
                    else:
                        case['label'] = 'unknown'
            else:
                # Handle text labels
                label = raw_label.lower()
                if label in ['depression', 'depressed', 'yes', 'positive', 'true']:
                    case['label'] = 'depression'
                elif label in ['no-depression', 'not depressed', 'no depression', 'no', 'negative', 'false']:
                    case['label'] = 'no-depression'
                else:
                    case['label'] = label
        else:
            case['label'] = 'unknown'  # No label for unlabeled data
        
        # Add any additional columns as metadata
        for col in columns:
            if col not in [text_col, label_col] and row.get(col):
                case[col.lower()] = row[col]
        
        test_cases.append(case)
    
    if skipped_neutral > 0:
        logger.info(f"Skipped {skipped_neutral} neutral entries (label=2)")
    
    logger.info(f"Loaded {len(test_cases)} test cases from CSV")
    return test_cases


def extract_prediction(response: dict, prompt_type: str) -> tuple[str, float]:
    """
    Extract the predicted class and confidence from model response.
    Different prompt types return different response structures.
    """
    try:
        analysis = response.get("analysis", response)
        
        # Handle different response formats based on prompt type
        if prompt_type == "simple":
            prediction = analysis.get("prediction", {})
            pred_class = prediction.get("class", "unknown")
            confidence = prediction.get("confidence", 0.0)
            
        elif prompt_type == "structured":
            likelihood = analysis.get("depression_likelihood", "").lower()
            confidence = analysis.get("confidence", 0) / 100.0
            pred_class = "depression" if likelihood in ["high", "medium"] else "no-depression"
            
        elif prompt_type == "chain_of_thought":
            final = analysis.get("final_classification", {})
            likelihood = final.get("depression_likelihood", "").lower()
            confidence = final.get("confidence", 0) / 100.0
            pred_class = "depression" if likelihood in ["high", "medium"] else "no-depression"
            
        elif prompt_type == "few_shot":
            assessment = analysis.get("assessment", "").lower()
            confidence = analysis.get("confidence", 0) / 100.0
            pred_class = "depression" if assessment in ["high", "medium"] else "no-depression"
            
        elif prompt_type == "feature_extraction":
            overall = analysis.get("overall_assessment", {})
            prob = overall.get("depression_probability", 0.0)
            confidence = overall.get("confidence_score", 0.0)
            pred_class = "depression" if prob >= 0.5 else "no-depression"
            
        else:
            # Default extraction
            pred_class = analysis.get("class", "unknown")
            confidence = analysis.get("confidence", 0.0)
            
        # Normalize class names
        if "depress" in pred_class.lower():
            pred_class = "depression"
        elif pred_class.lower() in ["no-depression", "no depression", "none", "low"]:
            pred_class = "no-depression"
            
        return pred_class, confidence
        
    except Exception as e:
        logger.error(f"Error extracting prediction: {e}")
        return "unknown", 0.0


def evaluate_model(model: str, prompt_type: str, test_cases: list[dict]) -> dict:
    """
    Evaluate a single model/prompt combination on the test set.
    """
    results = {
        "model": model,
        "prompt_type": prompt_type,
        "total": len(test_cases),
        "correct": 0,
        "true_positives": 0,  # Correctly identified depression
        "true_negatives": 0,  # Correctly identified no-depression
        "false_positives": 0, # Incorrectly flagged as depression
        "false_negatives": 0, # Missed depression
        "errors": 0,
        "predictions": []
    }
    
    last_request_time = 0.0
    
    for idx, case in enumerate(test_cases):
        # Rate limiting
        elapsed = time.time() - last_request_time
        if elapsed < MIN_REQUEST_INTERVAL and last_request_time > 0:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        
        logger.info(f"[{idx + 1}/{len(test_cases)}] Testing: {case['text'][:50]}...")
        
        try:
            last_request_time = time.time()
            response = analyze_with_groq(case["text"], model, prompt_type)
            predicted, confidence = extract_prediction(response, prompt_type)
            
            expected = case["label"]
            is_correct = predicted == expected
            
            # Update metrics
            if is_correct:
                results["correct"] += 1
                if expected == "depression":
                    results["true_positives"] += 1
                else:
                    results["true_negatives"] += 1
            else:
                if expected == "depression":
                    results["false_negatives"] += 1
                else:
                    results["false_positives"] += 1
            
            results["predictions"].append({
                "text": case["text"][:80] + "..." if len(case["text"]) > 80 else case["text"],
                "category": case.get("category", "unknown"),
                "expected": expected,
                "predicted": predicted,
                "confidence": confidence,
                "correct": is_correct
            })
            
        except Exception as e:
            logger.error(f"Error analyzing case {idx + 1}: {e}")
            results["errors"] += 1
            results["predictions"].append({
                "text": case["text"][:80],
                "expected": case["label"],
                "predicted": "error",
                "error": str(e),
                "correct": False
            })
    
    # Calculate final metrics
    results["accuracy"] = results["correct"] / results["total"] if results["total"] > 0 else 0
    
    # Precision: Of all depression predictions, how many were correct?
    total_predicted_positive = results["true_positives"] + results["false_positives"]
    results["precision"] = results["true_positives"] / total_predicted_positive if total_predicted_positive > 0 else 0
    
    # Recall: Of all actual depression cases, how many did we catch?
    total_actual_positive = results["true_positives"] + results["false_negatives"]
    results["recall"] = results["true_positives"] / total_actual_positive if total_actual_positive > 0 else 0
    
    # F1 Score
    if results["precision"] + results["recall"] > 0:
        results["f1_score"] = 2 * (results["precision"] * results["recall"]) / (results["precision"] + results["recall"])
    else:
        results["f1_score"] = 0
    
    return results


def print_results(results: dict):
    """Pretty print evaluation results."""
    print("\n" + "=" * 70)
    print(f"MODEL: {results['model']}")
    print(f"PROMPT TYPE: {results['prompt_type']}")
    print("=" * 70)
    
    print(f"\n📊 METRICS:")
    print(f"   Accuracy:  {results['accuracy']:.1%} ({results['correct']}/{results['total']})")
    print(f"   Precision: {results['precision']:.1%}")
    print(f"   Recall:    {results['recall']:.1%}")
    print(f"   F1 Score:  {results['f1_score']:.3f}")
    
    print(f"\n📈 CONFUSION MATRIX:")
    print(f"   True Positives:  {results['true_positives']} (correctly identified depression)")
    print(f"   True Negatives:  {results['true_negatives']} (correctly identified no-depression)")
    print(f"   False Positives: {results['false_positives']} (wrongly flagged as depression)")
    print(f"   False Negatives: {results['false_negatives']} (missed depression cases)")
    
    if results['errors'] > 0:
        print(f"\n⚠️  Errors: {results['errors']}")
    
    # Show incorrect predictions
    incorrect = [p for p in results['predictions'] if not p.get('correct')]
    if incorrect:
        print(f"\n❌ INCORRECT PREDICTIONS ({len(incorrect)}):")
        for pred in incorrect[:5]:  # Show first 5
            print(f"   • Expected: {pred['expected']}, Got: {pred['predicted']}")
            print(f"     Text: \"{pred['text']}\"")
            print()


def save_results(all_results: list[dict], filename: str):
    """Save results to JSON file."""
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_models_tested": len(all_results),
        "results": all_results
    }
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    logger.info(f"Results saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Zero-shot evaluation for depression detection")
    parser.add_argument("--model", type=str, help="Specific model to test (default: all)")
    parser.add_argument("--prompt", type=str, help="Specific prompt type to test (default: chain_of_thought)")
    parser.add_argument("--output", type=str, default="evaluation_results.json", help="Output JSON file")
    parser.add_argument("--all", action="store_true", help="Test all model/prompt combinations")
    parser.add_argument("--all-models", action="store_true", help="Test all models with default prompt")
    parser.add_argument("--csv", type=str, help="Path to CSV file with test cases")
    parser.add_argument("--text-column", type=str, help="CSV column name for text (auto-detected if not specified)")
    parser.add_argument("--label-column", type=str, help="CSV column name for labels (auto-detected if not specified)")
    parser.add_argument("--depression-threshold", type=int, help="For 0-4 scale: labels <= threshold = depression (e.g., 0 means only 0=depression)")
    parser.add_argument("--include-neutral", action="store_true", help="Include neutral entries (label=2) instead of skipping them")
    args = parser.parse_args()
    
    all_results = []
    
    # Load test cases from CSV or use built-in dataset
    if args.csv:
        test_cases = load_csv_test_cases(
            args.csv, 
            args.text_column, 
            args.label_column,
            depression_threshold=args.depression_threshold,
            include_neutral=args.include_neutral
        )
        print(f"\n📁 Loaded {len(test_cases)} test cases from: {args.csv}")
    else:
        test_cases = TEST_CASES
        print(f"\n📋 Using built-in test dataset ({len(test_cases)} cases)")
    
    if args.all:
        # Test all combinations
        models_to_test = MODELS
        prompts_to_test = PROMPT_TYPES
    elif args.all_models:
        models_to_test = MODELS
        prompts_to_test = ["chain_of_thought"]  # Default prompt for all models
    else:
        models_to_test = [args.model] if args.model else ["llama-3.3-70b-versatile"]
        prompts_to_test = [args.prompt] if args.prompt else ["chain_of_thought"]
    
    print(f"\n🔬 Zero-Shot Evaluation")
    print(f"   Models: {models_to_test}")
    print(f"   Prompts: {prompts_to_test}")
    print(f"   Test cases: {len(test_cases)}")
    print(f"   Rate limit: {REQUESTS_PER_MINUTE} requests/minute")
    
    total_tests = len(models_to_test) * len(prompts_to_test)
    estimated_time = (len(test_cases) * total_tests * MIN_REQUEST_INTERVAL) / 60
    print(f"   Estimated time: ~{estimated_time:.1f} minutes\n")
    
    for model in models_to_test:
        for prompt_type in prompts_to_test:
            print(f"\n🚀 Testing {model} with {prompt_type} prompt...")
            results = evaluate_model(model, prompt_type, test_cases)
            all_results.append(results)
            print_results(results)
    
    # Summary
    if len(all_results) > 1:
        print("\n" + "=" * 70)
        print("📋 SUMMARY - RANKED BY F1 SCORE")
        print("=" * 70)
        sorted_results = sorted(all_results, key=lambda x: x['f1_score'], reverse=True)
        for i, r in enumerate(sorted_results, 1):
            print(f"{i}. {r['model']} + {r['prompt_type']}")
            print(f"   F1: {r['f1_score']:.3f} | Acc: {r['accuracy']:.1%} | Prec: {r['precision']:.1%} | Rec: {r['recall']:.1%}")
    
    # Save results
    save_results(all_results, args.output)
    print(f"\n✅ Evaluation complete. Results saved to {args.output}")


if __name__ == "__main__":
    main()
