from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
import json
from datetime import datetime

# Import libraries for document processing
try:
    import python_docx2txt as docx2txt
    from PyPDF2 import PdfReader
    import spacy
    import re
    from textract import process
    import easyocr
    import cv2
    import numpy as np
    ADVANCED_LIBS_AVAILABLE = True
except ImportError:
    print("Advanced libraries not available. Install with: pip install -r requirements.txt")
    ADVANCED_LIBS_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize NLP model if available
nlp = None
if ADVANCED_LIBS_AVAILABLE:
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("English model not found. Install with: python -m spacy download en_core_web_sm")

# Initialize OCR reader
ocr_reader = None
if ADVANCED_LIBS_AVAILABLE:
    try:
        ocr_reader = easyocr.Reader(['vi', 'en'])
    except:
        print("EasyOCR not available")

class CVProcessor:
    def __init__(self):
        self.field_patterns = {
            'name': [
                r'(?:họ\s+tên|tên|name)\s*:?\s*([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ][a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]+)',
                r'^([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ][a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]{5,50})$',
            ],
            'email': [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'(?:email|mail|e-mail)\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            ],
            'phone': [
                r'(?:điện\s*thoại|phone|tel|mobile)\s*:?\s*([+]?[\d\s\-\(\)]{9,15})',
                r'([+]?84[\d\s\-]{8,12})',
                r'(0[\d\s\-]{8,12})',
            ],
            'dob': [
                r'(?:ngày\s*sinh|date\s*of\s*birth|dob|born)\s*:?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})',
            ],
            'gender': [
                r'(?:giới\s*tính|gender|sex)\s*:?\s*(nam|nữ|male|female)',
                r'(nam|nữ)(?:\s|$)',
            ],
            'education': [
                r'(?:học\s*vấn|education|degree)\s*:?\s*(.*?)(?:\n|$)',
                r'(đại\s*học|cao\s*đẳng|thạc\s*sĩ|tiến\s*sĩ|bachelor|master|phd)',
            ],
            'experience': [
                r'(?:kinh\s*nghiệm|experience)\s*:?\s*(.*?)(?:(?:\n.*?){0,5})',
                r'(\d+\s*năm.*?kinh\s*nghiệm)',
            ]
        }

    def extract_text_from_docx(self, file_path):
        """Extract text from DOCX file using multiple methods"""
        try:
            if ADVANCED_LIBS_AVAILABLE:
                # Method 1: python-docx2txt
                text = docx2txt.process(file_path)
                if text.strip():
                    return text, 0.9
            
            # Method 2: textract (fallback)
            if ADVANCED_LIBS_AVAILABLE:
                try:
                    text = process(file_path).decode('utf-8')
                    return text, 0.8
                except:
                    pass
            
            # Method 3: Basic extraction (fallback)
            return "Basic DOCX extraction not implemented", 0.3
            
        except Exception as e:
            return f"Error extracting DOCX: {str(e)}", 0.1

    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file using multiple methods"""
        try:
            if ADVANCED_LIBS_AVAILABLE:
                # Method 1: PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    if text.strip():
                        return text, 0.8
            
            # Method 2: textract (fallback)
            if ADVANCED_LIBS_AVAILABLE:
                try:
                    text = process(file_path).decode('utf-8')
                    return text, 0.7
                except:
                    pass
            
            return "Basic PDF extraction not implemented", 0.3
            
        except Exception as e:
            return f"Error extracting PDF: {str(e)}", 0.1

    def extract_with_nlp(self, text):
        """Use NLP to extract entities"""
        entities = {}
        confidence = {}
        
        if nlp:
            doc = nlp(text)
            
            # Extract person names
            persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                entities['name'] = persons[0]
                confidence['name'] = 0.85
            
            # Extract organizations (could be schools/companies)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                entities['school'] = orgs[0] if 'university' in orgs[0].lower() or 'college' in orgs[0].lower() else None
                entities['company'] = orgs[0] if not entities.get('school') else orgs[1] if len(orgs) > 1 else None
        
        return entities, confidence

    def extract_fields(self, text):
        """Extract all CV fields from text"""
        fields = {}
        confidence = {}
        
        # Use regex patterns
        for field, patterns in self.field_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    fields[field] = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    confidence[field] = 0.8
                    break
            
            # Default confidence for missing fields
            if field not in confidence:
                confidence[field] = 0.0
                fields[field] = ''
        
        # Use NLP if available
        if nlp:
            nlp_entities, nlp_confidence = self.extract_with_nlp(text)
            for key, value in nlp_entities.items():
                if key in fields and (not fields[key] or nlp_confidence.get(key, 0) > confidence.get(key, 0)):
                    fields[key] = value
                    confidence[key] = nlp_confidence[key]
        
        # Post-processing and validation
        fields = self.validate_and_clean_fields(fields)
        
        # Add missing standard fields
        standard_fields = ['name', 'email', 'phone', 'dob', 'gender', 'education', 'school', 'major', 'currentPosition', 'experience', 'appliedPosition']
        for field in standard_fields:
            if field not in fields:
                fields[field] = ''
                confidence[field] = 0.0
        
        return fields, confidence

    def validate_and_clean_fields(self, fields):
        """Validate and clean extracted fields"""
        # Clean phone number
        if 'phone' in fields and fields['phone']:
            phone = re.sub(r'[^\d+]', '', fields['phone'])
            if phone.startswith('84'):
                phone = '+' + phone
            elif phone.startswith('0'):
                phone = '+84' + phone[1:]
            fields['phone'] = phone
        
        # Validate email
        if 'email' in fields and fields['email']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, fields['email']):
                fields['email'] = ''
        
        # Clean and capitalize name
        if 'name' in fields and fields['name']:
            fields['name'] = ' '.join(word.capitalize() for word in fields['name'].split())
        
        return fields

    def process_image_ocr(self, image_path):
        """Process image using OCR"""
        if not ocr_reader:
            return "OCR not available", 0.1
        
        try:
            # Read image
            img = cv2.imread(image_path)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # OCR processing
            results = ocr_reader.readtext(gray)
            
            # Combine text
            text = ' '.join([result[1] for result in results if result[2] > 0.5])
            
            return text, 0.7
            
        except Exception as e:
            return f"OCR Error: {str(e)}", 0.1

# Initialize processor
cv_processor = CVProcessor()

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'advanced_libs': ADVANCED_LIBS_AVAILABLE,
        'nlp': nlp is not None,
        'ocr': ocr_reader is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/process-cv', methods=['POST'])
def process_cv():
    """Process CV file (DOCX/PDF)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    try:
        # Extract text based on file type
        if filename.lower().endswith('.docx'):
            text, extraction_confidence = cv_processor.extract_text_from_docx(file_path)
        elif filename.lower().endswith('.pdf'):
            text, extraction_confidence = cv_processor.extract_text_from_pdf(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        # Extract fields
        fields, confidence = cv_processor.extract_fields(text)
        
        # Adjust confidence based on extraction quality
        for key in confidence:
            confidence[key] *= extraction_confidence
        
        result = {
            'fields': fields,
            'confidence': confidence,
            'rawContent': text[:2000] + ('...' if len(text) > 2000 else ''),
            'extraction_method': 'python_advanced' if ADVANCED_LIBS_AVAILABLE else 'python_basic',
            'processing_time': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/process-image', methods=['POST'])
def process_image():
    """Process image using OCR"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    # Save uploaded image
    filename = secure_filename(f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    try:
        # Process with OCR
        text, extraction_confidence = cv_processor.process_image_ocr(file_path)
        
        # Extract fields
        fields, confidence = cv_processor.extract_fields(text)
        
        # Adjust confidence for OCR
        for key in confidence:
            confidence[key] *= extraction_confidence * 0.8  # OCR is less reliable
        
        result = {
            'fields': fields,
            'confidence': confidence,
            'rawContent': text[:2000] + ('...' if len(text) > 2000 else ''),
            'extraction_method': 'ocr',
            'processing_time': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'OCR processing failed: {str(e)}'}), 500
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/verify-field', methods=['POST'])
def verify_field():
    """Verify a specific field value"""
    data = request.json
    field = data.get('field')
    value = data.get('value')
    raw_content = data.get('rawContent', '')
    
    # Simple verification logic (can be enhanced with ML)
    verified = True
    confidence = 0.8
    
    if field == 'email':
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        verified = bool(re.match(email_pattern, value))
        confidence = 0.95 if verified else 0.1
    
    elif field == 'phone':
        phone_pattern = r'^[+]?[\d\s\-\(\)]{9,15}$'
        verified = bool(re.match(phone_pattern, value))
        confidence = 0.9 if verified else 0.2
    
    elif field == 'name':
        # Check if name appears in raw content
        verified = value.lower() in raw_content.lower()
        confidence = 0.8 if verified else 0.3
    
    return jsonify({
        'field': field,
        'value': value,
        'verified': verified,
        'confidence': confidence,
        'suggestion': None  # Could add AI suggestions here
    })

@app.route('/save-cv', methods=['POST'])
def save_cv():
    """Save CV data to database (or file)"""
    data = request.json
    
    # For now, save to JSON file (in production, use a real database)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"cv_data_{timestamp}.json"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'CV data saved successfully',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Save failed: {str(e)}'}), 500

@app.route('/')
def index():
    """Serve the Python version HTML"""
    return app.send_static_file('python_version.html')

if __name__ == '__main__':
    print("🐍 Python CV Processor Server Starting...")
    print("📚 Advanced libraries available:", ADVANCED_LIBS_AVAILABLE)
    print("🤖 NLP model loaded:", nlp is not None)
    print("👁️ OCR available:", ocr_reader is not None)
    print("🌐 Server URL: http://localhost:5000")
    print("🏥 Health check: http://localhost:5000/health")
    
    app.run(debug=True, host='0.0.0.0', port=5000)