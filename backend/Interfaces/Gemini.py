# Gemini Interface for Depression Signal Extraction utilizing Gemini's Api

from google import genai
from google.genai import types
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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
    
# Configure Gemini with new SDK
client = genai.Client(api_key=GEMINI_API_KEY)

# Choose your model
MODEL_NAME = "gemini-flash-latest"

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
    Use Gemini to analyze text for depression signals
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"GEMINI ANALYZE_TEXT - Prompt Type: {prompt_type}")
    logger.info(f"{'='*80}")
    logger.info(f"Text length: {len(text)} characters")
    
    prompt = get_prompt(prompt_type, text)
    logger.debug(f"Prompt (first 200 chars): {prompt[:200]}...")
    
    raw = ""  # Initialize for error reporting
    try:
        # Generate content with new SDK
        logger.info("Sending request to Gemini API...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                top_p=1,
                top_k=1,
                max_output_tokens=2048,
            )
        )
        
        # Validate response object exists
        if response is None:
            error_msg = "Gemini API returned None response - check API key and quota"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        # Check if response was blocked due to safety filters or other issues
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                finish_reason = str(candidate.finish_reason)
                logger.info(f"Finish reason: {finish_reason}")
                if 'BLOCKED' in finish_reason or 'ERROR' in finish_reason:
                    error_msg = f"Gemini response blocked: {finish_reason} - content may have triggered safety filters"
                    logger.error(f"❌ {error_msg}")
                    raise RuntimeError(error_msg)
        
        # Try to extract text from response
        try:
            raw = response.text if hasattr(response, 'text') else ""
            if raw:
                raw = raw.strip()
        except Exception as e:
            logger.warning(f"Could not access response.text: {e}")
            raw = ""
        
        logger.info(f"Raw response length: {len(raw)} characters")
        
        # Check if response is empty
        if not raw:
            error_msg = "Gemini returned empty response - likely due to API quota, content filtering, or API issues"
            logger.error(f"❌ {error_msg}")
            logger.error(f"Response object type: {type(response)}")
            if hasattr(response, 'candidates'):
                logger.error(f"Has candidates: {bool(response.candidates)}")
                if response.candidates:
                    logger.error(f"First candidate: {response.candidates[0]}")
            raise RuntimeError(error_msg)
        
        logger.debug(f"Raw response (first 300 chars):\n{raw[:300]}")
        
        # Clean up markdown code blocks if present
        if raw.startswith("```json"):
            raw = raw[7:]  # Remove ```json
            logger.info("Removed ```json prefix")
        if raw.startswith("```"):
            raw = raw[3:]  # Remove ```
            logger.info("Removed ``` prefix")
        if raw.endswith("```"):
            raw = raw[:-3]  # Remove trailing ```
            logger.info("Removed ``` suffix")
        raw = raw.strip()
        
        # Check again after cleaning
        if not raw:
            error_msg = "Response became empty after cleaning markdown blocks - Gemini may not have returned valid JSON"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        logger.debug(f"Cleaned response (first 300 chars):\n{raw[:300]}")
        
        # Parse JSON
        data = json.loads(raw)
        logger.info(f"✓ Successfully parsed JSON")
        logger.info(f"JSON keys: {list(data.keys())}")
        logger.debug(f"Full parsed data:\n{json.dumps(data, indent=2, default=str)}")
        
        return {
            "response": data,
            "prompt_type": prompt_type
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON from Gemini response:")
        logger.error(f"JSONDecodeError: {str(e)}")
        logger.error(f"Raw response: '{raw}'")
        logger.error(f"Response length: {len(raw)}")
        if len(raw) > 0:
            logger.error(f"First 500 chars: {raw[:500]}")
        raise RuntimeError(f"Gemini response is not valid JSON: {str(e)}")
    except RuntimeError:
        # Re-raise RuntimeError as-is
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error calling Gemini API: {type(e).__name__}: {str(e)}")
        raise RuntimeError(f"Error communicating with Gemini API: {str(e)}")


def test_gemini_connection(test_text: str = "Hello") -> dict:
    """
    Diagnostic function to test Gemini API connection.
    Returns connection status and helpful error messages.
    """
    logger.info("Testing Gemini API connection...")
    
    try:
        # Test with a simple prompt
        test_prompt = f"Respond with valid JSON with a 'status' key. Text to analyze: {test_text}"
        
        logger.info(f"Sending test request to {MODEL_NAME}...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=test_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                top_p=1,
                top_k=1,
                max_output_tokens=256,
            )
        )
        
        # Check response object
        status = {
            "connected": True,
            "model": MODEL_NAME,
            "response_received": response is not None,
            "has_text": hasattr(response, 'text') if response else False,
        }
        
        if response and hasattr(response, 'text'):
            text = response.text.strip() if response.text else ""
            status["response_length"] = len(text)
            status["response_empty"] = len(text) == 0
            
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = response.candidates[0].finish_reason if hasattr(response.candidates[0], 'finish_reason') else "unknown"
                status["finish_reason"] = str(finish_reason)
            
            if len(text) > 0:
                status["response_sample"] = text[:100]
                status["status"] = "✓ Connection OK - API is responsive"
            else:
                status["status"] = "⚠ Connection OK but empty response - check quota/filters"
        else:
            status["status"] = "❌ No response object - API key or network issue"
        
        logger.info(f"Test result: {status}")
        return status
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {type(e).__name__}: {str(e)}")
        return {
            "connected": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "status": f"❌ Connection failed: {str(e)}"
        }


def classify_from_signals(signals: dict) -> dict:
    """
    Classify based on detected signals
    """
    triggered = {
        k: v for k, v in signals.items()
        if v >= SIGNAL_THRESHOLDS[k]
    }

    label = (
        "DEPRESSED"
        if len(triggered) >= MIN_SIGNALS_FOR_DEPRESSED
        else "NOT_DEPRESSED"
    )

    confidence = round(
        sum(triggered.values()) / max(len(SIGNAL_THRESHOLDS), 1),
        2
    )

    return {
        "label": label,
        "confidence": confidence,
        "signals": triggered
    }


def analyze_text(text: str, prompt_type: str = "simple") -> dict:
    """
    Main analysis function - extracts signals and classifies
    Supports multiple prompt types
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"ANALYZE_TEXT called with prompt_type: {prompt_type}")
    logger.info(f"{'='*80}")
    
    result = extract_signals(text, prompt_type)
    
    logger.info(f"Returning analysis result")
    logger.info(f"Result keys: {list(result.keys())}")
    
    return {
        "analysis": result["response"],
        "prompt_type": result["prompt_type"]
    }

if __name__ == "__main__":
    # Test the function
    test_text = "I feel empty most days and I'm exhausted trying to keep up with classes."
    print("Testing Gemini API with new google-genai SDK...")
    print(f"Input: {test_text}\n")
    
    result = analyze_text(test_text, "simple")
    print("Result:")
    print(json.dumps(result, indent=2))