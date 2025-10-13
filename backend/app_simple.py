from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import logging
from datetime import datetime
import re
import json

# Import libraries for document processing
try:
    import docx2txt
    import PyPDF2
    from PIL import Image
    import io
    import zipfile
    import xml.etree.ElementTree as ET
except ImportError as e:
    print(f"Warning: Some libraries not available: {e}")

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

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
                r'([+]?(?:84|0)[1-9][0-9\s\-\.()]{7,})',
                r'\b([0-9]{3,4}[\s\-\.]?[0-9]{3,4}[\s\-\.]?[0-9]{3,4})\b'
            ],
            'dob': [
                r'(?:ngày\s*sinh|date\s*of\s*birth|dob|sinh\s*ngày)\s*:?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
                r'\b([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})\b'
            ],
            'gender': [
                r'(?:giới\s*tính|gender|sex)\s*:?\s*(nam|nữ|male|female|m|f)',
                r'\b(nam|nữ|male|female)\b'
            ],
            'education': [
                r'(?:học\s*vấn|education|qualification)\s*:?\s*([^\n\r]{2,100})',
                r'(?:bằng\s*cấp|degree)\s*:?\s*([^\n\r]{2,100})',
                r'\b(đại\s*học|cao\s*đẳng|trung\s*cấp|thạc\s*sĩ|tiến\s*sĩ|bachelor|master|phd|diploma)\b'
            ],
            'school': [
                r'(?:trường|school|university|college)\s*:?\s*([^\n\r]{2,100})',
                r'(?:đại\s*học|university)\s*([^\n\r]{2,100})'
            ],
            'major': [
                r'(?:chuyên\s*ngành|major|field)\s*:?\s*([^\n\r]{2,100})',
                r'(?:ngành\s*học|specialization)\s*:?\s*([^\n\r]{2,100})'
            ],
            'experience': [
                r'(?:kinh\s*nghiệm|experience)\s*:?\s*([^\n\r]{2,200})',
                r'([0-9]+\s*(?:năm|year|tháng|month)?\s*(?:kinh\s*nghiệm|experience))'
            ],
            'appliedPosition': [
                r'(?:vị\s*trí\s*ứng\s*tuyển|position\s*applied)\s*:?\s*([^\n\r]{2,100})',
                r'(?:ứng\s*tuyển\s*vị\s*trí|applying\s*for)\s*:?\s*([^\n\r]{2,100})'
            ]
        }

    def extract_text_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            text = docx2txt.process(file_path)
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            return ""

    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
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
        """Extract field value using regex patterns"""
        patterns = self.field_patterns.get(field_name, [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = match.group(1).strip()
                if value and len(value) > 1:
                    return value, 0.8  # Return value and confidence
        
        return "", 0.0

    def calculate_confidence(self, field_name, value, context):
        """Calculate confidence score for extracted field"""
        if not value:
            return 0.0
        
        base_confidence = 0.6
        
        # Boost confidence based on field-specific rules
        if field_name == 'email' and '@' in value and '.' in value:
            base_confidence += 0.3
        elif field_name == 'phone' and re.match(r'[+]?[0-9\s\-\.()]{8,}', value):
            base_confidence += 0.2
        elif field_name == 'name' and len(value.split()) >= 2:
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)

    def process_cv(self, file_path, file_type):
        """Main CV processing function"""
        try:
            # Extract text based on file type
            if file_type == 'docx':
                raw_text = self.extract_text_from_docx(file_path)
            elif file_type == 'pdf':
                raw_text = self.extract_text_from_pdf(file_path)
            else:
                return {"error": "Unsupported file type"}

            if not raw_text:
                return {"error": "Could not extract text from file"}

            # Extract fields
            extracted_data = {
                'fields': {},
                'confidence': {},
                'rawContent': raw_text[:1000]  # First 1000 chars
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Python CV Backend is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/process-cv', methods=['POST'])
def process_cv():
    """Process CV file endpoint"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        if not file.filename.lower().endswith(('.docx', '.pdf')):
            return jsonify({'error': 'Unsupported file type. Only DOCX and PDF are supported.'}), 400
        
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Process CV
            file_type = 'docx' if file.filename.lower().endswith('.docx') else 'pdf'
            result = cv_processor.process_cv(temp_file_path, file_type)
            
            return jsonify(result)
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in process_cv endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/verify-field', methods=['POST'])
def verify_field():
    """Verify field value endpoint"""
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        raw_content = data.get('rawContent', '')
        
        # Simple verification - check if value appears in raw content
        verified = value.lower() in raw_content.lower() if value and raw_content else False
        
        return jsonify({
            'field': field,
            'value': value,
            'verified': verified,
            'confidence': 0.8 if verified else 0.3
        })
    
    except Exception as e:
        logger.error(f"Error in verify_field endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/save-cv', methods=['POST'])
def save_cv():
    """Save CV data endpoint (placeholder)"""
    try:
        data = request.get_json()
        
        # In a real application, you would save to database here
        logger.info(f"CV data received for saving: {data.get('fields', {}).get('name', 'Unknown')}")
        
        return jsonify({
            'success': True,
            'message': 'CV data saved successfully',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in save_cv endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/process-image', methods=['POST'])
def process_image():
    """Process image endpoint (simplified without OCR)"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        
        # For now, return a placeholder result
        return jsonify({
            'fields': {
                'name': 'Extracted from Image',
                'email': 'image@example.com',
                'phone': '0123456789'
            },
            'confidence': {
                'name': 0.6,
                'email': 0.5,
                'phone': 0.5
            },
            'rawContent': 'Image processed with basic extraction...'
        })
    
    except Exception as e:
        logger.error(f"Error in process_image endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)