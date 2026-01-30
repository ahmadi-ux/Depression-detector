from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import os
import io
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ============================================================================
# FILE EXTRACTION UTILITIES
# ============================================================================

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

def extract_text_from_csv(file):
    """Extract text from CSV file"""
    try:
        content = file.read().decode('utf-8')
        return content.strip()
    except Exception as e:
        raise Exception(f"Error reading CSV: {str(e)}")

def extract_text_from_txt(file):
    """Extract text from TXT file"""
    try:
        content = file.read().decode('utf-8')
        return content.strip()
    except Exception as e:
        raise Exception(f"Error reading TXT: {str(e)}")

def extract_text_from_file(file):
    """Extract text from uploaded file based on file type"""
    filename = file.filename.lower()
    
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file)
    elif filename.endswith('.csv'):
        return extract_text_from_csv(file)
    elif filename.endswith('.txt'):
        return extract_text_from_txt(file)
    else:
        raise Exception(f"Unsupported file type: {os.path.splitext(filename)[1]}")

def process_with_llama(text_content):
    """
    Process text content with Llama LLM
    TODO: Implement actual Llama integration
    For now, return a placeholder response
    """
    # This is a placeholder - replace with actual Llama API call
    print(f"Processing text with Llama (length: {len(text_content)} chars)...")
    
    # TODO: Call actual Llama model
    # response = llama_model.predict(text_content)
    
    return {
        "summary": "This is a placeholder Llama analysis.",
        "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
        "recommendations": ["Recommendation 1", "Recommendation 2"],
        "original_text_length": len(text_content),
    }

def generate_pdf_report(filename, extracted_text, llama_output):
    """Generate a PDF report from Llama output"""
    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1f2937',
        spaceAfter=30,
    )
    elements.append(Paragraph(f"Depression Detector Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add file info
    elements.append(Paragraph(f"<b>File Analyzed:</b> {filename}", styles['Normal']))
    elements.append(Paragraph(f"<b>Analysis Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add Llama analysis results
    elements.append(Paragraph("<b>Analysis Summary</b>", styles['Heading2']))
    elements.append(Paragraph(llama_output.get('summary', 'N/A'), styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add key findings
    elements.append(Paragraph("<b>Key Findings</b>", styles['Heading2']))
    for finding in llama_output.get('key_findings', []):
        elements.append(Paragraph(f"• {finding}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add recommendations
    elements.append(Paragraph("<b>Recommendations</b>", styles['Heading2']))
    for rec in llama_output.get('recommendations', []):
        elements.append(Paragraph(f"• {rec}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add extracted text section (truncated)
    elements.append(Paragraph("<b>Original Text (first 1000 chars)</b>", styles['Heading2']))
    text_preview = extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
    elements.append(Paragraph(text_preview, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return pdf_buffer

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Main endpoint: receives file → processes with Llama → returns PDF report
    """
    try:
        print("=== UPLOAD REQUEST RECEIVED ===")
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"Processing file: {file.filename} ({file.content_type})")
        
        # Step 1: Extract text from file
        print("Step 1: Extracting text...")
        extracted_text = extract_text_from_file(file)
        print(f"Extracted {len(extracted_text)} characters")
        
        # Step 2: Process with Llama
        print("Step 2: Processing with Llama...")
        llama_output = process_with_llama(extracted_text)
        
        # Step 3: Generate PDF report
        print("Step 3: Generating PDF report...")
        pdf_report = generate_pdf_report(file.filename, extracted_text, llama_output)
        
        # Return PDF for download
        print("Returning PDF report...")
        return send_file(
            pdf_report,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

if __name__ == '__main__':
    app.run(debug=False, port=5000)
