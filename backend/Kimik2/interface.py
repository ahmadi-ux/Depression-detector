import json
import os
from dotenv import load_dotenv
from groq import Groq
from pathlib import Path

from ..Common.Utils import classify_from_signals  # shared logic

load_dotenv()

prompt_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Common",
    "prompt.txt"
)
with open(prompt_path, 'r', encoding='utf-8') as f:
    prompt_template = f.read()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
if not client.api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

GROQ_MODEL = "moonshotai/kimi-k2-instruct-0905"

def extract_signals(text: str) -> dict:
    """
    Use Kimi-k2 (Groq) to analyze text for depression-related linguistic signals.
    Returns raw signal scores + explanations (no classification here).
    """

    prompt = prompt_template.format(text=text)

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
