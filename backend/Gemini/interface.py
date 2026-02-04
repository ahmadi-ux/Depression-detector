from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from google import genai
from google.genai import types
import json
import os

# ============================================================================
# GEMINI API CONFIGURATION
# ============================================================================

# Get API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA-jkCnWGGzJBuiQvfGWnaYv4f0LmrC7Rc")

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


def extract_signals(text: str) -> dict:
    """
    Use Gemini to analyze text for depression signals
    """
    prompt = f"""
You are a clinical-language research assistant.

Your task is to analyze the text and estimate the presence of specific
depression-related linguistic signals.

RULES:
- Do NOT diagnose.
- Do NOT classify.
- Do NOT give advice.
- Respond ONLY with a valid JSON object. No other text.
- Explanations must be short, neutral, and evidence-based.
- If no evidence exists, use an empty string "".

SIGNAL DEFINITIONS:

sadness:
Persistent low mood, emptiness, despair, or emotional pain.

anhedonia:
Loss of interest, enjoyment, motivation, or emotional engagement.

fatigue:
Mental or physical exhaustion, burnout, reduced capacity to sustain effort.

hopelessness:
Pessimism, helplessness, lack of future orientation.

isolation:
Social withdrawal, loneliness, or emotional distancing.

SCORING GUIDELINES:
- 0.0 = no evidence
- 0.3 = weak or isolated hints
- 0.6 = clear and repeated signals
- 0.9 = strong and persistent signals

OUTPUT FORMAT (JSON ONLY, NO OTHER TEXT):

{{
    "signals": {{
        "sadness": 0.0,
        "anhedonia": 0.0,
        "fatigue": 0.0,
        "hopelessness": 0.0,
        "isolation": 0.0
    }},
    "explanations": {{
        "sadness": "",
        "anhedonia": "",
        "fatigue": "",
        "hopelessness": "",
        "isolation": ""
    }}
}}

TEXT TO ANALYZE:
{text}

Remember: Respond with ONLY the JSON object above. No markdown, no code blocks, no explanations outside the JSON."""

    try:
        # Generate content with new SDK
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
        
        # Clean up markdown code blocks if present
        if raw.startswith("```json"):
            raw = raw[7:]  # Remove ```json
        if raw.startswith("```"):
            raw = raw[3:]  # Remove ```
        if raw.endswith("```"):
            raw = raw[:-3]  # Remove trailing ```
        raw = raw.strip()
        
        # Parse JSON
        data = json.loads(raw)
        
        return {
            "signals": data["signals"],
            "explanations": data.get("explanations", {})
        }
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from Gemini response:")
        print(f"Raw response: {raw}")
        raise RuntimeError(f"Failed to parse Gemini output as JSON: {str(e)}")
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
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


def analyze_text(text: str) -> dict:
    """
    Main analysis function - extracts signals and classifies
    """
    result = extract_signals(text)
    all_signals = result["signals"]
    explanations = result["explanations"]
    
    classification = classify_from_signals(all_signals)
    
    # Add all signal scores and explanations to the result
    classification["all_signals"] = all_signals
    classification["explanations"] = explanations
    
    return classification

if __name__ == "__main__":
    # Test the function
    test_text = "I feel empty most days and I'm exhausted trying to keep up with classes."
    print("Testing Gemini API with new google-genai SDK...")
    print(f"Input: {test_text}\n")
    
    result = analyze_text(test_text)
    print("Result:")
    print(json.dumps(result, indent=2))