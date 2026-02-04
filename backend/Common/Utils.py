# common/utils.py
# Shared across all interfaces: constants, classification logic

SIGNAL_THRESHOLDS = {
    "sadness": 0.6,
    "anhedonia": 0.6,
    "fatigue": 0.5,
    "hopelessness": 0.6,
    "isolation": 0.5
}

MIN_SIGNALS_FOR_DEPRESSED = 2

def classify_from_signals(signals: dict) -> dict:
    """
    Classify based on detected signals (shared logic)
    """
    triggered = {
        k: v for k, v in signals.items()
        if v >= SIGNAL_THRESHOLDS.get(k, 0.5)  # Default threshold if missing
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

def default_recommendations():
    """
    Shared default recommendations
    """
    return [
        "This is not a clinical diagnosis.",
        "Please consult a qualified mental health professional.",
        "Consider speaking with a counselor or trusted support person."
    ]