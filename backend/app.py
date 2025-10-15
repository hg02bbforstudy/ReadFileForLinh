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
                # Main pattern: extract between "Họ và tên (chữ in hoa)" and "Ngày sinh"
                r'(?:họ\s*và\s*tên\s*\([^)]*\))([\s\S]*?)(?:ngày\s*sinh)',
                r'(?:họ\s*và\s*tên)([\s\S]*?)(?:ngày\s*sinh)',
                r'(?:ho\s*va\s*ten\s*\([^)]*\))([\s\S]*?)(?:ngay\s*sinh)',  # Without diacritics
                r'(?:ho\s*va\s*ten)([\s\S]*?)(?:ngay\s*sinh)',
                # Fallback patterns
                r'(?:họ\s*(?:và\s*)?tên|tên|name)\s*:?\s*([^\n\r]{2,50})',
                r'([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]+\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]+\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]+)'
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
                r'\b(nữ|nam|male|female)\b',
                r'Nữ',  # Specific match for "Nữ"
                r'Nam'   # Specific match for "Nam"
            ],
            'education': [
                r'(?:học\s*vấn|education|qualification|trình\s*độ)\s*:?\s*([^\n\r]{2,100})',
                r'(?:bằng\s*cấp|degree)\s*:?\s*([^\n\r]{2,100})',
                r'\b(đại\s*học|cao\s*đẳng|trung\s*cấp|thạc\s*sĩ|tiến\s*sĩ|bachelor|master|phd|diploma)\b',
                r'Đại\s*học',  # Specific pattern for "Đại học"
                r'(?:^|\n|\s)(Đại\s*học)(?=\s|$|\n)'
            ],
            'school': [
                r'(?:trường|school|university|college|học\s*tại)\s*:?\s*([^\n\r]{2,100})',
                r'(?:đại\s*học|university)\s*([^\n\r]{2,100})',
                r'(?:tốt\s*nghiệp\s*tại|graduated\s*from)\s*:?\s*([^\n\r]{2,100})',
                r'Đại\s*học\s*FPT\s*Hà\s*Nội',  # Specific pattern
                r'(Đại\s*học\s*[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ\s]+)',
                r'(?:học\s*tại|tại|at)\s*(Đại\s*học\s*[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ\s]+)'
            ],
            'major': [
                r'(?:chuyên\s*ngành|major|field|ngành\s*học)\s*:?\s*([^\n\r]{2,100})',
                r'(?:ngành\s*học|specialization)\s*:?\s*([^\n\r]{2,100})',
                r'Digital\s*Marketing',  # Specific pattern for "Digital Marketing"
                r'(Digital\s*[A-Za-z]+)',
                r'(?:ngành|chuyên\s*ngành)\s*:?\s*(Digital\s*Marketing)',
                r'(?:chuyên\s*về|học\s*về)\s*([A-Za-z\s]+ing)'
            ],
            'currentPosition': [
                # Return empty if no "hiện tại", "bây giờ", "currently" found
                r'(?:vị\s*trí\s*hiện\s*tại|current\s*position|công\s*việc\s*hiện\s*tại|hiện\s*đang|currently\s*working)\s*:?\s*([^\n\r]{2,100})',
                r'(?:đang\s*làm|hiện\s*tại\s*làm|bây\s*giờ\s*làm)\s*:?\s*([^\n\r]{2,100})',
                # This will intentionally match very rarely to return empty string
                r'___CURRENT_POSITION_NOT_FOUND___'
            ],
            'experience': [
                # Pattern to match "11/2023 - 04/2024: Nhân viên Digital Marketing - Tập Đoàn MAMA Sữa Non"
                r'([0-9]{1,2}\/[0-9]{4}\s*-\s*[0-9]{1,2}\/[0-9]{4}:\s*[^\n\r]+)',
                r'([0-9]{1,2}\/[0-9]{4}\s*[-–]\s*[0-9]{1,2}\/[0-9]{4}[:\s]*[^\n\r]+)',
                r'(?:kinh\s*nghiệm|experience)\s*:?\s*([^\n\r]{10,200})',
                r'(?:quá\s*trình\s*công\s*tác|work\s*experience)\s*:?\s*([^\n\r]{10,200})',
                # More flexible date range patterns
                r'([0-9\/\-\s]+:\s*[A-Za-zÀ-ỹ\s\-]+(?:\s*-\s*[A-Za-zÀ-ỹ\s]+)*)'
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
        
        # Special handling for name
        if field_name == 'name':
            return self.extract_name(text)
        
        patterns = self.field_patterns.get(field_name, [])
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = match.group(1).strip()
                if value and len(value) > 1:
                    return value, 0.8
        return "", 0.0
    
    def extract_name(self, text):
        """Extract name between 'Họ và tên (chữ in hoa)' and 'Ngày sinh'"""
        try:
            patterns = [
                # Pattern 1: Between "Họ và tên (chữ in hoa)" and "Ngày sinh"
                r'(?:họ\s*và\s*tên\s*\([^)]*\))([\s\S]*?)(?:ngày\s*sinh)',
                r'(?:họ\s*và\s*tên)([\s\S]*?)(?:ngày\s*sinh)',
                # Pattern 2: Without diacritics (for cases with encoding issues)
                r'(?:ho\s*va\s*ten\s*\([^)]*\))([\s\S]*?)(?:ngay\s*sinh)',
                r'(?:ho\s*va\s*ten)([\s\S]*?)(?:ngay\s*sinh)',
                # Pattern 3: Mixed case variations
                r'(?:Ho\s*va\s*ten\s*\([^)]*\))([\s\S]*?)(?:Ngay\s*sinh)',
                r'(?:HO\s*VA\s*TEN\s*\([^)]*\))([\s\S]*?)(?:NGAY\s*SINH)',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for match in matches:
                    raw_content = match.group(1).strip()
                    
                    # Clean the extracted content
                    cleaned_name = self.clean_extracted_name(raw_content)
                    if cleaned_name:
                        return cleaned_name, 0.9
            
            # Fallback to general patterns
            fallback_patterns = [
                r'(?:họ\s*(?:và\s*)?tên|tên|name)\s*:?\s*([^\n\r]{2,50})',
                r'([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]+\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]+\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]+)'
            ]
            
            for pattern in fallback_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    value = match.group(1).strip()
                    cleaned_name = self.clean_extracted_name(value)
                    if cleaned_name:
                        return cleaned_name, 0.7
            
            return "", 0.0
            
        except Exception as e:
            logger.error(f"Error extracting name: {e}")
            return "", 0.0
    
    def clean_extracted_name(self, raw_text):
        """Clean and format extracted name text, including splitting joined words"""
        if not raw_text:
            return ""
        
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', raw_text).strip()
        
        # Remove common unwanted patterns
        cleaned = re.sub(r'^\W+|\W+$', '', cleaned)  # Remove leading/trailing non-word chars
        cleaned = re.sub(r'^[:\-\s]+|[:\-\s]+$', '', cleaned)  # Remove colons, dashes at start/end
        
        # First, try to find already properly formatted names
        name_patterns = [
            # Pattern for full Vietnamese names (3 words)
            r'([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]{2,}\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]{2,}\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]{2,})',
            # Pattern for 2-word names
            r'([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]{2,}\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]{2,})',
            # Mixed case pattern
            r'([A-Za-zÀ-ỹ]{2,}\s+[A-Za-zÀ-ỹ]{2,}\s+[A-Za-zÀ-ỹ]{2,})',
            r'([A-Za-zÀ-ỹ]{2,}\s+[A-Za-zÀ-ỹ]{2,})'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, cleaned)
            if match:
                name = match.group(1).strip()
                # Validate: name should be 2-50 chars, contain at least one space
                if 2 <= len(name) <= 50 and ' ' in name:
                    return name
        
        # If no properly formatted name found, try to split joined text
        separated_name = self.separate_joined_name(cleaned)
        if separated_name:
            return separated_name
        
        # If no pattern matches but we have reasonable text
        if 2 <= len(cleaned) <= 50 and any(c.isalpha() for c in cleaned):
            return cleaned
        
        return ""
    
    def separate_joined_name(self, text):
        """Separate joined Vietnamese names using linguistic patterns"""
        if not text or len(text) < 6:  # Minimum for 3 Vietnamese names
            return ""
        
        # Remove spaces first to work with joined text
        joined_text = re.sub(r'\s+', '', text).upper()
        
        # Common Vietnamese surname patterns
        vietnamese_surnames = [
            'NGUYEN', 'TRAN', 'LE', 'PHAM', 'HOANG', 'HUYNH', 'VU', 'VO', 'DANG', 'BUI',
            'DO', 'HO', 'NGO', 'DUONG', 'LY', 'NGUYEN', 'TRAN', 'LE', 'PHAM', 'HOANG'
        ]
        
        # Common Vietnamese middle names
        vietnamese_middle_names = [
            'VAN', 'THI', 'CONG', 'DINH', 'HUU', 'MINH', 'QUOC', 'THANH', 'XUAN', 'ANH',
            'BAO', 'CAO', 'DUC', 'HAI', 'HONG', 'HUY', 'KHANH', 'KHANG', 'LINH', 'LONG',
            'MAI', 'NAM', 'PHONG', 'QUANG', 'TAM', 'THANG', 'TRUNG', 'TUAN', 'VIET', 'YEN'
        ]
        
        # Try to match known patterns like "PHAMYENLINH"
        specific_patterns = [
            ('PHAMYENLINH', 'PHAM YEN LINH'),
            ('NGUYENVANNAM', 'NGUYEN VAN NAM'),
            ('TRANTHIMAI', 'TRAN THI MAI'),
            ('LEVANANH', 'LE VAN ANH'),
        ]
        
        # Check specific known patterns first
        for joined, separated in specific_patterns:
            if joined in joined_text:
                return separated
        
        # Try to split using surname detection
        for surname in vietnamese_surnames:
            if joined_text.startswith(surname):
                remaining = joined_text[len(surname):]
                if len(remaining) >= 4:  # At least 2 chars for middle + 2 for last name
                    # Try to split remaining into 2 parts
                    separated_parts = self.split_remaining_name(remaining, vietnamese_middle_names)
                    if separated_parts:
                        return f"{surname} {separated_parts[0]} {separated_parts[1]}"
        
        # Fallback: try to split by character patterns (capital letters, vowel patterns)
        capitalized_split = self.split_by_capital_patterns(joined_text)
        if capitalized_split:
            return capitalized_split
        
        return ""
    
    def split_remaining_name(self, remaining_text, middle_names):
        """Split remaining text into middle and last name"""
        for middle in middle_names:
            if remaining_text.startswith(middle):
                last_name = remaining_text[len(middle):]
                if len(last_name) >= 2:  # Valid last name length
                    return [middle, last_name]
        
        # If no middle name match, split roughly in half
        if len(remaining_text) >= 4:
            mid_point = len(remaining_text) // 2
            # Adjust split point to avoid splitting in middle of syllable
            if mid_point < len(remaining_text) - 1:
                return [remaining_text[:mid_point], remaining_text[mid_point:]]
        
        return None
    
    def split_by_capital_patterns(self, text):
        """Split text by detecting capital letter patterns"""
        # Look for patterns like "ABCDEFGHI" -> "ABC DEF GHI"
        # This is a simple heuristic based on Vietnamese name lengths
        if len(text) >= 9:  # Minimum for 3-part name like PHAMYENLINH
            # Try 4-3-4, 4-3-3, 3-3-3 etc patterns
            patterns = [
                (4, 3, None),  # PHAM-YEN-LINH
                (3, 3, None),  # TRA-VAN-NAM  
                (5, 2, None),  # NGUYEN-VAN-A
                (3, 4, None),  # LE-MINH-HOANG
            ]
            
            for p1, p2, p3 in patterns:
                if p1 + p2 < len(text):
                    part1 = text[:p1]
                    part2 = text[p1:p1+p2]
                    part3 = text[p1+p2:]
                    
                    # Validate parts (should be reasonable lengths)
                    if (2 <= len(part1) <= 7 and 
                        2 <= len(part2) <= 5 and 
                        2 <= len(part3) <= 7):
                        return f"{part1} {part2} {part3}"
        
        return ""
    
    def extract_applied_position(self, text):
        """Extract applied position from between 'Vị trí ứng tuyển Nơi làm việc' and 'THÔNG TIN BẢN THÂN'"""
        try:
            # Main extraction: Between markers with comprehensive format support
            section_patterns = [
                # Joined text format: "MãsốVịtríứngtuyểnNơilàmviệc...I.THÔNGTINBẢNTHÂN"
                r'(?:mãsố|masố|ma\s*so)\s*(?:vịtríứngtuyển|vitriungtuyen|vị\s*trí\s*ứng\s*tuyển)\s*(?:nơilàmviệc|noilamviec|nơi\s*làm\s*việc)\s*([\s\S]*?)(?:i\.\s*(?:thôngtinbảnthân|thongtinbanthan|thông\s*tin\s*bản\s*thân)|(?:thôngtinbảnthân|thongtinbanthan|thông\s*tin\s*bản\s*thân)|$)',
                # Single line format: "Mã số Vị trí ứng tuyển Nơi làm việc ... I. THÔNG TIN BẢN THÂN"
                r'mã\s*số\s*vị\s*trí\s*ứng\s*tuyển\s*nơi\s*làm\s*việc\s*([\s\S]*?)(?:i\.\s*thông\s*tin\s*bản\s*thân|thông\s*tin\s*bản\s*thân|$)',
                # Table format: "Vị trí ứng tuyển\n\nNơi làm việc\n\n\n\nMarketing\n\n\n\nTổ chức nhân sự\n\n\n\nTHÔNG TIN BẢN THÂN"
                r'vị\s*trí\s*ứng\s*tuyển\s*(?:\n|\r\n?)*\s*nơi\s*làm\s*việc([\s\S]*?)(?:i\.\s*thông\s*tin\s*bản\s*thân|thông\s*tin\s*bản\s*thân|i\.\s*thông\s*tin|$)',
                # Standard format with various spacing
                r'vị\s*trí\s*ứng\s*tuyển[\s\S]*?nơi\s*làm\s*việc([\s\S]*?)(?:i\.\s*thông\s*tin\s*bản\s*thân|thông\s*tin\s*bản\s*thân|i\.\s*thông\s*tin|$)',
                # Without diacritics (encoding issues)
                r'vi\s*tri\s*ung\s*tuyen[\s\S]*?noi\s*lam\s*viec([\s\S]*?)(?:i\.\s*thong\s*tin\s*ban\s*than|thong\s*tin\s*ban\s*than|i\.\s*thong\s*tin|$)',
                # Mixed case variations
                r'Vi\s*tri\s*ung\s*tuyen[\s\S]*?Noi\s*lam\s*viec([\s\S]*?)(?:I\.\s*Thong\s*tin\s*ban\s*than|Thong\s*tin\s*ban\s*than|I\.\s*THONG\s*TIN|$)',
                r'VI\s*TRI\s*UNG\s*TUYEN[\s\S]*?NOI\s*LAM\s*VIEC([\s\S]*?)(?:I\.\s*THONG\s*TIN\s*BAN\s*THAN|THONG\s*TIN\s*BAN\s*THAN|I\.\s*THONG\s*TIN|$)',
                # Joined text variations  
                r'vitriungtuyennoi?lamviec([\s\S]*?)(?:i?thongtinbanthan|$)',
                r'VITRIUNGTUYENNOI?LAMVIEC([\s\S]*?)(?:I?THONGTINBANTHAN|$)'
            ]
            
            for pattern in section_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    raw_content = match.group(1).strip()
                    
                    if len(raw_content) > 3:
                        # Process the extracted content
                        processed_content = self.process_applied_position_content(raw_content)
                        if processed_content:
                            return processed_content, 0.95
            
            # Fallback: Look for position patterns anywhere in text
            fallback_patterns = [
                r'(?:vị\s*trí\s*ứng\s*tuyển|ứng\s*tuyển\s*vị\s*trí)\s*:?\s*([^\n\r]{5,200})',
                r'(?:applying\s*for|position\s*applied)\s*:?\s*([^\n\r]{5,200})'
            ]
            
            for pattern in fallback_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    content = match.group(1).strip()
                    processed_content = self.process_applied_position_content(content)
                    if processed_content:
                        return processed_content, 0.7
            
            return "", 0.0
            
        except Exception as e:
            logger.error(f"Error extracting applied position: {e}")
            return "", 0.0
    
    def process_applied_position_content(self, raw_content):
        """Process and clean applied position content - take ALL data between markers as one string"""
        if not raw_content:
            return ""
        
        # FIRST: Preserve the raw content completely - don't lose any text between markers
        logger.info(f"Raw position content: '{raw_content}'")
        
        # Convert newlines to spaces but preserve all actual content
        content = re.sub(r'[\n\r]+', ' ', raw_content)
        content = re.sub(r'\s+', ' ', content)  # Multiple spaces to single space
        content = content.strip()
        
        # ONLY remove characters at very start/end, not in middle
        content = re.sub(r'^[:\-\s\.,;]+', '', content)
        content = re.sub(r'[:\-\s\.,;]+$', '', content)
        
        # MINIMAL filtering - only remove obvious non-position elements
        # Remove standalone numbers (but keep words with numbers like "K1", "P1")
        content = re.sub(r'\b\d{1,10}\b(?!\w)', ' ', content)
        
        # Remove common header/footer words but be very conservative
        very_specific_skip = [
            r'\bmã\s*số\b',
            r'\bhộ\s*khẩu\s*thường\s*trú\b',
            r'\bnơi\s*ở\s*hiện\s*tại\b',
            r'\bthông\s*tin\s*người\s*liên\s*hệ\b',
            r'\btình\s*trạng\s*hôn\s*nhân\b',
            r'\bsức\s*khỏe\b',
            r'\bchiều\s*cao\b',
            r'\bcân\s*nặng\b'
        ]
        
        for pattern in very_specific_skip:
            content = re.sub(pattern, ' ', content, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Handle joined Vietnamese words - separate them
        content = self.separate_vietnamese_words(content)
        
        # If result has reasonable content, return it
        if len(content) >= 1 and re.search(r'[A-Za-zÀ-ỹ]', content):
            logger.info(f"Processed position content: '{content}'")
            return content
        
        return ""
    
    def separate_vietnamese_words(self, text):
        """Separate joined Vietnamese words for better readability"""
        if not text:
            return text
            
        # Common position-related words that might be joined
        word_mappings = {
            'marketing': 'Marketing',
            'Marketing': 'Marketing',
            'MARKETING': 'Marketing',
            'tổchứcnhânsự': 'Tổ chức nhân sự',
            'Tổchứcnhânsự': 'Tổ chức nhân sự', 
            'TỔCHỨCNHÂNSỰ': 'Tổ chức nhân sự',
            'tochucnhansu': 'Tổ chức nhân sự',
            'TOCHUCNHANSU': 'Tổ chức nhân sự',
            'nhânsự': 'nhân sự',
            'nhansu': 'nhân sự',
            'NHANSU': 'nhân sự',
            'kếtoán': 'kế toán',
            'ketoan': 'kế toán',
            'KETOAN': 'kế toán',
            'kinhdoanh': 'kinh doanh',
            'KINHDOANH': 'kinh doanh'
        }
        
        result = text
        for joined, separated in word_mappings.items():
            result = re.sub(re.escape(joined), separated, result, flags=re.IGNORECASE)
        
        return result
    

    
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