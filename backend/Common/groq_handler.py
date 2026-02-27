"""
Shared Groq-based LLM handler for multiple models.
Consolidates common functionality across Llama, ChatGPT, Kimi, Qwen, and Compound engines.
"""

import csv
import io
import json
import os
import logging
from dotenv import load_dotenv
from groq import Groq
from .prompts import get_prompt

import os
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
logger = logging.getLogger(__name__)

# Token limits - leave 500 token buffer from 6000 limit
MAX_TOTAL_TOKENS = 5500
MAX_OUTPUT_TOKENS = 1024  # Reserve for response
MAX_INPUT_TOKENS = MAX_TOTAL_TOKENS - MAX_OUTPUT_TOKENS  # ~4476 for prompt + text
CHARS_PER_TOKEN = 4  # Rough estimate for English text

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
if not client.api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")


def parse_csv_input(content: str, text_column: str = None, label_column: str = None,
                    depression_threshold: int = None, include_neutral: bool = False) -> list[dict]:
    """
    Parse CSV content and extract text entries with optional labels.
    
    Auto-detects delimiter (comma, semicolon, tab, pipe).
    Auto-detects text and label columns if not specified.
    
    Numeric label mapping (0-4 scale):
    - 4: Anxiety
    - 3: Anger
    - 2: None
    - 1: Happiness
    - 0: Sadness
    
    Args:
        content: CSV content as string
        text_column: Column name containing text (auto-detected if None)
        label_column: Column name containing labels (auto-detected if None)
        depression_threshold: If set, labels <= this value = depression
        include_neutral: If True, include label=2 entries
        
    Returns:
        List of dicts with 'text' and optionally 'label', 'original_label'
    """
    # Detect delimiter
    sample = content[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ','
    
    logger.info(f"CSV delimiter detected: {repr(delimiter)}")
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    rows = list(reader)
    
    if not rows:
        logger.warning("CSV is empty, returning content as single entry")
        return [{"text": content}]
    
    # Get columns
    columns = list(rows[0].keys())
    columns_lower = {c.lower().strip(): c for c in columns}
    
    logger.info(f"CSV columns: {columns}")
    
    # Auto-detect text column
    text_col_candidates = ['text', 'content', 'message', 'input', 'sentence', 'post', 'tweet', 'body']
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
    
    # Extract entries
    entries = []
    skipped_neutral = 0
    
    for row in rows:
        text = row.get(text_col, '').strip()
        if not text:
            continue
        
        entry = {"text": text}
        
        # Get label if available
        if label_col and label_col in row:
            raw_label = row[label_col].strip()
            
            # Check if label is numeric (0-4 scale)
            if raw_label.isdigit():
                num_label = int(raw_label)
                entry['original_label'] = num_label
                
                if depression_threshold is not None:
                    entry['label'] = 'depression' if num_label <= depression_threshold else 'no-depression'
                else:
                    # Default mapping for 0-4 scale
                    if num_label == 2:
                        if include_neutral:
                            entry['label'] = 'neutral'
                        else:
                            skipped_neutral += 1
                            continue  # Skip neutral entries
                    elif num_label in [0, 3]:
                        entry['label'] = 'depression'
                    elif num_label in [1, 4]:
                        entry['label'] = 'no-depression'
                    else:
                        entry['label'] = 'unknown'
            else:
                # Text labels
                label = raw_label.lower()
                if label in ['depression', 'depressed', 'yes', 'positive', 'true', '1']:
                    entry['label'] = 'depression'
                elif label in ['no-depression', 'not depressed', 'no depression', 'no', 'negative', 'false', '0']:
                    entry['label'] = 'no-depression'
                else:
                    entry['label'] = label
        
        entries.append(entry)
    
    if skipped_neutral > 0:
        logger.info(f"Skipped {skipped_neutral} neutral entries (label=2)")
    
    logger.info(f"Extracted {len(entries)} entries from CSV")
    return entries


def is_csv_content(content: str) -> bool:
    """
    Check if content appears to be CSV format.
    
    Returns True if:
    - Content has multiple lines with consistent delimiters
    - First line looks like a header row
    """
    lines = content.strip().split('\n')
    if len(lines) < 2:
        return False
    
    # Check for common delimiters
    first_line = lines[0]
    for delim in [',', ';', '\t', '|']:
        if delim in first_line:
            # Check if delimiter count is consistent
            first_count = first_line.count(delim)
            if first_count > 0:
                # Check at least 3 lines have same delimiter count
                consistent = sum(1 for line in lines[1:4] if line.count(delim) == first_count)
                if consistent >= min(2, len(lines) - 1):
                    return True
    return False


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses ~4 characters per token as rough approximation for English.
    For more accurate counts, use tiktoken library.
    """
    return len(text) // CHARS_PER_TOKEN


def truncate_to_token_limit(text: str, max_tokens: int) -> str:
    """
    Truncate text to stay within token limit.
    Tries to truncate at sentence boundaries when possible.
    
    Args:
        text: Input text to truncate
        max_tokens: Maximum tokens allowed
        
    Returns:
        Truncated text
    """
    estimated = estimate_tokens(text)
    if estimated <= max_tokens:
        return text
    
    # Calculate max characters
    max_chars = max_tokens * CHARS_PER_TOKEN
    truncated = text[:max_chars]
    
    # Try to truncate at last sentence boundary
    last_period = truncated.rfind('.')
    last_question = truncated.rfind('?')
    last_exclaim = truncated.rfind('!')
    last_boundary = max(last_period, last_question, last_exclaim)
    
    if last_boundary > max_chars * 0.7:  # Only if we keep at least 70%
        truncated = truncated[:last_boundary + 1]
    
    logger.warning(f"Text truncated from ~{estimated} to ~{estimate_tokens(truncated)} tokens")
    return truncated


def clean_json_response(raw_response: str) -> dict:
    """
    Clean and parse JSON response from LLM.
    Handles cases where LLM wraps JSON in markdown code blocks.
    Extracts the first balanced JSON object/array.
    """
    import re
    raw = raw_response.strip()
    
    # Remove markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        if "\n" in raw:
            raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    
    raw = raw.strip()
    
    # Find the first { or [
    start_idx = -1
    start_char = None
    for i, char in enumerate(raw):
        if char == '{':
            start_idx = i
            start_char = '{'
            break
        elif char == '[':
            start_idx = i
            start_char = '['
            break
    
    if start_idx == -1:
        # No JSON found, try original logic
        try:
            return json.loads(raw.strip())
        except Exception as e:
            raise ValueError(f"Could not extract valid JSON from: {raw_response}\nError: {e}")
    
    # Extract from start_idx to the matching closing brace/bracket
    json_str = extract_balanced_json(raw[start_idx:], start_char)
    
    if json_str:
        # Clean up common JSON issues
        json_str_fixed = json_str.replace("'", '"')
        json_str_fixed = re.sub(r',\s*([}\]])', r'\1', json_str_fixed)
        json_str_fixed = re.sub(r':\s*([}\]])', r': null\1', json_str_fixed)
        
        # Try to parse with duplicate key handling
        try:
            from collections import OrderedDict
            def no_dup_object_pairs_hook(pairs):
                d = OrderedDict()
                for k, v in pairs:
                    if k not in d:
                        d[k] = v
                return d
            return json.loads(json_str_fixed, object_pairs_hook=no_dup_object_pairs_hook)
        except Exception:
            pass
        
        # Try normal parse
        try:
            return json.loads(json_str_fixed)
        except Exception:
            pass
    
    # Final fallback
    try:
        return json.loads(raw.strip())
    except Exception as e:
        raise ValueError(f"Could not extract valid JSON from: {raw_response}\nError: {e}")


def extract_balanced_json(json_str: str, start_char: str) -> str:
    """
    Extract a balanced JSON object or array from a string.
    
    Args:
        json_str: String starting with { or [
        start_char: Opening character ('{' or '[')
    
    Returns:
        Extracted JSON string with balanced braces/brackets
    """
    if not json_str or json_str[0] != start_char:
        return ""
    
    end_char = '}' if start_char == '{' else ']'
    depth = 0
    in_string = False
    escape_next = False
    
    for i, char in enumerate(json_str):
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"':
            in_string = not in_string
            continue
        
        if in_string:
            continue
        
        if char == start_char:
            depth += 1
        elif char == end_char:
            depth -= 1
            if depth == 0:
                return json_str[:i+1]
    
    # If we get here, the JSON is unbalanced, return what we have
    return json_str


def analyze_with_groq(text: str, model: str, prompt_type: str = "simple") -> dict:
    """
    Generic Groq-based analysis for any model.
    
    Args:
        text: Text to analyze
        model: Groq model identifier (e.g., "llama-3.1-8b-instant")
        prompt_type: Type of analysis prompt to use
        
    Returns:
        Dictionary with "analysis" and "prompt_type" keys
    """
    # Estimate prompt template size (without text) - roughly 500-1500 tokens depending on prompt type
    prompt_template_tokens = 1500  # Conservative estimate for longest prompts
    max_text_tokens = MAX_INPUT_TOKENS - prompt_template_tokens
    
    # Truncate text if needed
    truncated_text = truncate_to_token_limit(text, max_text_tokens)
    prompt = get_prompt(prompt_type, truncated_text)
    
    # Final check on total prompt size
    prompt_tokens = estimate_tokens(prompt)
    if prompt_tokens > MAX_INPUT_TOKENS:
        logger.warning(f"Prompt still exceeds limit: ~{prompt_tokens} tokens")
    
    logger.debug(f"Analyzing with model: {model}, prompt_type: {prompt_type}")
    logger.debug(f"Text length: {len(truncated_text)} chars (~{estimate_tokens(truncated_text)} tokens)")
    logger.debug(f"Total prompt: ~{prompt_tokens} tokens, max output: {MAX_OUTPUT_TOKENS} tokens")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=MAX_OUTPUT_TOKENS,
    )
    
    raw_response = response.choices[0].message.content.strip()
    logger.info(f"{'='*80}")
    logger.info(f"RAW RESPONSE FROM {model.upper()}")
    logger.info(f"{'='*80}")
    logger.info(f"Response length: {len(raw_response)} characters")
    logger.info(f"Response content:\n{raw_response}")
    logger.info(f"{'='*80}\n")
    
    try:
        data = clean_json_response(raw_response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Raw response was: {repr(raw_response)}")
        raise ValueError(f"Invalid JSON from LLM: {e}")
    
    return {
        "analysis": data,
        "prompt_type": prompt_type
    }


def analyze_csv_content(content: str, model: str, prompt_type: str = "simple", 
                        text_column: str = None, label_column: str = None,
                        depression_threshold: int = None, include_neutral: bool = False,
                        rate_limit_seconds: float = 2.0) -> dict:
    """
    Analyze multiple text entries from CSV content.
    
    Supports numeric labels (0-4 scale) and tracks accuracy when labels are present.
    
    Args:
        content: CSV content as string
        model: Groq model identifier
        prompt_type: Type of analysis prompt to use
        text_column: Column name for text (auto-detected if None)
        label_column: Column name for labels (auto-detected if None)
        depression_threshold: If set, labels <= this value = depression
        include_neutral: If True, include label=2 entries
        rate_limit_seconds: Delay between API calls (default: 2.0 for 30 req/min)
        
    Returns:
        Dictionary with individual results, aggregate statistics, and accuracy metrics
    """
    import time
    
    entries = parse_csv_input(content, text_column, label_column, 
                              depression_threshold, include_neutral)
    logger.info(f"Analyzing {len(entries)} entries from CSV")
    
    results = []
    depressed_count = 0
    not_depressed_count = 0
    error_count = 0
    
    # Accuracy tracking (when labels are available)
    true_positives = 0
    true_negatives = 0
    false_positives = 0
    false_negatives = 0
    has_labels = False
    
    for idx, entry in enumerate(entries):
        text = entry['text']
        expected_label = entry.get('label')
        original_label = entry.get('original_label')
        
        if expected_label and expected_label not in ['unknown', 'neutral']:
            has_labels = True
        
        logger.info(f"Processing entry {idx + 1}/{len(entries)}")
        
        # Rate limiting
        if idx > 0:
            time.sleep(rate_limit_seconds)
        
        try:
            response = analyze_with_groq(text, model, prompt_type)
            analysis = response.get("analysis", {})
            
            # Extract classification
            prediction = analysis.get("prediction", {})
            pred_class = prediction.get("class", "unknown")
            confidence = prediction.get("confidence", 0.0)
            
            # Normalize prediction
            if "depress" in pred_class.lower() and "no" not in pred_class.lower():
                depressed_count += 1
                pred_class = "depression"
            elif pred_class.lower() in ["no-depression", "no depression", "none", "no"]:
                not_depressed_count += 1
                pred_class = "no-depression"
            
            # Track accuracy if we have labels
            is_correct = None
            if expected_label and expected_label in ['depression', 'no-depression']:
                is_correct = pred_class == expected_label
                if pred_class == "depression":
                    if expected_label == "depression":
                        true_positives += 1
                    else:
                        false_positives += 1
                elif pred_class == "no-depression":
                    if expected_label == "no-depression":
                        true_negatives += 1
                    else:
                        false_negatives += 1
            
            result_entry = {
                "entry_number": idx + 1,
                "text": text[:100] + "..." if len(text) > 100 else text,
                "predicted": pred_class,
                "confidence": confidence,
                "full_analysis": analysis
            }
            
            if expected_label:
                result_entry["expected"] = expected_label
                result_entry["correct"] = is_correct
            if original_label is not None:
                result_entry["original_label"] = original_label
            
            results.append(result_entry)
            
        except Exception as e:
            logger.error(f"Error analyzing entry {idx + 1}: {e}")
            error_count += 1
            results.append({
                "entry_number": idx + 1,
                "text": text[:100] + "..." if len(text) > 100 else text,
                "predicted": "error",
                "expected": expected_label,
                "error": str(e)
            })
    
    # Calculate statistics
    total_analyzed = depressed_count + not_depressed_count
    depression_ratio = depressed_count / total_analyzed if total_analyzed > 0 else 0
    
    output = {
        "analysis": {
            "total_entries": len(entries),
            "depressed_count": depressed_count,
            "not_depressed_count": not_depressed_count,
            "error_count": error_count,
            "depression_ratio": depression_ratio,
            "entries": results
        },
        "model": model,
        "prompt_type": prompt_type
    }
    
    # Add accuracy metrics if labels were present
    if has_labels:
        total_labeled = true_positives + true_negatives + false_positives + false_negatives
        accuracy = (true_positives + true_negatives) / total_labeled if total_labeled > 0 else 0
        
        # Precision: Of all depression predictions, how many were correct?
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        
        # Recall: Of all actual depression cases, how many did we catch?
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        # F1 Score
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        output["accuracy_metrics"] = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "true_negatives": true_negatives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "total_labeled": total_labeled
        }
    
    return output
