"""
Unified LLM engine handler supporting all available models.
Dynamically routes to the appropriate backend based on LLM selection.
"""

import io
import json
import logging
import traceback
from werkzeug.datastructures import FileStorage
from backend.Common.engineUtils import extract_text_from_file, generate_combined_pdf_report
from backend.Common.sentence_analyzer import analyze_sentences

logger = logging.getLogger(__name__)

# Mapping of LLM names to their interface modules
LLM_INTERFACES = {
    "llama": "backend.Interfaces.Llama",
    "gemini": "backend.Interfaces.Gemini",
    "chatgpt": "backend.Interfaces.ChatGPT",
    "kimi": "backend.Interfaces.Kimi2",
    "qwen": "backend.Interfaces.Qwen",
    "compound": "backend.Interfaces.Compound",
    "llamabig": "backend.Interfaces.LlamaBig",
    "grok": "backend.Interfaces.Grok"
}

# Display names for PDF reports
LLM_DISPLAY_NAMES = {
    "llama": "Llama",
    "gemini": "Gemini",
    "chatgpt": "ChatGPT",
    "kimi": "Kimi2",
    "qwen": "Qwen",
    "compound": "Compound",
    "llamabig": "LlamaBig",
    "grok": "Grok"
}


def get_llm_interface(llm_type: str):
    """
    Dynamically import and return the analyze_text function for the specified LLM.
    
    Args:
        llm_type: One of 'llama', 'gemini', 'chatgpt', 'kimi', 'qwen', 'compound', 'llamabig', 'grok'
        
    Returns:
        The analyze_text function from the LLM's interface module
        
    Raises:
        ValueError: If llm_type is not recognized
    """
    llm_type = llm_type.lower()
    
    if llm_type not in LLM_INTERFACES:
        raise ValueError(f"Unknown LLM type: {llm_type}. Available: {list(LLM_INTERFACES.keys())}")
    
    module_path = LLM_INTERFACES[llm_type]
    
    try:
        # Dynamically import the module
        module = __import__(module_path, fromlist=['analyze_text'])
        return module.analyze_text
    except ImportError as e:
        raise ValueError(f"Failed to load interface for {llm_type}: {e}")


def run_llm_job(llm_type: str, file_payloads, prompt_type: str = "simple"):
    """
    Universal job runner for any supported LLM.
    
    Args:
        llm_type: The LLM to use ('llama', 'gemini', 'chatgpt', 'kimi', 'qwen', 'compound', 'llamabig', 'grok')
        file_payloads: List of file payload dictionaries with 'bytes' and 'filename'
        prompt_type: The prompt template type to use (default: 'simple')
        
    Returns:
        Tuple of (pdf_bytes, depression_classification) where classification is 'depressed' or 'not-depressed'
    """
    llm_type = llm_type.lower()
    logger.info(f"Running job with LLM: {llm_type}, Prompt: {prompt_type}")
    
    combined_results = []
    depression_levels = []  # Track all depression levels
    
    for payload in file_payloads:
        logger.debug(f"Processing file: {payload['filename']}")
        
        # Extract text from file
        file = FileStorage(
            stream=io.BytesIO(payload["bytes"]), 
            filename=payload["filename"]
        )
        extracted_text = extract_text_from_file(file)
        
        # Use sentence-by-sentence analysis if prompt_type is "sentence"
        if prompt_type == "sentence":
            # Get the model from the LLM interface
            model_map = {
                "llama": "llama-3.1-8b-instant",
                "gemini": "gemma2-9b-it",
                "chatgpt": "openai/gpt-oss-120b",
                "kimi": "moonshotai/kimi-k2-instruct-0905",
                "qwen": "qwen-qwq-32b",
                "compound": "compound-beta",
                "llamabig": "llama-3.3-70b-versatile",
                "grok": "grok-1"
            }
            model = model_map.get(llm_type, "llama-3.1-8b-instant")
            llm_output = analyze_sentences(extracted_text, model, prompt_type)
        else:
            # Get the interface function for this LLM
            analyze_text = get_llm_interface(llm_type)
            logger.info(f"\n{'='*80}")
            logger.info(f"CALLING LLM INTERFACE: {llm_type}")
            logger.info(f"{'='*80}")
            llm_output = analyze_text(extracted_text, prompt_type)
            
            # Log the raw LLM output structure immediately
            logger.info(f"\n{'='*80}")
            logger.info(f"RAW LLM OUTPUT FROM {llm_type.upper()}")
            logger.info(f"{'='*80}")
            logger.info(f"Output type: {type(llm_output)}")
            logger.info(f"Output keys: {list(llm_output.keys()) if isinstance(llm_output, dict) else 'N/A'}")
            logger.info(f"\nFull output:\n{json.dumps(llm_output, indent=2, default=str)}")
            logger.info(f"{'='*80}\n")
        
        # Extract depression classification from llm_output
        depression_class = extract_depression_classification(llm_output)
        depression_levels.append(depression_class)
        logger.info(f"Extracted classification: {depression_class}")
        
        combined_results.append({
            "filename": payload["filename"],
            "text": extracted_text,
            "analysis": llm_output
        })
    
    # Determine overall depression classification
    # If any result is 'depressed' or 'high'/'medium', classify as depressed
    overall_classification = determine_overall_classification(depression_levels)
    
    # Get display name for PDF title
    display_name = LLM_DISPLAY_NAMES.get(llm_type, llm_type.capitalize())
    
    # Generate PDF report
    pdf = generate_combined_pdf_report(combined_results, title_suffix=display_name)
    
    logger.info(f"Job completed successfully for {llm_type}. Classification: {overall_classification}")
    return pdf.getvalue(), overall_classification


def extract_depression_classification(llm_output: dict) -> str:
    """
    Extract depression classification from LLM output.
    Returns 'depressed', 'not-depressed', or 'unknown'
    
    WHY UNKNOWN? This function checks multiple response structures.
    Enable debug logging below to see which structure your LLM returns.
    """
    try:
        logger.info(f"\n{'='*80}")
        logger.info("EXTRACTING DEPRESSION CLASSIFICATION")
        logger.info(f"{'='*80}")
        
        # Log the entire output structure first
        logger.info(f"LLM Output type: {type(llm_output)}")
        logger.info(f"LLM Output keys: {list(llm_output.keys()) if isinstance(llm_output, dict) else 'N/A'}")
        logger.debug(f"Full LLM Output:\n{json.dumps(llm_output, indent=2, default=str)}")
        
        analysis = llm_output.get("analysis", {})
        logger.info(f"\nAnalysis extracted: {type(analysis)}")
        logger.info(f"Analysis is dict: {isinstance(analysis, dict)}")
        if isinstance(analysis, dict):
            logger.info(f"Analysis keys: {list(analysis.keys())}")
        logger.debug(f"Analysis content:\n{json.dumps(analysis, indent=2, default=str)}")
        
        # Check various possible structures based on prompt type
        if isinstance(analysis, dict):
            # ============ CHECK 1: depression_likelihood (structured prompt) ============
            if 'depression_likelihood' in analysis:
                level = str(analysis.get('depression_likelihood', '')).lower()
                logger.info(f"\n✓ FOUND: 'depression_likelihood' = '{level}'")
                if level in ['high', 'medium']:
                    logger.info(f"  MATCH: Level '{level}' → DEPRESSED")
                    return 'depressed'
                elif level == 'low':
                    logger.info(f"  MATCH: Level '{level}' → NOT_DEPRESSED")
                    return 'not-depressed'
                else:
                    logger.warning(f"  NO_MATCH: Level '{level}' not in expected values [high, medium, low]")
            else:
                logger.debug("  ✗ NOT_FOUND: 'depression_likelihood' key missing")
            
            # ============ CHECK 2: class field (simple/feature_extraction prompts) ============
            if 'class' in analysis:
                cls = str(analysis.get('class', '')).lower().strip()
                logger.info(f"\n✓ FOUND: 'class' = '{cls}'")
                
                # Exact matches for NOT depressed
                not_depressed_patterns = ['not-depressed', 'no-depression', 'not depressed', 'no depression', 'none', 'no', 'healthy', 'normal']
                if cls in not_depressed_patterns:
                    logger.info(f"  MATCH: Class '{cls}' matches NOT_DEPRESSED patterns → NOT_DEPRESSED")
                    return 'not-depressed'
                
                # Exact matches for depressed
                depressed_patterns = ['depressed', 'depression', 'yes', 'positive']
                if cls in depressed_patterns:
                    logger.info(f"  MATCH: Class '{cls}' matches DEPRESSED patterns → DEPRESSED")
                    return 'depressed'
                
                # Fallback to substring matching for other variations
                if 'not' in cls or 'no-' in cls or cls.startswith('no '):
                    logger.info(f"  PARTIAL_MATCH: Class '{cls}' contains 'not'/'no' → NOT_DEPRESSED")
                    return 'not-depressed'
                elif 'depress' in cls:
                    logger.info(f"  PARTIAL_MATCH: Class '{cls}' contains 'depress' → DEPRESSED")
                    return 'depressed'
                else:
                    logger.warning(f"  NO_MATCH: Class '{cls}' does not match any pattern")
            else:
                logger.debug("  ✗ NOT_FOUND: 'class' key missing")
            
            # ============ CHECK 3: prediction.class nested field ============
            if 'prediction' in analysis:
                pred = analysis.get('prediction', {})
                logger.info(f"\n✓ FOUND: 'prediction' field (type: {type(pred)})")
                if isinstance(pred, dict):
                    logger.info(f"  Prediction keys: {list(pred.keys())}")
                    cls = str(pred.get('class', '')).lower().strip()
                    logger.info(f"  prediction['class'] = '{cls}'")
                    
                    if cls in ['not-depressed', 'no-depression', 'not depressed', 'no depression']:
                        logger.info(f"  MATCH: Class '{cls}' → NOT_DEPRESSED")
                        return 'not-depressed'
                    elif cls in ['depressed', 'depression']:
                        logger.info(f"  MATCH: Class '{cls}' → DEPRESSED")
                        return 'depressed'
                    elif 'not' in cls or 'no' in cls:
                        logger.info(f"  PARTIAL_MATCH: Class '{cls}' contains 'not'/'no' → NOT_DEPRESSED")
                        return 'not-depressed'
                    elif 'depress' in cls:
                        logger.info(f"  PARTIAL_MATCH: Class '{cls}' contains 'depress' → DEPRESSED")
                        return 'depressed'
                    else:
                        logger.warning(f"  NO_MATCH: Prediction class '{cls}' not recognized")
                else:
                    logger.warning(f"  ERROR: prediction is not a dict, skipping")
            else:
                logger.debug("  ✗ NOT_FOUND: 'prediction' key missing")
            
            # ============ CHECK 4: assessment field (some responses use this) ============
            if 'assessment' in analysis:
                assess = str(analysis.get('assessment', '')).lower()
                logger.info(f"\n✓ FOUND: 'assessment' = '{assess}'")
                if assess in ['high', 'medium']:
                    logger.info(f"  MATCH: Assessment '{assess}' → DEPRESSED")
                    return 'depressed'
                elif assess == 'low':
                    logger.info(f"  MATCH: Assessment '{assess}' → NOT_DEPRESSED")
                    return 'not-depressed'
                else:
                    logger.warning(f"  NO_MATCH: Assessment '{assess}' not in [high, medium, low]")
            else:
                logger.debug("  ✗ NOT_FOUND: 'assessment' key missing")
            
            # ============ CHECK 5: probability_depression (scores) ============
            if 'probability_depression' in analysis:
                prob = analysis.get('probability_depression')
                logger.info(f"\n✓ FOUND: 'probability_depression' = {prob}")
                try:
                    prob_float = float(prob)
                    threshold = 0.5
                    if prob_float >= threshold:
                        logger.info(f"  MATCH: Probability {prob_float} >= {threshold} → DEPRESSED")
                        return 'depressed'
                    else:
                        logger.info(f"  MATCH: Probability {prob_float} < {threshold} → NOT_DEPRESSED")
                        return 'not-depressed'
                except (ValueError, TypeError) as e:
                    logger.warning(f"  ERROR: Could not convert probability to float: {e}")
            else:
                logger.debug("  ✗ NOT_FOUND: 'probability_depression' key missing")
        else:
            logger.error(f"ERROR: Analysis is not a dict (type={type(analysis)}), cannot extract classification")
        
        # If we get here, none of the patterns matched
        logger.warning(f"\n{'='*80}")
        logger.warning(f"❌ UNABLE TO EXTRACT CLASSIFICATION - RETURNED 'unknown'")
        logger.warning(f"Analysis structure did not match any expected pattern")
        logger.warning(f"Available analysis keys: {list(analysis.keys()) if isinstance(analysis, dict) else type(analysis)}")
        logger.warning(f"{'='*80}\n")
        
        return 'unknown'
        
    except Exception as e:
        logger.error(f"\n{'='*80}")
        logger.error(f"❌ EXCEPTION while extracting classification:")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        logger.error(f"{'='*80}\n")
        return 'unknown'


def determine_overall_classification(classifications: list) -> str:
    """
    Determine overall classification from multiple file results.
    If any file is 'depressed', overall is 'depressed'
    """
    if not classifications:
        return 'unknown'
    
    # If any result is depressed, overall is depressed
    if 'depressed' in classifications:
        return 'depressed'
    
    # If all are not-depressed, overall is not-depressed
    if all(c == 'not-depressed' for c in classifications):
        return 'not-depressed'
    
    # Mixed or unknown
    return 'depressed' if 'unknown' not in classifications else 'unknown'
