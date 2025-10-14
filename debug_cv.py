import sys
import os
sys.path.append('backend')

# Import processing libraries
try:
    import docx2txt
    import PyPDF2
    import re
except ImportError as e:
    print(f"Error importing libraries: {e}")
    sys.exit(1)

def extract_docx_text(file_path):
    """Extract text from DOCX file"""
    try:
        text = docx2txt.process(file_path)
        return text
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return ""

def extract_pdf_text(file_path):
    """Extract text from PDF file"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- PAGE {page_num + 1} ---\n"
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def analyze_cv_structure(text, file_type):
    """Analyze CV structure and extract key information"""
    print(f"\n{'='*50}")
    print(f"ANALYZING {file_type.upper()} CONTENT")
    print(f"{'='*50}")
    
    # Print full text for manual analysis
    print("FULL TEXT CONTENT:")
    print("-" * 30)
    print(text[:2000])  # First 2000 characters
    if len(text) > 2000:
        print(f"\n... (truncated, total length: {len(text)} characters)")
    
    print("\n" + "="*50)
    print("FIELD ANALYSIS:")
    print("="*50)
    
    # Look for specific patterns
    patterns = {
        'name': [
            r'(?:họ\s*(?:và\s*)?tên|tên|name)\s*:?\s*([^\n\r]{2,50})',
            r'^([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]+(?:\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]*){1,3})'
        ],
        'email': [
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ],
        'phone': [
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
        'appliedPosition': [
            r'vị\s*trí\s*ứng\s*tuyển[\s\S]*?nơi\s*làm\s*việc([\s\S]*?)(?:I\.\s*THÔNG\s*TIN|$)',
            r'Vị\s*trí\s*ứng\s*tuyển[\s\S]*?Nơi\s*làm\s*việc([\s\S]*?)(?:I\.\s*THÔNG\s*TIN|$)'
        ]
    }
    
    for field_name, field_patterns in patterns.items():
        print(f"\n🔍 SEARCHING FOR: {field_name.upper()}")
        found = False
        
        for i, pattern in enumerate(field_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                found = True
                if len(match.groups()) > 0:
                    value = match.group(1).strip()
                    print(f"  ✅ Pattern {i+1}: '{value}'")
                    print(f"     Full match: '{match.group(0)[:100]}...'")
                else:
                    print(f"  ✅ Pattern {i+1}: '{match.group(0)[:100]}...'")
        
        if not found:
            print(f"  ❌ No matches found")

def main():
    docx_file = "Phạm Yến Linh.docx"
    pdf_file = "Phạm Yến Linh.pdf"
    
    print("CV STRUCTURE ANALYZER")
    print("====================")
    
    # Analyze DOCX
    if os.path.exists(docx_file):
        docx_text = extract_docx_text(docx_file)
        if docx_text:
            analyze_cv_structure(docx_text, "DOCX")
    
    # Analyze PDF
    if os.path.exists(pdf_file):
        pdf_text = extract_pdf_text(pdf_file)
        if pdf_text:
            analyze_cv_structure(pdf_text, "PDF")

if __name__ == "__main__":
    main()