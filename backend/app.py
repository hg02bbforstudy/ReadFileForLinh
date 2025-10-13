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
    import spacy
    from PIL import Image
    import easyocr
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

class AdvancedCVProcessor:
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
                r'(?:giới\s*tính|gender|sex)\s*:?\s*(nam|nữ|male|female)',
                r'\b(nam|nữ|male|female)\b'
            ],
            'education': [
                r'(?:học\s*vấn|education|trình\s*độ)\s*:?\s*(đại\s*học|cao\s*đẳng|trung\s*cấp|phổ\s*thông|bachelor|master|phd|tiến\s*sĩ|thạc\s*sĩ)',
                r'\b(đại\s*học|cao\s*đẳng|trung\s*cấp|bachelor|master|phd|tiến\s*sĩ|thạc\s*sĩ)\b'
            ],
            'school': [
                r'(?:trường|university|college|học\s*viện)\s*:?\s*([^\n\r]{10,80})',
                r'đại\s*học\s+([^\n\r]{5,50})',
                r'trường\s+([^\n\r]{5,50})',
                r'học\s*viện\s+([^\n\r]{5,50})'
            ],
            'major': [
                r'(?:chuyên\s*ngành|major|ngành\s*học)\s*:?\s*([^\n\r]{5,50})',
                r'ngành\s*:?\s*([^\n\r]{5,50})'
            ],
            'appliedPosition': [
                r'(?:vị\s*trí\s*ứng\s*tuyển|applied\s*position)\s*:?\s*([^\n\r]{5,50})',
                r'ứng\s*tuyển\s*:?\s*([^\n\r]{5,50})',
                r'(?:vị\s*trí\s*ứng\s*tuyển.*?nơi\s*làm\s*việc)(.*?)(?:i\.\s*thông\s*tin\s*bản\s*thân|thông\s*tin\s*bản\s*thân)'
            ],
            'currentPosition': [
                r'(?:vị\s*trí\s*hiện\s*tại|current\s*position)\s*:?\s*([^\n\r]{5,50})',
                r'(?:công\s*việc\s*hiện\s*tại)\s*:?\s*([^\n\r]{5,50})'
            ],
            'experience': [
                r'(?:kinh\s*nghiệm|experience)\s*:?\s*([^\n\r]{5,100})',
                r'(\d+)\s*năm\s*kinh\s*nghiệm',
                r'kinh\s*nghiệm\s*:?\s*([^\n\r]{5,100})'
            ]
        }

    def extract_text_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            # Method 1: Using docx2txt
            text = docx2txt.process(file_path)
            if text.strip():
                return text
            
            # Method 2: Manual XML parsing
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                xml_content = zip_file.read('word/document.xml')
                root = ET.fromstring(xml_content)
                
                # Extract text from all text nodes
                text_elements = []
                for elem in root.iter():
                    if elem.text:
                        text_elements.append(elem.text)
                
                return ' '.join(text_elements)
                
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

    def extract_text_from_image(self, image_data):
        """Extract text from image using OCR"""
        try:
            # Initialize EasyOCR reader
            reader = easyocr.Reader(['vi', 'en'])
            
            # Convert image data to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Perform OCR
            results = reader.readtext(image)
            
            # Extract text
            text_lines = [result[1] for result in results]
            return ' '.join(text_lines)
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    def clean_text(self, text):
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep Vietnamese
        text = re.sub(r'[^\w\s@\.\/\-():,áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]', ' ', text)
        return text.strip()

    def extract_field(self, text, patterns, field_name):
        """Extract field using multiple patterns"""
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if matches:
                value = matches[0].strip() if isinstance(matches[0], str) else matches[0][0].strip()
                if value and len(value) > 1:
                    confidence = self.calculate_confidence(value, field_name, i)
                    return value, confidence
        return '', 0.0

    def calculate_confidence(self, value, field_name, pattern_index):
        """Calculate confidence score for extracted value"""
        base_confidence = 0.7 - (pattern_index * 0.1)  # First pattern gets higher confidence
        
        # Field-specific confidence adjustments
        if field_name == 'email' and '@' in value and '.' in value and ' ' not in value:
            base_confidence += 0.25
        elif field_name == 'phone':
            digits = re.sub(r'\D', '', value)
            if 8 <= len(digits) <= 12:
                base_confidence += 0.2
        elif field_name == 'name':
            words = value.split()
            if 2 <= len(words) <= 4 and all(len(w) > 1 for w in words):
                base_confidence += 0.15
        elif field_name == 'dob' and re.match(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}', value):
            base_confidence += 0.1
        
        return min(base_confidence, 0.99)

    def advanced_processing(self, text, results, confidence):
        """Advanced processing for complex fields"""
        # Special processing for applied position
        if not results.get('appliedPosition') or confidence.get('appliedPosition', 0) < 0.7:
            special_result = self.extract_applied_position_special(text)
            if special_result[1] > confidence.get('appliedPosition', 0):
                results['appliedPosition'] = special_result[0]
                confidence['appliedPosition'] = special_result[1]

        # Cross-validate related fields
        if results.get('school') and results.get('education'):
            if 'đại học' in results['school'].lower() and 'đại học' not in results['education'].lower():
                results['education'] = 'Đại học'
                confidence['education'] = max(confidence.get('education', 0), 0.8)

    def extract_applied_position_special(self, text):
        """Special extraction for applied position between specific markers"""
        pattern = r'vị\s*trí\s*ứng\s*tuyển.*?nơi\s*làm\s*việc(.*?)(?:i\.\s*thông\s*tin\s*bản\s*thân|thông\s*tin\s*bản\s*thân|kinh\s*nghiệm)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            extracted = match.group(1).strip()
            if 5 < len(extracted) < 100:
                return extracted, 0.9
        
        return '', 0

    def process_cv(self, text):
        """Main CV processing function"""
        logger.info(f"Processing CV text with {len(text)} characters")
        
        # Clean text
        cleaned_text = self.clean_text(text)
        
        results = {}
        confidence = {}
        
        # Extract each field
        for field, patterns in self.field_patterns.items():
            value, conf = self.extract_field(cleaned_text, patterns, field)
            results[field] = value
            confidence[field] = conf
            
            if value:
                logger.info(f"Extracted {field}: {value} (confidence: {conf:.2f})")

        # Advanced processing
        self.advanced_processing(cleaned_text, results, confidence)
        
        return {
            'fields': results,
            'confidence': confidence,
            'rawContent': text[:2000] + '...' if len(text) > 2000 else text,
            'timestamp': datetime.now().isoformat(),
            'method': 'python_backend'
        }

# Initialize CV processor
cv_processor = AdvancedCVProcessor()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/process-cv', methods=['POST'])
def process_cv():
    """Process CV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # Extract text based on file type
            filename_lower = file.filename.lower()
            
            if filename_lower.endswith('.docx'):
                text = cv_processor.extract_text_from_docx(temp_path)
            elif filename_lower.endswith('.pdf'):
                text = cv_processor.extract_text_from_pdf(temp_path)
            else:
                return jsonify({'error': 'Unsupported file type'}), 400

            if not text.strip():
                return jsonify({'error': 'Could not extract text from file'}), 400

            # Process CV
            result = cv_processor.process_cv(text)
            
            logger.info(f"Successfully processed CV: {file.filename}")
            return jsonify(result)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error processing CV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/process-image', methods=['POST'])
def process_image():
    """Process image file with OCR"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No image selected'}), 400

        # Read image data
        image_data = image_file.read()
        
        # Extract text using OCR
        text = cv_processor.extract_text_from_image(image_data)
        
        if not text.strip():
            return jsonify({'error': 'Could not extract text from image'}), 400

        # Process CV
        result = cv_processor.process_cv(text)
        result['method'] = 'python_ocr'
        
        logger.info(f"Successfully processed image: {image_file.filename}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify-field', methods=['POST'])
def verify_field():
    """Verify a specific field"""
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        raw_content = data.get('rawContent', '')

        if not field or not value:
            return jsonify({'error': 'Missing field or value'}), 400

        # Simple verification logic
        verified = True
        confidence = 0.8

        # Field-specific verification
        if field == 'email':
            verified = '@' in value and '.' in value
            confidence = 0.9 if verified else 0.3
        elif field == 'phone':
            digits = re.sub(r'\D', '', value)
            verified = 8 <= len(digits) <= 12
            confidence = 0.9 if verified else 0.4
        elif field == 'dob':
            verified = bool(re.match(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}', value))
            confidence = 0.8 if verified else 0.3

        return jsonify({
            'field': field,
            'verified': verified,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error verifying field: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/save-cv', methods=['POST'])
def save_cv():
    """Save CV data to database (mock implementation)"""
    try:
        data = request.get_json()
        
        # Mock save to database
        cv_id = f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Saved CV data with ID: {cv_id}")
        
        return jsonify({
            'success': True,
            'cv_id': cv_id,
            'message': 'CV data saved successfully',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error saving CV: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)