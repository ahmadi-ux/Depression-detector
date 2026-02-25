"""
Shared Groq-based LLM handler for multiple models.
Consolidates common functionality across Llama, ChatGPT, Kimi, Qwen, and Compound engines.
"""

import json
import os
import logging
from dotenv import load_dotenv
from groq import Groq
from .prompts import get_prompt

import os
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
logger = logging.getLogger(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
if not client.api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")


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
    prompt = get_prompt(prompt_type, text)
    
    logger.debug(f"Analyzing with model: {model}, prompt_type: {prompt_type}")
    logger.debug(f"Text length: {len(text)} characters")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2048,
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
