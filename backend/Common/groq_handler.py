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

load_dotenv()
logger = logging.getLogger(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
if not client.api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")


def clean_json_response(raw_response: str) -> dict:
    """
    Clean and parse JSON response from LLM.
    Handles cases where LLM wraps JSON in markdown code blocks.
    """
    raw = raw_response.strip()
    
    # Remove markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        # Check if there's a language specifier (e.g., ```json)
        if "\n" in raw:
            raw = raw.split("\n", 1)[1]
    
    # Remove trailing markdown block if present
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    
    return json.loads(raw.strip())


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
