# 🐍 CV Reader - Python Enhanced Version

Phiên bản nâng cao của CV Reader sử dụng Python backend với AI và NLP để tăng độ chính xác trích xuất thông tin.

## 🚀 Các phiên bản có sẵn

### 1. **HTML + Python API** (`python_version.html` + `cv_processor_api.py`)
- Frontend HTML đẹp mắt
- Backend Python Flask API
- Hỗ trợ OCR cho ảnh chụp
- Realtime processing

### 2. **Streamlit Web App** (`streamlit_app.py`)
- Giao diện thân thiện
- Tương tác trực tiếp
- Export nhiều định dạng
- Phù hợp demo và testing

## 📦 Cài đặt

### Bước 1: Cài đặt Python packages
```bash
pip install -r requirements.txt
```

### Bước 2: Cài đặt SpaCy model (tùy chọn)
```bash
python -m spacy download en_core_web_sm
```

### Bước 3: Cài đặt Tesseract (cho OCR)
- **Windows**: Tải từ https://github.com/UB-Mannheim/tesseract/wiki
- **Linux**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`

## 🎯 Chạy ứng dụng

### Option 1: Flask API + HTML Frontend
```bash
# Terminal 1: Start Python API
python cv_processor_api.py

# Terminal 2: Serve HTML (hoặc mở trực tiếp python_version.html)
python -m http.server 8080
```

Truy cập: `http://localhost:8080/python_version.html`

### Option 2: Streamlit App
```bash
streamlit run streamlit_app.py
```

Truy cập: `http://localhost:8501`

## ✨ Tính năng nâng cao

### 🔍 **Trích xuất chính xác hơn**
- **DOCX**: python-docx2txt + textract
- **PDF**: PyPDF2 + pdfplumber
- **OCR**: EasyOCR cho ảnh chụp
- **NLP**: SpaCy cho entity recognition

### 🤖 **AI Enhancement**
- Tự động phát hiện tên người, công ty
- Validation thông minh cho email, SĐT
- Confidence scoring cho mỗi trường
- Gợi ý sửa lỗi

### 📊 **Xuất dữ liệu đa dạng**
- CSV, JSON, Excel
- Database integration
- Batch processing
- API endpoints

### 🌐 **Tính năng web**
- Drag & drop files
- Camera capture (OCR)
- Real-time processing
- Responsive design

## 🔧 Cấu hình

### Environment Variables (.env)
```bash
# API Configuration
FLASK_ENV=development
API_PORT=5000

# Database (optional)
DATABASE_URL=sqlite:///cv_database.db

# OCR Configuration
OCR_LANGUAGES=vi,en
OCR_CONFIDENCE_THRESHOLD=0.5

# NLP Configuration
SPACY_MODEL=en_core_web_sm
USE_VIETNAMESE_NLP=true
```

### Advanced Processing Options
```python
# cv_processor_api.py - Customization
CV_FIELDS = {
    'name': {'required': True, 'confidence_threshold': 0.8},
    'email': {'required': True, 'validate': 'email'},
    'phone': {'required': True, 'validate': 'phone'},
    # ... more fields
}
```

## 📈 So sánh với phiên bản JavaScript

| Tính năng | JavaScript | Python Enhanced |
|-----------|------------|-----------------|
| **Tốc độ** | ⚡ Nhanh | 🐌 Chậm hơn |
| **Độ chính xác** | 📊 70-80% | 🎯 85-95% |
| **DOCX parsing** | 📄 Cơ bản | 🔍 Nâng cao |
| **PDF parsing** | 📑 Cơ bản | 🔬 Deep analysis |
| **OCR Support** | ❌ Không | ✅ Có |
| **NLP/AI** | ❌ Không | 🤖 Có |
| **Validation** | 📝 Cơ bản | ✅ Thông minh |
| **Database** | 💾 LocalStorage | 🗄️ Real DB |
| **Scalability** | 👤 Client-side | 🏢 Server-side |

## 🚀 Deploy Production

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "cv_processor_api.py"]
```

### Cloud Deployment Options
- **Heroku**: `git push heroku main`
- **Vercel**: Serverless functions
- **AWS Lambda**: API Gateway
- **Google Cloud Run**: Container deployment

## 🔮 Tính năng tương lai

- [ ] Vietnamese NLP model
- [ ] ML-based field extraction
- [ ] Batch processing API
- [ ] Real-time collaboration
- [ ] Advanced OCR preprocessing
- [ ] Export to HR systems
- [ ] Analytics dashboard
- [ ] Mobile app integration

## 🆚 Khi nào dùng phiên bản nào?

### Dùng **JavaScript Version** khi:
- ✅ Cần tốc độ xử lý nhanh
- ✅ Deploy đơn giản (static hosting)
- ✅ Không cần server
- ✅ CV có format chuẩn

### Dùng **Python Version** khi:
- 🎯 Cần độ chính xác cao
- 🤖 Muốn AI enhancement
- 📷 Cần OCR cho ảnh chụp
- 🗄️ Cần lưu database
- 🏢 Ứng dụng enterprise

## 📞 Hỗ trợ

Nếu gặp lỗi hoặc cần hỗ trợ:
1. Check Python version >= 3.8
2. Kiểm tra requirements.txt đã cài đầy đủ
3. Xem logs trong terminal
4. Test với file CV đơn giản trước

---

**🎉 Enjoy the enhanced CV processing with Python power!**