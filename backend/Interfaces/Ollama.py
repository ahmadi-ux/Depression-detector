# Ollama Interface for Local Model Inference

import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# Ollama API endpoint (default local)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"  # Change to your preferred model (e.g., "neural-chat", "llama2", "zephyr")
OLLAMA_TIMEOUT = 60000  # 1000 minutes timeout for model inference


def set_ollama_model(model_name: str):
    """Set the Ollama model to use"""
    global OLLAMA_MODEL
    OLLAMA_MODEL = model_name
    logger.info(f"Ollama model set to: {OLLAMA_MODEL}")


def set_ollama_url(url: str):
    """Set the Ollama server URL"""
    global OLLAMA_BASE_URL
    OLLAMA_BASE_URL = url
    logger.info(f"Ollama URL set to: {OLLAMA_BASE_URL}")


def set_ollama_timeout(timeout_seconds: int):
    """Set the timeout for Ollama requests (in seconds)"""
    global OLLAMA_TIMEOUT
    OLLAMA_TIMEOUT = timeout_seconds
    logger.info(f"Ollama timeout set to: {OLLAMA_TIMEOUT} seconds")


def check_ollama_connection() -> bool:
    """Check if Ollama server is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}")
        return False


def build_prompt(text: str, prompt_type: str = "simple") -> str:
    """Build analysis prompt for the given text"""
    prompts = {
        "simple": f"""TASK: Analyze text for depression indicators. CRITICAL: Return ONLY valid JSON matching this exact structure, no other text:
{{"depression_score": <number 0-100>, "key_signals": [<list of strings>], "summary": "<string>"}}

TEXT TO ANALYZE:
{text}

INSTRUCTIONS:
- depression_score: integer 0-100 where 0=no depression indicators, 100=severe depression indicators
- key_signals: list of specific phrases/words showing depression (max 5)
- summary: 1-2 sentence analysis
- Return ONLY the JSON object, nothing else
- Do not include markdown, code blocks, or explanations

JSON RESPONSE:""",
        
        "structured": f"""TASK: Structured depression analysis. CRITICAL: Return ONLY valid JSON matching this exact structure, no other text:
{{"depression_score": <number 0-100>, "key_signals": [<list of strings>], "summary": "<string>"}}

TEXT TO ANALYZE:
{text}

Evaluate:
1. Emotional valence (positive/neutral/negative)
2. Hopelessness indicators
3. Self-worth concerns
4. Anhedonia (loss of interest)
5. Fatigue/energy level mentions

INSTRUCTIONS:
- Return depression_score (0-100) based on above criteria
- List key_signals observed
- Provide summary
- Return ONLY the JSON object, nothing else

JSON RESPONSE:""",
        
        "feature_extraction": f"""TASK: Extract depression linguistic features. CRITICAL: Return ONLY valid JSON matching this exact structure, no other text:
{{"depression_score": <number 0-100>, "key_signals": [<list of strings>], "summary": "<string>"}}

TEXT TO ANALYZE:
{text}

Categories to identify: emotions, cognitions, behaviors, physical_symptoms, social_withdrawal

INSTRUCTIONS:
- Assign depression_score based on feature presence
- List key_signals with specific examples
- Summarize findings
- Return ONLY the JSON object, nothing else

JSON RESPONSE:""",
        
        "chain_of_thought": f"""TASK: Step-by-step depression analysis. CRITICAL: Return ONLY valid JSON matching this exact structure, no other text:
{{"depression_score": <number 0-100>, "key_signals": [<list of strings>], "summary": "<string>"}}

TEXT TO ANALYZE:
{text}

Think through:
1. What emotional tone is present?
2. What statements suggest hopelessness?
3. What indicates loss of interest?
4. What's the overall depression likelihood?

INSTRUCTIONS:
- Convert your analysis into depression_score (0-100)
- Extract key_signals from the text
- Write summary from your reasoning
- Return ONLY the JSON object, nothing else

JSON RESPONSE:""",
        
        "free_form": f"""TASK: Comprehensive mental health text analysis. CRITICAL: Return ONLY valid JSON matching this exact structure, no other text:
{{"depression_score": <number 0-100>, "key_signals": [<list of strings>], "summary": "<string>"}}

TEXT TO ANALYZE:
{text}

INSTRUCTIONS:
- Thoroughly assess depression indicators
- Assign depression_score (0-100)
- Identify key_signals (specific phrases/themes)
- Provide summary of findings
- Return ONLY the JSON object, nothing else
- Do not include markdown, code blocks, or explanations

JSON RESPONSE:"""
    }
    
    return prompts.get(prompt_type, prompts["simple"])


def analyze_text_fallback(text: str) -> dict:
    """
    Fallback analysis when Ollama doesn't return structured JSON.
    Performs keyword-based analysis of text content.
    """
    logger.info("Using fallback keyword-based analysis")
    
    text_lower = text.lower()
    
    # Depression indicators
    depression_keywords = [
        'depressed', 'depression', 'hopeless', 'hopelessness', 'suicidal', 'suicide',
        'worthless', 'worthlessness', 'empty', 'emptiness', 'despair', 'despair',
        'sad', 'sadness', 'miserable', 'suffering', 'painful', 'pain',
        'lonely', 'loneliness', 'isolated', 'isolation', 'numb', 'numb',
        'fatigue', 'exhausted', 'tired', 'loss of interest', 'can\'t', 'cannot',
        'meaningless', 'pointless', 'no point', 'no reason', 'give up', 'giving up'
    ]
    
    # Count depression indicators
    depression_score = 0
    key_signals = []
    
    for keyword in depression_keywords:
        count = text_lower.count(keyword)
        if count > 0:
            depression_score += min(count * 5, 15)  # Max 15 points per keyword
            key_signals.append(keyword)
    
    # Cap at 100
    depression_score = min(depression_score, 100)
    
    # Create summary
    if depression_score >= 70:
        severity = "severe"
    elif depression_score >= 50:
        severity = "moderate"
    elif depression_score >= 30:
        severity = "mild"
    else:
        severity = "low"
    
    summary = f"Fallback analysis: Text shows {severity} depression indicators based on keyword presence."
    
    logger.info(f"Fallback analysis: score={depression_score}, signals={len(key_signals)}")
    
    return {
        "depression_score": depression_score,
        "key_signals": key_signals[:5],  # Top 5 signals
        "summary": summary,
        "analysis_type": "fallback_keyword_analysis"
    }


def analyze_text(text: str, prompt_type: str = "simple") -> dict:
    """
    Use Ollama to analyze text for depression-related signals.
    Supports multiple prompt types.
    """
    try:
        # Check connection
        if not check_ollama_connection():
            return {
                "error": "Ollama server not running",
                "solution": "Start Ollama with: ollama serve",
                "status": "connection_failed"
            }
        
        prompt = build_prompt(text, prompt_type)
        
        logger.info(f"Sending request to Ollama (model: {OLLAMA_MODEL})")
        logger.info(f"Request timeout: {OLLAMA_TIMEOUT} seconds ({OLLAMA_TIMEOUT/60:.1f} minutes)")
        logger.debug(f"Prompt: {prompt[:200]}...")  # Log first 200 chars of prompt
        
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,  # Lower temp for more consistent responses
            },
            timeout=OLLAMA_TIMEOUT  # Configurable timeout for model inference
        )
        
        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return {
                "error": f"Ollama returned status {response.status_code}",
                "details": response.text
            }
        
        result = response.json()
        response_text = result.get("response", "").strip()
        
        # Log the complete response for debugging
        logger.info(f"Raw Ollama response length: {len(response_text)} characters")
        logger.debug(f"Raw Ollama response:\n{response_text}")
        
        # Try to extract JSON from response
        try:
            # Find JSON object in response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                logger.info(f"Found JSON in response: {json_str[:100]}...")
                parsed = json.loads(json_str)
                
                # Check if this is the correct format (has depression_score, key_signals, summary)
                if "depression_score" in parsed and "key_signals" in parsed and "summary" in parsed:
                    logger.info("✓ Response matches expected format")
                    return parsed
                
                # If not, try to extract from nested structures
                logger.warning(f"Response format doesn't match. Keys: {list(parsed.keys())}")
                
                # Try to find depression analysis in nested answer/response fields
                for key in ["answer", "response", "analysis", "result"]:
                    if key in parsed and isinstance(parsed[key], dict):
                        nested = parsed[key]
                        if "depression_score" in nested and "key_signals" in nested:
                            logger.info(f"✓ Found analysis in nested '{key}' field")
                            return nested
                
                # Try to extract from context or text field and analyze
                for key in ["context", "text", "answer_text", "content"]:
                    if key in parsed:
                        value = parsed[key]
                        if isinstance(value, dict) and "text" in value:
                            text_content = value["text"]
                        elif isinstance(value, str):
                            text_content = value
                        else:
                            continue
                        
                        logger.warning(f"Could not extract structured analysis, using fallback on '{key}' content")
                        return analyze_text_fallback(text_content)
                
                # Last resort: use fallback on the response_text itself
                logger.warning("Could not parse expected structure, using fallback analysis")
                return analyze_text_fallback(response_text[:1000])
                
            else:
                # If no JSON found, return structured response
                logger.warning(f"No JSON found in response. Full response:\n{response_text}")
                return analyze_text_fallback(response_text[:1000])
                
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse Ollama JSON response: {e}")
            logger.debug(f"Failed to parse: {response_text}")
            return analyze_text_fallback(response_text[:1000])
            
    except requests.exceptions.Timeout:
        logger.error("Ollama request timeout")
        return {
            "error": "Ollama request timeout",
            "note": "Model inference took too long. Try a smaller model.",
            "suggestion": "Use 'mistral' or 'neural-chat' for faster inference"
        }
    except Exception as e:
        logger.error(f"Ollama interface error: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "error"
        }


def get_available_models() -> dict:
    """Get list of available models on Ollama server"""
    try:
        if not check_ollama_connection():
            return {"models": [], "error": "Ollama not running"}
        
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"].split(":")[0] for model in data.get("models", [])]
            return {"models": models, "success": True}
        else:
            return {"models": [], "error": f"Status {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching Ollama models: {e}")
        return {"models": [], "error": str(e)}


if __name__ == "__main__":
    # Test the interface
    test_text = "I feel empty most days and I'm exhausted trying to keep up with classes."
    
    print("Checking Ollama connection...")
    if check_ollama_connection():
        print("✓ Ollama is running!")
        print(f"Using model: {OLLAMA_MODEL}")
        print("\nAnalyzing text...")
        result = analyze_text(test_text, "simple")
        print(json.dumps(result, indent=2))
    else:
        print("✗ Ollama is not running. Start it with: ollama serve")
