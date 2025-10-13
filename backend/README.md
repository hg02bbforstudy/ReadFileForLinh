# CV Reader Python Backend

## 🐍 Flask API for CV Processing

This is the Python backend for the CV Reader application, providing advanced document processing capabilities with high accuracy.

### ✨ Features

- **Advanced Text Extraction**: DOCX, PDF, and image processing
- **Smart Pattern Matching**: Vietnamese-aware regex patterns
- **OCR Support**: EasyOCR for image text extraction
- **Field Validation**: Confidence scoring and verification
- **CORS Enabled**: Works with frontend applications
- **Health Monitoring**: Health check endpoints

### 📦 Installation

1. **Clone and setup**:
```bash
git clone https://github.com/hg02bbforstudy/ReadFileForLinh.git
cd ReadFileForLinh/backend
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run locally**:
```bash
python app.py
```

The server will start on `http://localhost:5000`

### 🚀 Deployment Options

#### Option 1: Railway (Recommended)
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Select the `backend` folder
4. Deploy automatically

#### Option 2: Heroku
1. Install Heroku CLI
2. Create app: `heroku create your-cv-reader-api`
3. Deploy: `git subtree push --prefix backend heroku main`

#### Option 3: Render
1. Go to [render.com](https://render.com)
2. Connect GitHub repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app`

### 📋 API Endpoints

#### Health Check
```
GET /health
```

#### Process CV File
```
POST /process-cv
Content-Type: multipart/form-data
Body: file (DOCX or PDF)
```

#### Process Image with OCR
```
POST /process-image  
Content-Type: multipart/form-data
Body: image (JPG, PNG)
```

#### Verify Field
```
POST /verify-field
Content-Type: application/json
Body: {"field": "email", "value": "test@example.com", "rawContent": "..."}
```

#### Save CV Data
```
POST /save-cv
Content-Type: application/json
Body: {cv data object}
```

### 🔧 Environment Variables

- `PORT`: Server port (default: 5000)
- `FLASK_ENV`: Environment (production/development)

### 📊 Processing Capabilities

- **Text Extraction**: Advanced DOCX and PDF parsing
- **Pattern Recognition**: 11 CV fields with multiple patterns each
- **Confidence Scoring**: Smart confidence calculation
- **Field Validation**: Cross-field validation and verification
- **OCR Processing**: Image text extraction with Vietnamese support
- **Error Handling**: Comprehensive error handling and logging

### 🌐 Frontend Integration

Update your frontend to use the deployed backend URL:

```javascript
const API_BASE_URL = 'https://your-app.railway.app'; // Replace with your URL
```

### 🔒 Security Features

- CORS configuration for cross-origin requests
- File type validation
- Size limits and error handling
- Temporary file cleanup
- Input sanitization

### 📈 Performance

- Optimized text processing algorithms
- Efficient memory usage with temporary files
- Concurrent request handling
- Fast response times

### 🐛 Troubleshooting

1. **Import errors**: Ensure all dependencies are installed
2. **Memory issues**: Consider reducing file size limits
3. **OCR errors**: EasyOCR requires GPU support for best performance
4. **CORS issues**: Check CORS configuration

### 🚀 Quick Deploy Commands

```bash
# For Railway
railway login
railway link
railway up

# For Heroku  
heroku login
heroku create your-app-name
git subtree push --prefix backend heroku main

# For local testing
python app.py
```