import json
from ..Common.groq_handler import analyze_with_groq

GROQ_MODEL = "groq/compound"

def extract_signals(text: str, prompt_type: str = "simple") -> dict:
    """
    Use Compound (Groq) to analyze text for depression-related linguistic signals.
    Supports multiple prompt types.
    """
    return analyze_with_groq(text, GROQ_MODEL, prompt_type)


def analyze_text(text: str, prompt_type: str = "simple") -> dict:
    """
    Full pipeline: Extract signals via Compound and return result.
    """
    return extract_signals(text, prompt_type)


if __name__ == "__main__":
    test_text = "I feel empty most days and I'm exhausted trying to keep up with classes."
    result = analyze_text(test_text, "simple")
    print(json.dumps(result, indent=2))
