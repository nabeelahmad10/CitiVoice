import os
import io
import re
import requests
from flask import Flask, send_from_directory, request, jsonify
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import fitz  # PyMuPDF

app = Flask(__name__)
# Increase request size limit to 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# -------------------- Mistral API Functions --------------------
MISTRAL_API_KEY = "qCrx2JAOa9tDelNuVPhSusV5Fogl1NEL"  # Replace with your actual API key
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def call_mistral_api(prompt, model="mistral-large-latest"):
    """Call the Mistral API with the provided prompt."""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']

# -------------------- Document Processing Functions --------------------
def extract_text_from_pdf(pdf_bytes):
    """Extract text from a PDF using PyMuPDF."""
    text = ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_image(image_bytes):
    """Extract text from an image using pytesseract OCR."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"Error extracting text from image: {str(e)}"

def process_pdf_with_ocr(pdf_bytes):
    """If regular text extraction yields limited results, use OCR on PDF images."""
    text = extract_text_from_pdf(pdf_bytes)
    if len(text.strip()) < 100 and not text.startswith("Error"):
        try:
            images = convert_from_bytes(pdf_bytes)
            ocr_text = ""
            for image in images:
                ocr_text += pytesseract.image_to_string(image)
            return ocr_text if ocr_text.strip() else text
        except Exception as e:
            return f"Error processing PDF with OCR: {str(e)}"
    return text

# -------------------- Routes --------------------
@app.route('/')
def index():
    # Serve solutionprovider.html from the same folder as this script.
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "solutionprovider.html")

@app.route('/ask', methods=['POST'])
def ask():
    try:
        query = request.form.get('query', '')
        query_type = request.form.get('type', 'general')
        document_text = None

        # Process file upload if provided
        if 'document' in request.files and request.files['document'].filename != '':
            file = request.files['document']
            if file.content_length and file.content_length > 10 * 1024 * 1024:
                return jsonify({"error": "File too large. Please upload files smaller than 10MB."})
            file_bytes = file.read()
            if not file_bytes:
                return jsonify({"error": "Empty file uploaded."})
            if file.filename.lower().endswith('.pdf'):
                document_text = process_pdf_with_ocr(file_bytes)
            elif file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                document_text = extract_text_from_image(file_bytes)
            else:
                return jsonify({"error": "Unsupported file format. Please upload PDF or image files."})
        
        # If a document is provided, build a summary prompt; otherwise process the text query directly.
        if document_text:
            summary_prompt = f"Please summarize the following document in clear, concise language:\n\n{document_text}"
            response_text = call_mistral_api(summary_prompt)
        else:
            response_text = call_mistral_api(query)
            
        return jsonify({
            "response": response_text,
            "document_text": document_text  # For debugging/confirmation
        })
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"})

if __name__ == '__main__':
    print("Starting Solution Provider Backend...")
    app.run(debug=True, host='0.0.0.0', port=5007)
