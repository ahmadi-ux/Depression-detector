import requests
import json
import re

SIGNAL_THRESHOLDS = {
    "sadness": 0.6,
    "anhedonia": 0.6,
    "fatigue": 0.5,
    "hopelessness": 0.6,
    "isolation": 0.5
}

MIN_SIGNALS_FOR_DEPRESSED = 2


def extract_signals(text: str) -> dict:
    prompt = f"""
    You are a clinical-language research assistant.

    Your task is to analyze the text and estimate the presence of specific
    depression-related linguistic signals.

    RULES:
    - Do NOT diagnose.
    - Do NOT classify.
    - Do NOT give advice.
    - Do NOT include text outside the JSON object.
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

    OUTPUT FORMAT (JSON ONLY):

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
    """

    response = requests.post(
    OLLAMA_URL,
    json={
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False,

        # Hard stateless guarantees
        "temperature": 0.0,
        "context": [],
        "keep_alive": 0,
        "stop": [
            "\n\nHere",
            "Here's",
            "Reasoning",
            "Explanation:"
        ]
    },
    timeout=600
)


    raw = response.json()["response"]

    try:
        # Try to parse the entire response as JSON first
        data = json.loads(raw)
        return {
            "signals": data["signals"],
            "explanations": data.get("explanations", {})
        }
    except json.JSONDecodeError:
        # If that fails, try to extract JSON using regex
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            data = json.loads(json_match.group(0))
            return {
                "signals": data["signals"],
                "explanations": data.get("explanations", {})
            }
        else:
            raise RuntimeError(f"Failed to parse model output:\n{raw}")


def classify_from_signals(signals: dict) -> dict:
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
    result = extract_signals(text)
    signals = result["signals"]
    explanations = result["explanations"]
    
    classification = classify_from_signals(signals)
    classification["explanations"] = explanations
    
    return classification

if __name__ == "__main__":
    text = "I feel empty most days and I’m exhausted trying to keep up with classes."
    result = analyze_text(text)
    print(json.dumps(result, indent=2))