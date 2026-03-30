"""
Compare multiple test results files and generate analysis.
Extracts statistics from each result file and provides:
- Model performance comparison (accuracy, precision, recall, F1)
- Common misclassifications across models
- Timestamp tracking for performance over time
- Detailed error analysis
"""

import os
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def safe_to_int(value) -> int:
    """Safely convert value to int, returns 0 if fails."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value).strip())
    except (ValueError, AttributeError):
        return 0


def safe_to_float(value) -> float:
    """Safely convert value to float, returns 0.0 if fails."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (ValueError, AttributeError):
        return 0.0


def get_stat(stats: dict, key: str, default=0):
    """Get a stat value, trying common key variations."""
    # Try exact key first
    if key in stats:
        return stats[key]
    
    # Try with different spacing/formatting
    variants = [
        key.lower(),
        key.upper(),
        key.replace(' ', ''),
        key.replace('Score', 'score'),
    ]
    
    for variant in variants:
        for k, v in stats.items():
            if k.lower() == variant.lower() or k.replace(' ', '').lower() == variant.lower():
                return v
    
    return default


def format_number(value, decimals: int = 4) -> str:
    """Safely format a number value, handling both floats and strings."""
    if value is None or value == 'N/A':
        return 'N/A'
    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}"
    return str(value)


def parse_result_file(file_path: str) -> dict:
    """
    Parse a single result file.
    
    Returns dict with:
    - stats: header line statistics (TP, FP, TN, FN, ERROR, metrics)
    - errors: list of error entries with text and labels
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
    
    if not lines:
        return None
    
    # Parse header line - format is: Key1: Value1 Key2: Value2 Key3: Value3
    header = lines[0].strip()
    stats = {}
    
    import re
    # More specific regex that handles multi-word keys
    # This will match: "F1 Score: 0.8584" or "Model: llama-3.1-8b-instant"
    pattern = r'((?:[A-Z][a-z]*\s)*[A-Z][a-z]*):\s+([^\s]+)'
    matches = re.findall(pattern, header)
    
    for key, value in matches:
        key = key.strip()
        value = value.strip()
        
        # Try to convert to number if possible
        try:
            if '.' in value:
                stats[key] = float(value)
            else:
                stats[key] = int(value)
        except ValueError:
            stats[key] = value
    
    # Parse error entries
    errors = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        
        error_type = None
        if line.startswith('FP'):
            error_type = 'FP'
        elif line.startswith('FN'):
            error_type = 'FN'
        elif line.startswith('ERROR'):
            error_type = 'ERROR'
        
        if not error_type:
            continue
        
        # Extract label and text
        error_dict = {'type': error_type, 'raw': line}
        
        if 'Label:' in line and 'Predicted:' in line and 'Text:' in line:
            try:
                label_part = line.split('Label:')[1].split('|')[0].strip()
                pred_part = line.split('Predicted:')[1].split('|')[0].strip()
                text_part = line.split('Text:')[1].strip()
                
                error_dict['label'] = label_part
                error_dict['predicted'] = pred_part
                error_dict['text'] = text_part[:100]  # First 100 chars
            except:
                pass
        
        errors.append(error_dict)
    
    return {
        'stats': stats,
        'errors': errors,
        'file_path': file_path
    }


def get_results_files(results_dir: str) -> list:
    """Get all result files sorted by timestamp (newest first)."""
    files = []
    for f in os.listdir(results_dir):
        if f.endswith('.txt'):
            files.append(os.path.join(results_dir, f))
    
    # Sort by modification time, newest first
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files


def generate_comparison_report(results_dir: str, output_file: str = None) -> str:
    """Generate a comprehensive comparison report."""
    
    results_dir = Path(results_dir)
    files = get_results_files(str(results_dir))
    
    if not files:
        return "No result files found."
    
    report = []
    report.append("=" * 80)
    report.append("TEST RESULTS COMPARISON REPORT")
    report.append("=" * 80)
    report.append(f"\nScanned {len(files)} result file(s)")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Parse all files
    parsed_results = []
    for file_path in files:
        parsed = parse_result_file(file_path)
        if parsed:
            parsed_results.append(parsed)
    
    if not parsed_results:
        return "No valid result files found."
    
    # Section 1: Performance Comparison Table
    report.append("-" * 80)
    report.append("PERFORMANCE COMPARISON")
    report.append("-" * 80)
    
    # Create comparison table
    headers = ['Model', 'Prompt', 'Accuracy', 'Precision', 'Recall', 'F1 Score', 'TP', 'FP', 'TN', 'FN']
    report.append(f"{headers[0]:<30} {headers[1]:<20} {headers[2]:<12} {headers[3]:<12} {headers[4]:<12} {headers[5]:<12} {headers[6]:<6} {headers[7]:<6} {headers[8]:<6} {headers[9]:<6}")
    report.append("-" * 120)
    
    for result in parsed_results:
        stats = result['stats']
        model = str(get_stat(stats, 'Model', 'Unknown'))[:30]
        prompt = str(get_stat(stats, 'Prompt', 'Unknown'))[:20]
        accuracy = format_number(get_stat(stats, 'Accuracy', 0))
        precision = format_number(get_stat(stats, 'Precision', 0))
        recall = format_number(get_stat(stats, 'Recall', 0))
        f1 = format_number(get_stat(stats, 'F1 Score', 0))
        tp = str(safe_to_int(get_stat(stats, 'TP', 0)))[:6]
        fp = str(safe_to_int(get_stat(stats, 'FP', 0)))[:6]
        tn = str(safe_to_int(get_stat(stats, 'TN', 0)))[:6]
        fn = str(safe_to_int(get_stat(stats, 'FN', 0)))[:6]
        
        report.append(f"{model:<30} {prompt:<20} {accuracy:<12} {precision:<12} {recall:<12} {f1:<12} {tp:<6} {fp:<6} {tn:<6} {fn:<6}")
    
    # Section 2: Best and Worst Performers
    report.append("\n" + "-" * 80)
    report.append("BEST AND WORST PERFORMERS")
    report.append("-" * 80)
    
    if parsed_results:
        # Best by accuracy
        best_acc = max(parsed_results, key=lambda x: safe_to_float(get_stat(x['stats'], 'Accuracy', 0)))
        report.append(f"\nHighest Accuracy:")
        report.append(f"  Model: {get_stat(best_acc['stats'], 'Model', 'Unknown')}")
        report.append(f"  Prompt: {get_stat(best_acc['stats'], 'Prompt', 'Unknown')}")
        report.append(f"  Accuracy: {format_number(get_stat(best_acc['stats'], 'Accuracy', 'N/A'))}")
        report.append(f"  F1 Score: {format_number(get_stat(best_acc['stats'], 'F1 Score', 'N/A'))}")
        
        # Best by F1
        best_f1 = max(parsed_results, key=lambda x: safe_to_float(get_stat(x['stats'], 'F1 Score', 0)))
        report.append(f"\nHighest F1 Score:")
        report.append(f"  Model: {get_stat(best_f1['stats'], 'Model', 'Unknown')}")
        report.append(f"  Prompt: {get_stat(best_f1['stats'], 'Prompt', 'Unknown')}")
        report.append(f"  F1 Score: {format_number(get_stat(best_f1['stats'], 'F1 Score', 'N/A'))}")
        report.append(f"  Accuracy: {format_number(get_stat(best_f1['stats'], 'Accuracy', 'N/A'))}")
        
        # Worst by accuracy
        worst_acc = min(parsed_results, key=lambda x: safe_to_float(get_stat(x['stats'], 'Accuracy', 1)))
        report.append(f"\nLowest Accuracy:")
        report.append(f"  Model: {get_stat(worst_acc['stats'], 'Model', 'Unknown')}")
        report.append(f"  Prompt: {get_stat(worst_acc['stats'], 'Prompt', 'Unknown')}")
        report.append(f"  Accuracy: {format_number(get_stat(worst_acc['stats'], 'Accuracy', 'N/A'))}")
        report.append(f"  F1 Score: {format_number(get_stat(worst_acc['stats'], 'F1 Score', 'N/A'))}")
    
    # Section 3: Error Analysis - Most Common Misclassifications
    report.append("\n" + "-" * 80)
    report.append("ERROR ANALYSIS - MOST COMMON MISCLASSIFICATION PATTERNS")
    report.append("-" * 80)
    
    fp_patterns = defaultdict(int)  # False positives by label
    fn_patterns = defaultdict(int)  # False negatives by label
    
    for result in parsed_results:
        for error in result['errors']:
            error_type = error['type']
            label = error.get('label', 'Unknown')
            
            if error_type == 'FP':
                fp_patterns[f"Label {label} -> Predicted Depressed"] += 1
            elif error_type == 'FN':
                fn_patterns[f"Label {label} -> Predicted Not-Depressed"] += 1
    
    if fp_patterns:
        report.append("\nMost Common False Positives:")
        for pattern, count in sorted(fp_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"  {pattern}: {count} occurrences")
    
    if fn_patterns:
        report.append("\nMost Common False Negatives:")
        for pattern, count in sorted(fn_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"  {pattern}: {count} occurrences")
    
    # Section 4: Error Count by Model
    report.append("\n" + "-" * 80)
    report.append("ERROR BREAKDOWN BY MODEL")
    report.append("-" * 80)
    report.append(f"\n{'Model':<40} {'FP':<10} {'FN':<10} {'Total':<10}")
    report.append("-" * 70)
    
    for result in parsed_results:
        fp_count = sum(1 for e in result['errors'] if e['type'] == 'FP')
        fn_count = sum(1 for e in result['errors'] if e['type'] == 'FN')
        total = fp_count + fn_count
        model_name = result['stats'].get('Model', 'Unknown')
        prompt = result['stats'].get('Prompt', 'Unknown')
        label = f"{model_name[:30]} ({prompt[:10]})"
        report.append(f"{label:<40} {fp_count:<10} {fn_count:<10} {total:<10}")
    
    # Section 5: Sample Error Examples
    report.append("\n" + "-" * 80)
    report.append("SAMPLE ERROR EXAMPLES")
    report.append("-" * 80)
    report.append("\n" + "-" * 80)
    report.append("SAMPLE ERROR EXAMPLES")
    report.append("-" * 80)
    
    if parsed_results:
        result = parsed_results[0]  # Show examples from first (most recent) result
        fp_examples = [e for e in result['errors'] if e['type'] == 'FP'][:3]
        fn_examples = [e for e in result['errors'] if e['type'] == 'FN'][:3]
        
        if fp_examples:
            report.append(f"\nFalse Positives (from {result['stats'].get('Model', 'Unknown')}):")
            for i, err in enumerate(fp_examples, 1):
                report.append(f"  {i}. Label: {err.get('label', 'N/A')}, Text: {err.get('text', 'N/A')}")
        
        if fn_examples:
            report.append(f"\nFalse Negatives (from {result['stats'].get('Model', 'Unknown')}):")
            for i, err in enumerate(fn_examples, 1):
                report.append(f"  {i}. Label: {err.get('label', 'N/A')}, Text: {err.get('text', 'N/A')}")
    
    # Section 6: Statistics
    report.append("\n" + "-" * 80)
    report.append("AGGREGATE STATISTICS")
    report.append("-" * 80)
    
    if parsed_results:
        total_tp = sum(safe_to_int(r['stats'].get('TP', 0)) for r in parsed_results)
        total_fp = sum(safe_to_int(r['stats'].get('FP', 0)) for r in parsed_results)
        total_tn = sum(safe_to_int(r['stats'].get('TN', 0)) for r in parsed_results)
        total_fn = sum(safe_to_int(r['stats'].get('FN', 0)) for r in parsed_results)
        total_samples = total_tp + total_fp + total_tn + total_fn
        
        report.append(f"\nTotal Across All Models:")
        report.append(f"  True Positives: {total_tp}")
        report.append(f"  False Positives: {total_fp}")
        report.append(f"  True Negatives: {total_tn}")
        report.append(f"  False Negatives: {total_fn}")
        report.append(f"  Total Samples: {total_samples}")
        
        if total_samples > 0:
            overall_accuracy = (total_tp + total_tn) / total_samples
            report.append(f"  Overall Accuracy: {format_number(overall_accuracy)}")
    
    report.append("\n" + "=" * 80)
    
    report_text = "\n".join(report)
    
    # Write to file if specified
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"Report saved to: {output_file}")
        except Exception as e:
            print(f"Error writing report: {e}")
    
    return report_text


def main():
    results_dir = Path(__file__).resolve().parent / "results"
    
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return
    
    # Generate report to console and file
    report = generate_comparison_report(str(results_dir))
    print(report)
    
    # Save to file
    output_file = results_dir / f"comparison_report_{datetime.now().strftime('%m%d_%H%M%S')}.txt"
    generate_comparison_report(str(results_dir), str(output_file))


if __name__ == "__main__":
    main()
