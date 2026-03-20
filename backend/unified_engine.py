"""
Unified LLM engine handler supporting all available models.
Dynamically routes to the appropriate backend based on LLM selection.
"""

import io
import logging
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
    "llamabig": "backend.Interfaces.LlamaBig"
}

# Display names for PDF reports
LLM_DISPLAY_NAMES = {
    "llama": "Llama",
    "gemini": "Gemini",
    "chatgpt": "ChatGPT",
    "kimi": "Kimi2",
    "qwen": "Qwen",
    "compound": "Compound",
    "llamabig": "LlamaBig"
}


def get_llm_interface(llm_type: str):
    """
    Dynamically import and return the analyze_text function for the specified LLM.
    
    Args:
        llm_type: One of 'llama', 'gemini', 'chatgpt', 'kimi', 'qwen', 'compound', 'llamabig'
        
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
        llm_type: The LLM to use ('llama', 'gemini', 'chatgpt', 'kimi', 'qwen', 'compound', 'llamabig')
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
                "llamabig": "llama-3.3-70b-versatile"
            }
            model = model_map.get(llm_type, "llama-3.1-8b-instant")
            llm_output = analyze_sentences(extracted_text, model, prompt_type)
        else:
            # Get the interface function for this LLM
            analyze_text = get_llm_interface(llm_type)
            llm_output = analyze_text(extracted_text, prompt_type)
        
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
    """
    try:
        analysis = llm_output.get("analysis", {})
        
        # Check various possible structures based on prompt type
        if isinstance(analysis, dict):
            # Check for depression_likelihood (high/medium/low pattern)
            if 'depression_likelihood' in analysis:
                level = str(analysis.get('depression_likelihood', '')).lower()
                if level in ['high', 'medium']:
                    return 'depressed'
                elif level == 'low':
                    return 'not-depressed'
            
            # Check for class field - be explicit about patterns
            if 'class' in analysis:
                cls = str(analysis.get('class', '')).lower().strip()
                # Check for NOT depressed patterns first
                if cls in ['not-depressed', 'no-depression', 'not depressed', 'no depression', 'none', 'no', 'healthy', 'normal']:
                    return 'not-depressed'
                # Check for depressed patterns
                elif cls in ['depressed', 'depression', 'yes', 'positive']:
                    return 'depressed'
                # Fallback to substring matching for other variations
                elif 'not' in cls or 'no-' in cls or cls.startswith('no '):
                    return 'not-depressed'
                elif 'depress' in cls:
                    return 'depressed'
            
            # Check for prediction field
            if 'prediction' in analysis:
                pred = analysis.get('prediction', {})
                if isinstance(pred, dict):
                    cls = str(pred.get('class', '')).lower().strip()
                    if cls in ['not-depressed', 'no-depression', 'not depressed', 'no depression']:
                        return 'not-depressed'
                    elif cls in ['depressed', 'depression']:
                        return 'depressed'
                    elif 'not' in cls or 'no' in cls:
                        return 'not-depressed'
                    elif 'depress' in cls:
                        return 'depressed'
            
            # Check for assessment field
            if 'assessment' in analysis:
                assess = str(analysis.get('assessment', '')).lower()
                if assess in ['high', 'medium']:
                    return 'depressed'
                elif assess == 'low':
                    return 'not-depressed'
        
        logger.warning(f"Could not extract depression classification from: {analysis}")
        return 'unknown'
    except Exception as e:
        logger.error(f"Error extracting depression classification: {e}")
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
