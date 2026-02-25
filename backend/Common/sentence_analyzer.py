"""
Sentence-by-sentence depression analysis.
Splits text into sentences and analyzes each individually for more granular results.

Source for sentence splitting: https://stackoverflow.com/a/31505798
Posted by D Greenberg, modified by community. License - CC BY-SA 4.0
"""

import re
import json
import logging
from .groq_handler import analyze_with_groq

logger = logging.getLogger(__name__)

# Sentence splitting patterns
alphabets = "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = r"(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|edu|me)"
digits = "([0-9])"
multiple_dots = r'\.{2,}'


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences using regex-based approach.
    
    Handles common edge cases like:
    - Abbreviations (Mr., Dr., etc.)
    - Decimal numbers
    - URLs/websites
    - Acronyms
    - Multiple dots (ellipsis)
    
    :param text: Text to split into sentences
    :return: List of sentences
    """
    text = " " + text + "  "
    text = text.replace("\n", " ")
    text = re.sub(prefixes, "\\1<prd>", text)
    text = re.sub(websites, "<prd>\\1", text)
    text = re.sub(digits + "[.]" + digits, "\\1<prd>\\2", text)
    text = re.sub(multiple_dots, lambda match: "<prd>" * len(match.group(0)) + "<stop>", text)
    if "Ph.D" in text:
        text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub(r"\s" + alphabets + "[.] ", " \\1<prd> ", text)
    text = re.sub(acronyms + " " + starters, "\\1<stop> \\2", text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>\\3<prd>", text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>", text)
    text = re.sub(" " + suffixes + "[.] " + starters, " \\1<stop> \\2", text)
    text = re.sub(" " + suffixes + "[.]", " \\1<prd>", text)
    text = re.sub(" " + alphabets + "[.]", " \\1<prd>", text)
    if '"' in text:
        text = text.replace("."", "".")
    if "\"" in text:
        text = text.replace(".\"", "\".")
    if "!" in text:
        text = text.replace("!\"", "\"!")
    if "?" in text:
        text = text.replace("?\"", "\"?")
    text = text.replace(".", ".<stop>")
    text = text.replace("?", "?<stop>")
    text = text.replace("!", "!<stop>")
    text = text.replace("<prd>", ".")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]:
        sentences = sentences[:-1]
    return [s for s in sentences if s]


def analyze_sentences(text: str, model: str, prompt_type: str = "sentence") -> dict:
    """
    Split text into sentences and analyze each for depression indicators.
    
    Args:
        text: Full text to analyze
        model: Groq model identifier
        prompt_type: Prompt type to use (default: "sentence")
    
    Returns:
        Dictionary with per-sentence results and aggregated statistics
    """
    sentences = split_into_sentences(text)
    logger.info(f"Split text into {len(sentences)} sentences")
    
    sentence_results = []
    depressed_count = 0
    not_depressed_count = 0
    confidence_sum = 0.0
    
    for idx, sentence in enumerate(sentences):
        if not sentence:
            continue
            
        logger.debug(f"Analyzing sentence {idx + 1}/{len(sentences)}")
        
        try:
            analysis = analyze_with_groq(sentence, model, prompt_type)
            result = analysis.get("analysis", {})
            
            # Extract classification
            pred_class = result.get("class", "unknown")
            confidence = result.get("confidence", 0.0)
            
            if pred_class == "depression":
                depressed_count += 1
            elif pred_class == "no-depression":
                not_depressed_count += 1
            
            confidence_sum += confidence
            
            sentence_results.append({
                "sentence_number": idx + 1,
                "sentence": sentence,
                "class": pred_class,
                "confidence": confidence
            })
            
        except Exception as e:
            logger.error(f"Error analyzing sentence {idx + 1}: {e}")
            sentence_results.append({
                "sentence_number": idx + 1,
                "sentence": sentence,
                "class": "error",
                "confidence": 0.0,
                "error": str(e)
            })
    
    # Calculate aggregate statistics
    total_analyzed = depressed_count + not_depressed_count
    avg_confidence = confidence_sum / total_analyzed if total_analyzed > 0 else 0.0
    depression_ratio = depressed_count / total_analyzed if total_analyzed > 0 else 0.0
    
    # Determine overall classification based on ratio
    if depression_ratio >= 0.25:
        overall_class = "depression"
    else:
        overall_class = "no-depression"
    
    return {
        "analysis": {
            "text_id": "sentence_analysis",
            "model": "sentence-by-sentence",
            "prediction": {
                "class": overall_class,
                "confidence": avg_confidence,
                "probability_depression": depression_ratio,
                "probability_no_depression": 1 - depression_ratio
            },
            "sentence_analysis": {
                "total_sentences": len(sentences),
                "depressed_sentences": depressed_count,
                "not_depressed_sentences": not_depressed_count,
                "depression_ratio": depression_ratio,
                "avg_confidence": avg_confidence
            },
            "sentences": sentence_results
        },
        "prompt_type": prompt_type
    }
