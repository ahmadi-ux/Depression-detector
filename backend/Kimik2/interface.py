import json
import os
from dotenv import load_dotenv
from groq import Groq

from ..Common.Utils import classify_from_signals  # shared logic

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
if not client.api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

GROQ_MODEL = "moonshotai/kimi-k2-instruct-0905"

def extract_signals(text: str) -> dict:
    """
    Use Kimi-k2 (Groq) to analyze text for depression-related linguistic signals.
    Returns raw signal scores + explanations (no classification here).
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

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2048,
    )

    raw = response.choices[0].message.content.strip()

    # Defensive cleanup (Kimi sometimes wraps JSON)
    if raw.startswith("```"):
        raw = raw.split("```")[1]

    data = json.loads(raw)

    return {
        "signals": data["signals"],
        "explanations": data.get("explanations", {})
    }


def analyze_text(text: str) -> dict:
    """
    Full pipeline:
    1. Extract signals via Kimi-k2 (Groq)
    2. Classify using shared rules
    3. Return merged result
    """

    extracted = extract_signals(text)
    signals = extracted["signals"]
    explanations = extracted["explanations"]

    classification = classify_from_signals(signals)

    classification["all_signals"] = signals
    classification["explanations"] = explanations

    return classification


if __name__ == "__main__":
    test_text = "I feel empty most days and I'm exhausted trying to keep up with classes."
    result = analyze_text(test_text)
    print(json.dumps(result, indent=2))
