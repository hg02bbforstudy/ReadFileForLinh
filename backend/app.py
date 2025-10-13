from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import logging
import re
import json
from datetime import datetime

# Import CV processing libraries
try:
    import docx2txt
    import PyPDF2
except ImportError as e:
    print(f"Warning: Some libraries not available: {e}")

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCVProcessor:
    def __init__(self):
        self.field_patterns = {
            'name': [
                r'(?:họ\s*(?:và\s*)?tên|tên|name)\s*:?\s*([^\n\r]{2,50})',
                r'^([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]+(?:\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]*){1,3})'
            ],
            'email': [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'(?:email|e-mail|thư\s*điện\s*tử)\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            'phone': [
                r'(?:điện\s*thoại|phone|mobile|di\s*động|sđt)\s*:?\s*([+]?[0-9\s\-\.()]{8,})',
                r'([+]?(?:84|0)[1-9][0-9\s\-\.()]{7,})'
            ],
            'appliedPosition': [
                r'(?:vị\s*trí\s*ứng\s*tuyển|position\s*applied)\s*:?\s*([^\n\r]{2,100})'
            ]
        }
    
    def extract_text_from_docx(self, file_path):
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            return ""
    
    def extract_text_from_pdf(self, file_path):
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return ""
    
    def extract_field_value(self, text, field_name):
        patterns = self.field_patterns.get(field_name, [])
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = match.group(1).strip()
                if value and len(value) > 1:
                    return value, 0.8
        return "", 0.0
    
    def process_cv(self, file_path, file_type):
        try:
            if file_type == 'docx':
                raw_text = self.extract_text_from_docx(file_path)
            elif file_type == 'pdf':
                raw_text = self.extract_text_from_pdf(file_path)
            else:
                return {"error": "Unsupported file type"}

            if not raw_text:
                return {"error": "Could not extract text from file"}

            extracted_data = {
                'fields': {},
                'confidence': {},
                'rawContent': raw_text[:1000]
            }

            for field_name in self.field_patterns.keys():
                value, confidence = self.extract_field_value(raw_text, field_name)
                extracted_data['fields'][field_name] = value
                extracted_data['confidence'][field_name] = confidence

            return extracted_data

        except Exception as e:
            logger.error(f"Error processing CV: {e}")
            return {"error": str(e)}

# Initialize processor
cv_processor = SimpleCVProcessor()

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'healthy',
        'message': 'CV Backend is running',
        'port': os.environ.get('PORT', 5000)
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Backend is working!'})

@app.route('/process-cv', methods=['POST', 'OPTIONS'])
def process_cv():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith(('.docx', '.pdf')):
            return jsonify({'error': 'Unsupported file type'}), 400
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            file_type = 'docx' if file.filename.lower().endswith('.docx') else 'pdf'
            result = cv_processor.process_cv(temp_file_path, file_type)
            return jsonify(result)
        
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in process_cv endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)