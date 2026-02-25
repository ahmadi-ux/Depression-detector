import json
from ..Common.groq_handler import analyze_with_groq

GROQ_MODEL = "llama-3.1-8b-instant"


def extract_signals(text: str, prompt_type: str = "simple") -> dict:
    """
    Use LLaMA (Groq) to analyze text for depression-related linguistic signals.
    Supports multiple prompt types.
    """
    return analyze_with_groq(text, GROQ_MODEL, prompt_type)


def analyze_text(text: str, prompt_type: str = "simple") -> dict:
    """
    Full pipeline: Extract signals via LLaMA and return result.
    """
    # Post-process: Truncate at first closing brace after an opening brace
    result = extract_signals(text, prompt_type)
    # If the result is a string (raw), try to truncate at first valid JSON
    if isinstance(result, str):
        import re
        match = re.search(r'\{.*?\}', result, re.DOTALL)
        if match:
            result = match.group(0)
    return result


if __name__ == "__main__":
    test_text = "I feel empty most days and I'm exhausted trying to keep up with classes."
    result = analyze_text(test_text, "simple")
    print(json.dumps(result, indent=2))
