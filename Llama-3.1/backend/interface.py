import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

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
You are a research assistant.

Extract depression-related linguistic signals from the text.
Do NOT classify.
Do NOT explain.
Do NOT diagnose.

Return JSON ONLY in this exact format:
{{
  "signals": {{
    "sadness": 0.0,
    "anhedonia": 0.0,
    "fatigue": 0.0,
    "hopelessness": 0.0,
    "isolation": 0.0
  }}
}}

Text:
{text}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        },
        timeout=600
    )

    raw = response.json()["response"]

    try:
        return json.loads(raw)["signals"]
    except Exception as e:
        raise RuntimeError(f"Failed to parse model output:\n{raw}") from e


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
    signals = extract_signals(text)
    return classify_from_signals(signals)


if __name__ == "__main__":
    text = "I feel empty most days and I’m exhausted trying to keep up with classes."
    result = analyze_text(text)
    print(json.dumps(result, indent=2))
