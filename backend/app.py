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
                r'^([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]+(?:\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]*){1,3})',
                r'\b([A-Z][a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]+\s+(?:[A-Z][a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]+\s*)+)\b'
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
                r'(?:học\s*vấn|education|qualification|trình\s*độ)\s*:?\s*([^\n\r]{2,100})',
                r'(?:bằng\s*cấp|degree)\s*:?\s*([^\n\r]{2,100})',
                r'\b(đại\s*học|cao\s*đẳng|trung\s*cấp|thạc\s*sĩ|tiến\s*sĩ|bachelor|master|phd|diploma)\b'
            ],
            'school': [
                r'(?:trường|school|university|college|học\s*tại)\s*:?\s*([^\n\r]{2,100})',
                r'(?:đại\s*học|university)\s*([^\n\r]{2,100})',
                r'(?:tốt\s*nghiệp\s*tại|graduated\s*from)\s*:?\s*([^\n\r]{2,100})'
            ],
            'major': [
                r'(?:chuyên\s*ngành|major|field|ngành\s*học)\s*:?\s*([^\n\r]{2,100})',
                r'(?:ngành\s*học|specialization)\s*:?\s*([^\n\r]{2,100})'
            ],
            'currentPosition': [
                r'(?:vị\s*trí\s*hiện\s*tại|current\s*position|công\s*việc\s*hiện\s*tại)\s*:?\s*([^\n\r]{2,100})',
                r'(?:làm\s*việc\s*tại|working\s*as)\s*:?\s*([^\n\r]{2,100})'
            ],
            'experience': [
                r'(?:kinh\s*nghiệm|experience|số\s*năm\s*kinh\s*nghiệm)\s*:?\s*([^\n\r]{2,200})',
                r'([0-9]+\s*(?:năm|year|tháng|month)?\s*(?:kinh\s*nghiệm|experience))',
                r'(?:đã\s*làm\s*việc|worked\s*for)\s*([0-9]+\s*(?:năm|year))'
            ],
            'appliedPosition': [
                r'(?:vị\s*trí\s*ứng\s*tuyển|position\s*applied|ứng\s*tuyển\s*vị\s*trí)\s*([^\n\r]{2,100})',
                r'(?:ứng\s*tuyển\s*vào\s*vị\s*trí|applying\s*for)\s*:?\s*([^\n\r]{2,100})',
                r'vị\s*trí\s*ứng\s*tuyển[\s\S]*?nơi\s*làm\s*việc([\s\S]*?)(?:I\.\s*THÔNG\s*TIN|$)',
                r'Vị\s*trí\s*ứng\s*tuyển[\s\S]*?Nơi\s*làm\s*việc([\s\S]*?)(?:I\.\s*THÔNG\s*TIN|$)'
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
        # Special handling for applied position
        if field_name == 'appliedPosition':
            return self.extract_applied_position(text)
        
        patterns = self.field_patterns.get(field_name, [])
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = match.group(1).strip()
                if value and len(value) > 1:
                    return value, 0.8
        return "", 0.0
    
    def extract_applied_position(self, text):
        """Extract applied position from specific text section as requested"""
        try:
            # Method 1: Extract between "Vị trí ứng tuyển Nơi làm việc" and "I. THÔNG TIN BẢN THÂN"
            pattern1 = r'vị\s*trí\s*ứng\s*tuyển\s*nơi\s*làm\s*việc([\s\S]*?)(?:i\.\s*thông\s*tin\s*bản\s*thân|$)'
            match1 = re.search(pattern1, text, re.IGNORECASE | re.MULTILINE)
            
            if match1:
                content = match1.group(1).strip()
                # Clean up the content
                content = re.sub(r'\n+', ' ', content)
                content = re.sub(r'\s+', ' ', content)
                if len(content) > 5:
                    return content[:200], 0.9
            
            # Method 2: Look for specific applied position patterns
            patterns = [
                r'(?:vị\s*trí\s*ứng\s*tuyển|applying\s*for)\s*:?\s*([^\n\r]{5,100})',
                r'(?:ứng\s*tuyển\s*vị\s*trí|position\s*applied)\s*:?\s*([^\n\r]{5,100})'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    value = match.group(1).strip()
                    if len(value) > 5:
                        return value, 0.8
            
            return "", 0.0
            
        except Exception as e:
            logger.error(f"Error extracting applied position: {e}")
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

@app.route('/verify-field', methods=['POST', 'OPTIONS'])
def verify_field():
    if request.method == 'OPTIONS':
        return '', 200
        
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

@app.route('/save-cv', methods=['POST', 'OPTIONS'])
def save_cv():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        # In a real application, save to database here
        logger.info(f"CV data received for saving: {data.get('fields', {}).get('name', 'Unknown')}")
        
        return jsonify({
            'success': True,
            'message': 'CV data saved successfully',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in save_cv endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/process-image', methods=['POST', 'OPTIONS'])
def process_image():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        
        # For now, return a placeholder result (OCR would be added later)
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