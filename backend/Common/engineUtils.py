# common/engine_utils.py
# Shared across all engines: file extraction, PDF generation


import io
import json
import logging
import os
from datetime import datetime
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from werkzeug.datastructures import FileStorage

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

def extract_text_from_plain(file, filetype="TXT/CSV"):
    try:
        content = file.read().decode('utf-8', errors='replace')
        return content.strip()
    except Exception as e:
        raise ValueError(f"Error reading {filetype}: {str(e)}")

def extract_text_from_file(file):
    filename = file.filename.lower()
    ext = os.path.splitext(filename)[1]
    extractors = {
        '.pdf': extract_text_from_pdf,
        '.csv': lambda f: extract_text_from_plain(f, filetype="CSV"),
        '.txt': lambda f: extract_text_from_plain(f, filetype="TXT"),
    }
    if ext in extractors:
        return extractors[ext](file)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def generate_combined_pdf_report(results, title_suffix="Analysis"):
    """
    Generate combined PDF report (shared)
    """
    logger.info(f"\n{'='*80}")
    logger.info("STARTING PDF GENERATION")
    logger.info(f"{'='*80}")
    logger.info(f"Number of results: {len(results)}")
    
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    # Set PDF metadata (title and author)
    def set_pdf_metadata(canvas, doc):
        canvas.setTitle(f"Depression Analysis Report ({title_suffix})")
        canvas.setAuthor("Depression Detector System")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Combined Depression Analysis Report ({title_suffix})", styles['Heading1']))
    elements.append(Spacer(1, 0.3 * inch))

    for idx, result in enumerate(results):
        logger.info(f"\n--- Processing Result {idx} ---")
        logger.info(f"Filename: {result.get('filename', 'N/A')}")
        
        elements.append(Paragraph(f"File: {result['filename']}", styles['Heading2']))

        analysis = result["analysis"]
        logger.info(f"Analysis object type: {type(analysis)}")
        logger.info(f"Analysis keys: {analysis.keys() if isinstance(analysis, dict) else 'NOT A DICT'}")
        logger.debug(f"Full analysis object:\n{json.dumps(analysis, indent=2, default=str)}")

        # Unwrap nested analysis if present (from LLM engines)
        if isinstance(analysis, dict) and "analysis" in analysis and "prompt_type" in analysis:
            logger.info("⚠ Detected wrapped analysis structure, unwrapping...")
            actual_analysis = analysis["analysis"]
            logger.debug(f"Unwrapped analysis:\n{json.dumps(actual_analysis, indent=2, default=str)}")
        else:
            actual_analysis = analysis

        # Handle different prompt response structures
        label = 'UNKNOWN'
        confidence = 0.0
        
        # Check for different possible response structures
        if 'label' in actual_analysis:
            label = actual_analysis.get('label', 'UNKNOWN')
            confidence = actual_analysis.get('confidence', 0.0)
            logger.info(f"✓ Found 'label' structure: {label}")
        elif 'prediction' in actual_analysis:
            # Simple prompt format
            pred = actual_analysis.get('prediction', {})
            label = pred.get('class', 'UNKNOWN')
            confidence = pred.get('confidence', 0.0)
            logger.info(f"✓ Found 'prediction' structure: {label}")
        elif 'depression_likelihood' in actual_analysis:
            # Structured prompt format
            label = actual_analysis.get('depression_likelihood', 'UNKNOWN')
            confidence = (actual_analysis.get('confidence', 0) / 100.0)
            logger.info(f"✓ Found 'depression_likelihood' structure: {label}")
        elif 'assessment' in actual_analysis:
            # Few-shot format
            label = actual_analysis.get('assessment', 'UNKNOWN')
            confidence = (actual_analysis.get('confidence', 0) / 100.0)
            logger.info(f"✓ Found 'assessment' structure: {label}")
        elif 'final_classification' in actual_analysis:
            # Chain-of-thought format
            final_class = actual_analysis.get('final_classification', {})
            label = final_class.get('depression_likelihood', 'UNKNOWN')
            confidence = (final_class.get('confidence', 0) / 100.0)
            logger.info(f"✓ Found 'final_classification' structure: {label}")
        elif 'features' in actual_analysis and 'overall_assessment' in actual_analysis:
            # Feature extraction format
            overall = actual_analysis.get('overall_assessment', {})
            prob = overall.get('depression_probability', 0.0)
            label = 'Depression' if prob > 0.5 else 'No Depression'
            confidence = overall.get('confidence_score', 0.0)
            logger.info(f"✓ Found 'features' + 'overall_assessment' structure: {label}")
        elif 'depression_probability' in actual_analysis:
            # Feature extraction format (alternate)
            prob = actual_analysis.get('depression_probability', 0.0)
            label = 'Depression' if prob > 0.5 else 'No Depression'
            confidence = actual_analysis.get('confidence_score', 0.0)
            logger.info(f"✓ Found 'depression_probability' structure: {label}")
        elif 'emotional_state' in actual_analysis and 'clinical_observations' in actual_analysis:
            # Free-form format
            label = actual_analysis.get('depression_likelihood', 'UNKNOWN')
            confidence = (actual_analysis.get('confidence', 0) / 100.0)
            logger.info(f"✓ Found 'free_form' structure: {label}")
        elif 'sentence_analysis' in actual_analysis:
            # Sentence-by-sentence format
            pred = actual_analysis.get('prediction', {})
            label = pred.get('class', 'UNKNOWN')
            confidence = pred.get('confidence', 0.0)
            logger.info(f"✓ Found 'sentence_analysis' structure: {label}")
        else:
            logger.warning(f"⚠ Unknown response structure. Keys: {actual_analysis.keys()}")

        conf_percent = confidence * 100 if confidence <= 1.0 else confidence

        elements.append(Paragraph(f"Label: <b>{label}</b>", styles['Normal']))
        elements.append(Paragraph(f"Confidence: {conf_percent:.1f}%", styles['Normal']))

        # Extract signals if available
        if signals := actual_analysis.get("signals"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Detected Signals:", styles['Heading3']))
            for signal, value in signals.items():
                elements.append(Paragraph(f"- {signal}: {value:.2f}", styles['Normal']))
            logger.info(f"Found signals: {list(signals.keys())}")

        # Extract explanations if available
        if explanations := actual_analysis.get("explanations"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Explanations:", styles['Heading3']))
            for signal, expl in explanations.items():
                if expl:
                    elements.append(Paragraph(f"<b>{signal.capitalize()}:</b> {expl}", styles['Normal']))
                    elements.append(Spacer(1, 0.05 * inch))
            logger.info(f"Found explanations: {len(explanations)} items")

        # Extract linguistic features if available
        if features := actual_analysis.get("linguistic_features"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Linguistic Features:", styles['Heading3']))
            for feature, value in features.items():
                feature_label = feature.replace('_', ' ').title()
                elements.append(Paragraph(f"- {feature_label}: {value}", styles['Normal']))
            logger.info(f"Found linguistic features: {list(features.keys())}")

        # Extract quantifiable features (from feature extraction prompt)
        if quantifiable_features := actual_analysis.get("features"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Extracted Features:", styles['Heading3']))
            for feature, value in quantifiable_features.items():
                feature_label = feature.replace('_', ' ').title()
                elements.append(Paragraph(f"- {feature_label}: {value}", styles['Normal']))
            logger.info(f"Found quantifiable features: {list(quantifiable_features.keys())}")

        # Extract primary indicators (from feature extraction prompt)
        if overall := actual_analysis.get("overall_assessment"):
            if indicators := overall.get("primary_indicators"):
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph("Primary Indicators:", styles['Heading3']))
                for indicator in indicators:
                    elements.append(Paragraph(f"• {indicator}", styles['Normal']))
                logger.info(f"Found primary indicators: {len(indicators)} items")

        # Extract markers and evidence if available (from structured prompt)
        if markers := actual_analysis.get("markers_present"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Depression Markers Detected:", styles['Heading3']))
            for marker in markers:
                elements.append(Paragraph(f"✓ {marker}", styles['Normal']))
            logger.info(f"Found markers: {len(markers)} items")

        # Extract evidence for each marker (from structured prompt)
        if evidence := actual_analysis.get("evidence"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Evidence from Text:", styles['Heading3']))
            for marker, quotes in evidence.items():
                if quotes:  # Only show if there are quotes
                    elements.append(Paragraph(f"<b>{marker}:</b>", styles['Normal']))
                    if isinstance(quotes, list):
                        for quote in quotes:
                            # Indent quoted evidence
                            elements.append(Paragraph(f'<i>"{quote}"</i>', styles['Normal']))
                    else:
                        elements.append(Paragraph(f'<i>"{quotes}"</i>', styles['Normal']))
                    elements.append(Spacer(1, 0.05 * inch))
            logger.info(f"Found evidence: {len(evidence)} markers with quotes")

        # Extract additional analysis fields
        if analysis_desc := actual_analysis.get("clinical_observations"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Clinical Observations:", styles['Heading3']))
            elements.append(Paragraph(analysis_desc, styles['Normal']))
        
        if reasoning := actual_analysis.get("reasoning_summary"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Reasoning:", styles['Heading3']))
            elements.append(Paragraph(reasoning, styles['Normal']))

        # Extract few-shot specific fields
        if indicators := actual_analysis.get("indicators_found"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Indicators Found:", styles['Heading3']))
            if isinstance(indicators, list):
                for indicator in indicators:
                    elements.append(Paragraph(f"• {indicator}", styles['Normal']))
            else:
                elements.append(Paragraph(str(indicators), styles['Normal']))
            logger.info(f"Found indicators: {len(indicators) if isinstance(indicators, list) else 1} items")

        if reasoning := actual_analysis.get("reasoning"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Reasoning:", styles['Heading3']))
            elements.append(Paragraph(reasoning, styles['Normal']))
            logger.info("Found reasoning field")

        if comparison := actual_analysis.get("comparison_to_examples"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Comparison to Examples:", styles['Heading3']))
            elements.append(Paragraph(comparison, styles['Normal']))
            logger.info("Found comparison to examples")

        # Extract chain-of-thought analysis
        if initial_obs := actual_analysis.get("initial_observation"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Initial Observation:", styles['Heading3']))
            elements.append(Paragraph(initial_obs, styles['Normal']))

        if ling_analysis := actual_analysis.get("linguistic_analysis"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Linguistic Analysis:", styles['Heading3']))
            for aspect, description in ling_analysis.items():
                aspect_label = aspect.replace('_', ' ').title()
                elements.append(Paragraph(f"<b>{aspect_label}:</b> {description}", styles['Normal']))
                elements.append(Spacer(1, 0.05 * inch))

        if content_themes := actual_analysis.get("content_themes"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Content Themes:", styles['Heading3']))
            for theme, description in content_themes.items():
                theme_label = theme.replace('_', ' ').title()
                elements.append(Paragraph(f"<b>{theme_label}:</b> {description}", styles['Normal']))
                elements.append(Spacer(1, 0.05 * inch))

        if pattern_recog := actual_analysis.get("pattern_recognition"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Pattern Recognition:", styles['Heading3']))
            for pattern, detected in pattern_recog.items():
                pattern_label = pattern.replace('_', ' ').title()
                status = "✓" if detected else "✗"
                elements.append(Paragraph(f"{status} {pattern_label}", styles['Normal']))

        # Extract free-form clinical analysis fields
        if emotional := actual_analysis.get("emotional_state"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Emotional State:", styles['Heading3']))
            elements.append(Paragraph(emotional, styles['Normal']))
            logger.info("Found emotional state")

        if self_desc := actual_analysis.get("self_description_patterns"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Self-Description Patterns:", styles['Heading3']))
            elements.append(Paragraph(self_desc, styles['Normal']))
            logger.info("Found self description patterns")

        if distress := actual_analysis.get("psychological_distress_indicators"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Psychological Distress Indicators:", styles['Heading3']))
            elements.append(Paragraph(distress, styles['Normal']))
            logger.info("Found psychological distress indicators")

        if overall_imp := actual_analysis.get("overall_impression"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Overall Impression:", styles['Heading3']))
            elements.append(Paragraph(overall_imp, styles['Normal']))
            logger.info("Found overall impression")

        if clinical_notes := actual_analysis.get("clinical_notes"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Clinical Notes:", styles['Heading3']))
            elements.append(Paragraph(clinical_notes, styles['Normal']))
            logger.info("Found clinical notes")

        # Extract sentence-by-sentence analysis data
        if sentence_stats := actual_analysis.get("sentence_analysis"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Sentence-by-Sentence Analysis:", styles['Heading3']))
            
            total = sentence_stats.get("total_sentences", 0)
            depressed = sentence_stats.get("depressed_sentences", 0)
            not_depressed = sentence_stats.get("not_depressed_sentences", 0)
            ratio = sentence_stats.get("depression_ratio", 0)
            avg_conf = sentence_stats.get("avg_confidence", 0)
            
            elements.append(Paragraph(f"Total Sentences Analyzed: <b>{total}</b>", styles['Normal']))
            elements.append(Paragraph(f"Depressed Sentences: <b>{depressed}</b>", styles['Normal']))
            elements.append(Paragraph(f"Non-Depressed Sentences: <b>{not_depressed}</b>", styles['Normal']))
            elements.append(Paragraph(f"Depression Ratio: <b>{ratio*100:.1f}%</b>", styles['Normal']))
            elements.append(Paragraph(f"Average Confidence: <b>{avg_conf*100:.1f}%</b>", styles['Normal']))
            logger.info(f"Found sentence analysis: {total} sentences, {depressed} depressed")

        # Extract individual sentence results (show first 10 or depressed ones)
        if sentences := actual_analysis.get("sentences"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Individual Sentence Results:", styles['Heading3']))
            
            # Show depressed sentences first
            depressed_sentences = [s for s in sentences if s.get("class") == "depression"]
            if depressed_sentences:
                elements.append(Paragraph("<b>Depressed Sentences:</b>", styles['Normal']))
                for sent in depressed_sentences[:10]:  # Limit to 10
                    sent_text = sent.get("sentence", "")[:100]  # Truncate long sentences
                    if len(sent.get("sentence", "")) > 100:
                        sent_text += "..."
                    conf = sent.get("confidence", 0) * 100
                    elements.append(Paragraph(
                        f"• [{conf:.0f}%] <i>\"{sent_text}\"</i>", 
                        styles['Normal']
                    ))
                if len(depressed_sentences) > 10:
                    elements.append(Paragraph(f"... and {len(depressed_sentences) - 10} more depressed sentences", styles['Normal']))
            
            # Show a few non-depressed for context
            non_depressed = [s for s in sentences if s.get("class") == "no-depression"]
            if non_depressed and len(non_depressed) <= 5:
                elements.append(Spacer(1, 0.05 * inch))
                elements.append(Paragraph("<b>Non-Depressed Sentences:</b>", styles['Normal']))
                for sent in non_depressed:
                    sent_text = sent.get("sentence", "")[:100]
                    if len(sent.get("sentence", "")) > 100:
                        sent_text += "..."
                    conf = sent.get("confidence", 0) * 100
                    elements.append(Paragraph(
                        f"• [{conf:.0f}%] <i>\"{sent_text}\"</i>", 
                        styles['Normal']
                    ))
            elif non_depressed:
                elements.append(Spacer(1, 0.05 * inch))
                elements.append(Paragraph(f"<b>Non-Depressed Sentences:</b> {len(non_depressed)} total (not shown)", styles['Normal']))
            
            logger.info(f"Found {len(sentences)} individual sentence results")

        elements.append(Spacer(1, 0.2 * inch))
        
        text_content = result["text"]
        logger.info(f"Text length: {len(text_content)} characters")
        preview = text_content[:500] + "..." if len(text_content) > 500 else text_content
        elements.append(Paragraph("Text Preview:", styles['Heading3']))
        elements.append(Paragraph(preview if preview.strip() else "[Empty text]", styles['Normal']))
        elements.append(Spacer(1, 0.4 * inch))

    logger.info(f"\n{'='*80}")
    logger.info("PDF GENERATION COMPLETE")
    logger.info(f"{'='*80}\n")
    
    doc.build(elements, onFirstPage=set_pdf_metadata, onLaterPages=set_pdf_metadata)
    pdf_buffer.seek(0)
    return pdf_buffer