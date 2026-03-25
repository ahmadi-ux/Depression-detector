# Grok Interface for Depression Signal Extraction utilizing x.ai's Grok API
# Unless you bought tokens this is unusable, but just leaving the code here
import requests
import json
import os
import logging
from dotenv import load_dotenv
from ..Common.prompts import get_prompt

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Always load .env from backend/Common/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'Common', '.env'))

# Get API key from environment variable
GROK_API_KEY = os.environ.get("GROK_API_KEY")
if not GROK_API_KEY:
    raise ValueError("GROK_API_KEY environment variable is not set")

# Grok API Configuration
GROK_API_URL = "https://api.x.ai/v1/chat/completions"
MODEL_NAME = "grok-4-1-fast"

SIGNAL_THRESHOLDS = {
    "sadness": 0.6,
    "anhedonia": 0.6,
    "fatigue": 0.5,
    "hopelessness": 0.6,
    "isolation": 0.5
}

MIN_SIGNALS_FOR_DEPRESSED = 2


def extract_signals(text: str, prompt_type: str = "simple") -> dict:
    """
    Use Grok to analyze text for depression signals
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"GROK ANALYZE_TEXT - Prompt Type: {prompt_type}")
    logger.info(f"{'='*80}")
    logger.info(f"Text length: {len(text)} characters")
    
    prompt = get_prompt(prompt_type, text)
    logger.debug(f"Prompt (first 200 chars): {prompt[:200]}...")
    
    raw = ""  # Initialize for error reporting
    try:
        # Prepare request to Grok API
        logger.info("Sending request to Grok API...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROK_API_KEY}"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a mental health assessment assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": MODEL_NAME,
            "stream": False,
            "temperature": 0.0
        }
        
        response = requests.post(
            GROK_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # Check if request was successful
        if response.status_code != 200:
            error_msg = f"Grok API returned status code {response.status_code}: {response.text}"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        response_data = response.json()
        logger.info(f"Grok API response received successfully")
        
        # Extract the response content
        if 'choices' not in response_data or not response_data['choices']:
            error_msg = "Grok API response missing 'choices'"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        raw = response_data['choices'][0]['message']['content']
        logger.debug(f"Raw response (first 300 chars): {raw[:300]}...")
        
        # Parse JSON from response
        try:
            # Try to find JSON in the response (in case there's extra text)
            start_idx = raw.find('{')
            end_idx = raw.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = raw[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                raise ValueError("No JSON object found in response")
                
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON from Grok response: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.debug(f"Raw response: {raw}")
            raise RuntimeError(error_msg)
        
        logger.info(f"✓ Successfully parsed response from Grok")
        return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request to Grok API failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error in Grok analysis: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.debug(f"Raw response: {raw}")
        raise RuntimeError(error_msg)


def analyze_text(text: str, prompt_type: str = "simple") -> dict:
    """
    Full pipeline: Extract signals via Grok and return result.
    """
    return extract_signals(text, prompt_type)


if __name__ == "__main__":
    test_text = "I feel empty most days and I'm exhausted trying to keep up with classes."
    result = analyze_text(test_text, "simple")
    print(json.dumps(result, indent=2))
