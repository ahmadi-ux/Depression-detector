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

load_dotenv() 

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
        
        # Get the response text
        raw = response.text.strip()
        logger.info(f"Raw response length: {len(raw)} characters")
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
        logger.error(f"Error: {str(e)}")
        logger.error(f"Raw response: {raw}")
        raise RuntimeError(f"Failed to parse Gemini output as JSON: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Error calling Gemini API: {str(e)}")
        raise


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