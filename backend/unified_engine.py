"""
Unified LLM engine handler supporting all available models.
Dynamically routes to the appropriate backend based on LLM selection.
"""

import io
import logging
from werkzeug.datastructures import FileStorage
from backend.Common.engineUtils import extract_text_from_file, generate_combined_pdf_report

logger = logging.getLogger(__name__)

# Mapping of LLM names to their interface modules
LLM_INTERFACES = {
    "llama": "backend.Llama.interface",
    "gemini": "backend.Gemini.interface",
    "chatgpt": "backend.ChatGPT.interface",
    "kimi": "backend.Kimik2.interface",
    "qwen": "backend.Gwen.interface",
    "compound": "backend.Compound.interface"
}

# Display names for PDF reports
LLM_DISPLAY_NAMES = {
    "llama": "Llama",
    "gemini": "Gemini",
    "chatgpt": "ChatGPT",
    "kimi": "Kimi",
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
    
    # Get the interface function for this LLM
    analyze_text = get_llm_interface(llm_type)
    
    combined_results = []
    for payload in file_payloads:
        logger.debug(f"Processing file: {payload['filename']}")
        
        # Extract text from file
        file = FileStorage(
            stream=io.BytesIO(payload["bytes"]), 
            filename=payload["filename"]
        )
        extracted_text = extract_text_from_file(file)
        
        # Analyze using the selected LLM
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
