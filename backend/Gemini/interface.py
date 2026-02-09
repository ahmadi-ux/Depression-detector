from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv() 

prompt_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Common",
    "prompt.txt"
)
with open(prompt_path, 'r', encoding='utf-8') as f:
    prompt_template = f.read()

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


def extract_signals(text: str) -> dict:
    """
    Use Gemini to analyze text for depression signals
    """
    prompt = prompt_template.format(text=text)
    
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