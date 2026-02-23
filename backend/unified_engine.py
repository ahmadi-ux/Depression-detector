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
    "compound": "backend.Interfaces.Compound"
}

# Display names for PDF reports
LLM_DISPLAY_NAMES = {
    "llama": "Llama",
    "gemini": "Gemini",
    "chatgpt": "ChatGPT",
    "kimi": "Kimi2",
    "qwen": "Qwen",
    "compound": "Compound"
}


def get_llm_interface(llm_type: str):
    """
    Dynamically import and return the analyze_text function for the specified LLM.
    
    Args:
        llm_type: One of 'llama', 'gemini', 'chatgpt', 'kimi', 'qwen', 'compound'
        
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
        llm_type: The LLM to use ('llama', 'gemini', 'chatgpt', 'kimi', 'qwen', 'compound')
        file_payloads: List of file payload dictionaries with 'bytes' and 'filename'
        prompt_type: The prompt template type to use (default: 'simple')
        
    Returns:
        PDF bytes for the analysis report
    """
    llm_type = llm_type.lower()
    logger.info(f"Running job with LLM: {llm_type}, Prompt: {prompt_type}")
    
    combined_results = []
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
                "chatgpt": "llama-3.3-70b-versatile",
                "kimi": "llama-3.1-8b-instant",
                "qwen": "qwen-qwq-32b",
                "compound": "compound-beta"
            }
            model = model_map.get(llm_type, "llama-3.1-8b-instant")
            llm_output = analyze_sentences(extracted_text, model, prompt_type)
        else:
            # Get the interface function for this LLM
            analyze_text = get_llm_interface(llm_type)
            llm_output = analyze_text(extracted_text, prompt_type)
        
        combined_results.append({
            "filename": payload["filename"],
            "text": extracted_text,
            "analysis": llm_output
        })
    
    # Get display name for PDF title
    display_name = LLM_DISPLAY_NAMES.get(llm_type, llm_type.capitalize())
    
    # Generate PDF report
    pdf = generate_combined_pdf_report(combined_results, title_suffix=display_name)
    
    logger.info(f"Job completed successfully for {llm_type}")
    return pdf.getvalue()
