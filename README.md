# 🔐 SmartCloud Vault

**Sensitive Data Detection and Management System**

A comprehensive, AI-powered local application for detecting, classifying, and protecting sensitive data in files. Features advanced NLP-based detection, automated classification, data protection, compliance reporting, and security policy recommendations.

---

## ✨ Features

### Core Functionality
- **🤖 AI-Powered Detection**: Dual-layer detection using regex patterns and ML models (spaCy + HuggingFace Transformers)
- **🖼️ Image OCR Support**: Extract text from images (JPG, JPEG, PNG) using Tesseract OCR
- **📊 Automatic Classification**: Files categorized into Public, Internal, Confidential, or Restricted levels
- **🛡️ Data Protection**: Masking and encryption capabilities for sensitive information
- **📧 Email-Based Access Control**: Original files for uploaders, masked files for others
- **☁️ AWS S3 Storage**: Dual-bucket cloud storage with local fallback (NEW!)
- **📈 Advanced Analytics**: Company and department-level data analysis with risk scoring
- **💡 AI Recommendations**: Intelligent security policy suggestions based on data patterns
- **📄 Compliance Reports**: Professional PDF reports with charts, tables, and actionable insights

### Storage Options
- **Local Storage**: Traditional filesystem storage (default)
- **AWS S3**: Scalable cloud storage with dual-bucket architecture
  - Separate buckets for original and masked documents
  - Server-side encryption (AES-256)
  - Company-based file organization
  - Seamless switching between local and cloud

### Detection Capabilities
- **Regex-Based**:
  - Email addresses
  - Phone numbers (multiple formats)
  - Credit card numbers
  - Social Security Numbers (SSN)
  - National IDs
  - Password keywords

- **AI-Based (NLP)**:
  - Person names (PII)
  - Organizations
  - Locations
  - Custom entity recognition

---

## 🏗️ Architecture

```
smartcloud-vault/
├── backend/                 # FastAPI Backend
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration management
│   ├── api/                # API endpoints
│   │   ├── upload.py       # File upload & scanning
│   │   ├── protection.py   # Data protection
│   │   ├── analysis.py     # Analytics
│   │   ├── recommendations.py
│   │   └── reports.py      # PDF generation
│   ├── ai_engine/          # AI/ML modules
│   │   ├── detector.py     # Sensitive data detection
│   │   └── classifier.py   # File classification
│   ├── analysis/           # Analysis engine
│   ├── recommendations/    # Policy engine
│   ├── reports/            # PDF report generation
│   ├── storage/            # Data storage
│   │   ├── database.py     # MongoDB operations
│   │   ├── file_storage.py # Local file management
│   │   ├── storage_interface.py  # Storage abstraction
│   │   ├── local_storage.py      # Local storage backend
│   │   ├── s3_storage.py         # AWS S3 backend (NEW!)
│   │   └── storage_factory.py    # Storage initialization
│   ├── models/             # Pydantic schemas
│   └── utils/              # Helper utilities
│
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── pages/         # Route pages
│   │   │   ├── Upload.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── Recommendations.jsx
│   │   ├── services/      # API client
│   │   └── App.jsx        # Main component
│   └── package.json
│
└── docs/
    └── sample_files/      # Test files
```

---

## 📋 Prerequisites

### Required
- **Python 3.9+**
- **Node.js 16+** and npm
- **MongoDB 5.0+** (running locally)

### Installation

#### MongoDB
**Windows:**
```bash
# Download from: https://www.mongodb.com/try/download/community
# Install and ensure MongoDB service is running
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install mongodb

# Mac
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Tesseract OCR (Required for Image Upload Feature)

**Windows:**
1. Download the Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (recommended: `tesseract-ocr-w64-setup-5.3.x.exe`)
3. During installation, note the installation path (default: `C:\Program Files\Tesseract-OCR`)
4. Add Tesseract to your system PATH:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click "Edit"
   - Click "New" and add: `C:\Program Files\Tesseract-OCR`
   - Click OK to save
5. Verify installation:
   ```bash
   tesseract --version
   ```

**Alternative (if PATH not set):**
Set the `TESSERACT_CMD` environment variable in your `.env` file:
```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Verify
tesseract --version
```

**Mac:**
```bash
brew install tesseract

# Verify
tesseract --version
```

---

## 🚀 Installation & Setup

### 1. Clone/Navigate to Project
```bash
cd c:\cloud_el\smartcloud-vault
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Copy environment file
copy .env.example .env

# Edit .env if needed (MongoDB connection, etc.)
```

**Optional: Enable AWS S3 Storage**

To use cloud storage instead of local files:

```bash
# See QUICK_START_S3.md for complete instructions

# Edit .env:
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
S3_ORIGINAL_BUCKET=smartcloud-vault-original
S3_MASKED_BUCKET=smartcloud-vault-masked
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

---

## 🎯 Running the Application

### Start MongoDB
Ensure MongoDB is running:
```bash
# Windows: Already running as service
# Linux/Mac:
mongod --dbpath /path/to/data
```

### Start Backend (Terminal 1)
```bash
cd backend
venv\Scripts\activate  # Activate virtual environment
python main.py
```
Backend will start at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
Frontend will start at: **http://localhost:5173**

---

## 📖 Usage Guide

### 1. Upload Files
1. Navigate to the Upload page
2. Enter company name
3. Select department (HR, Finance, Sales, IT, etc.)
4. Enter your email address (required for access control)
5. Choose a file:
   - **Text files**: .txt, .csv, .pdf, .docx
   - **Images**: .jpg, .jpeg, .png (OCR text extraction)
6. Click "Upload & Scan"
7. View detection results and classification
8. **For images**: Review the extracted OCR text preview

### 2. Protect Sensitive Data
After scanning:
- **Mask Sensitive Data**: Replace detected items with [REDACTED]
- **Encrypt File**: Apply encryption to the entire file
- **Mask & Encrypt**: Combined protection

### 3. View Analytics
1. Go to Dashboard
2. Select a company
3. View:
   - Total files and risk score
   - Classification distribution (pie chart)
   - Department breakdown (bar chart)
   - Department risk table
   - Top sensitive data types

### 4. Generate Reports
1. From Dashboard, click "Download Report"
2. PDF report includes:
   - Executive summary
   - Company overview
   - Department risk analysis
   - Security recommendations
   - Compliance readiness score

### 5. Security Recommendations
1. Navigate to Recommendations page
2. Select company
3. Click "Generate New" to create recommendations
4. Filter by priority (High/Medium/Low)
5. Review actionable security policies

### 6. Image OCR Feature
**Upload images containing sensitive data:**
1. Select an image file (.jpg, .jpeg, .png) during upload
2. System automatically extracts text using OCR
3. View extracted text preview immediately after upload
4. OCR text is processed for sensitive data detection
5. Two text files are created:
   - **Original**: Full OCR extracted text (accessible only to uploader)
   - **Masked**: Sensitive data masked (accessible to others)

**What gets masked in OCR text:**
- ✅ **Masked**: Phone numbers, bank details, credit cards, SSN, passwords
- ❌ **Preserved**: Names, email addresses, organization names

### 7. File Access Control (Email-Based)
**How it works:**
- When you upload a file, provide your email address
- **Your email = Original file**: Full, unmasked content
- **Different email = Masked file**: Sensitive data redacted

**Example:**
```
Uploader: john@company.com
File contains: Name: John, Email: john@company.com, Phone: 555-1234

Access with john@company.com → Full file (all data visible)
Access with mary@company.com → Masked file (Phone: [MASKED-PHONE])
```

---

## 🧪 Testing with Sample Files

Sample files are provided in `docs/sample_files/`:

| File | Department | Contains | Expected Classification |
|------|------------|----------|------------------------|
| sample_hr.txt | HR | Names, emails, phone, SSN | Restricted |
| sample_finance.txt | Finance | Credit cards, SSN | Restricted |
| sample_sales.txt | Sales | Emails, phone, business data | Confidential |
| sample_public.txt | IT | No sensitive data | Public |

**Test Workflow:**
1. Upload each sample file with appropriate company/department
2. Observe AI detection results
3. Check classification accuracy
4. Apply protection
5. View analytics on Dashboard
6. Generate recommendations
7. Download compliance report

---

## 🔌 API Endpoints

### File Management
- `POST /api/upload` - Upload and scan file
- `GET /api/upload/files` - List files
- `GET /api/upload/files/{file_id}` - Get file details

### Protection
- `POST /api/protect/{file_id}` - Protect file (mask/encrypt)
- `GET /api/protect/{file_id}/download` - Download protected file

### Analysis
- `GET /api/analysis/company?company={name}` - Company analysis
- `GET /api/analysis/department?company={name}&department={dept}` - Department analysis
- `GET /api/analysis/overview` - System overview
- `GET /api/analysis/companies` - List all companies

### Recommendations
- `POST /api/recommendations/generate?company={name}` - Generate recommendations
- `GET /api/recommendations?company={name}` - Get recommendations

### Reports
- `POST /api/reports/generate?company={name}` - Generate PDF report
- `GET /api/reports/download/{report_id}` - Download report
- `GET /api/reports/list` - List generated reports

Full API documentation: **http://localhost:8000/docs**

---

## 🛠️ Configuration

### Environment Variables (.env)

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=smartcloud_vault

# JWT (for future auth)
SECRET_KEY=your-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
UPLOAD_DIR=./storage/uploads
PROTECTED_DIR=./storage/protected
TEMP_DIR=./storage/temp

# AI Models
SPACY_MODEL=en_core_web_sm
HUGGINGFACE_MODEL=dslim/bert-base-NER

# Application
DEBUG=True
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
MAX_FILE_SIZE=10485760  # 10MB
```

---

## 📊 Database Schema

### Collections

**files**
- file_id, original_filename, company, department
- classification, scan_completed, is_protected
- file_size, upload_date, scan_date
- detections_count, classification_score

**detections**
- file_id, detections (array), scan_date

**analysis**
- company, department, type (company/department)
- statistics, risk_score, timestamp

**recommendations**
- id, company, department, priority
- title, description, rationale, action_items
- created_date

**reports**
- report_id, company, department
- file_path, generated_date, file_size

---

## 🎨 Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB (Motor async driver)
- **AI/NLP**: spaCy, HuggingFace Transformers, PyTorch
- **OCR**: Tesseract OCR, pytesseract, Pillow
- **File Processing**: PyPDF2, python-docx, pandas
- **Security**: cryptography (Fernet encryption)
- **Reports**: ReportLab, Pillow

### Frontend
- **Framework**: React 18
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP**: Axios

---

## 🔧 Troubleshooting

### MongoDB Connection Error
```
Solution: Ensure MongoDB is running
- Windows: Check Services (mongodb)
- Linux/Mac: mongod --dbpath /path/to/data
```

### AI Models Not Loading
```
Solution: Download models manually
python -m spacy download en_core_web_sm
```

### Port Already in Use
```
Backend (8000): Kill process or change port in main.py
Frontend (5173): Change port in vite.config.js
```

### CORS Errors
```
Solution: Check CORS_ORIGINS in .env includes frontend URL
```

### Tesseract OCR Not Found
```
Error: "Tesseract OCR not found"

Solutions:
1. Verify Tesseract is installed:
   tesseract --version

2. Add Tesseract to system PATH (Windows):
   - Add C:\Program Files\Tesseract-OCR to PATH
   - Restart terminal/IDE

3. Set TESSERACT_CMD in .env:
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

4. Restart backend after configuration changes
```

### Image Upload Not Working
```
Solution: 
- Ensure pytesseract is installed: pip install pytesseract
- Verify image format is supported (.jpg, .jpeg, .png)
- Check backend logs for OCR errors
```

### S3 Storage Issues
```
See AWS_S3_SETUP_GUIDE.md for complete troubleshooting

Quick fixes:
- Verify USE_S3_STORAGE=true in .env
- Check AWS credentials are set
- Ensure S3 buckets exist
- Run: python test_s3_integration.py
```

---

## 📚 Documentation

### Main Guides
- **[README.md](README.md)** - This file (overview and setup)
- **[QUICK_START_S3.md](QUICK_START_S3.md)** - 5-minute S3 setup guide

### AWS S3 Integration
- **[AWS_S3_SETUP_GUIDE.md](AWS_S3_SETUP_GUIDE.md)** - Complete S3 setup with screenshots
- **[S3_DEVELOPER_GUIDE.md](S3_DEVELOPER_GUIDE.md)** - Code examples and API reference
- **[S3_IMPLEMENTATION_SUMMARY.md](S3_IMPLEMENTATION_SUMMARY.md)** - Architecture and design decisions

### Other Documentation
- Check `/docs` folder for feature-specific guides
- API Docs: http://localhost:8000/docs (when backend is running)

---

## 🚧 Recent Updates

### v2.1 - AWS S3 Integration (Latest)
- ✅ Dual-bucket S3 storage architecture
- ✅ Seamless local/cloud storage switching
- ✅ Server-side encryption (AES-256)
- ✅ Company-based file organization
- ✅ Backward compatible with local storage
- ✅ Comprehensive setup documentation

### v2.0 - Context-Aware Intelligence
- Enhanced AI detection with government ID support
- Context-aware masking and classification
- Email-based access control
- OCR support for images

---

## 🚧 Future Enhancements

- [x] Cloud storage integration (AWS S3) ✅ **NEW!**
- [ ] Azure Blob Storage support
- [ ] Google Cloud Storage support
- [ ] User authentication & role-based access
- [ ] Real-time scanning dashboard
- [ ] Custom detection patterns
- [ ] Multi-language support
- [ ] Automated compliance workflows
- [ ] Integration with DLP systems
- [ ] Email notifications
- [ ] Audit trail & logging
- [ ] Advanced ML model fine-tuning

---

## 📝 License

This project is for educational and internal use.

---

## 👥 Support

For issues or questions:
1. Check API documentation: http://localhost:8000/docs
2. Review sample files in `docs/sample_files/`
3. Verify MongoDB connection
4. Check browser console and backend logs

---

## 🎯 Quick Start Commands

```bash
# Backend
cd backend
venv\Scripts\activate
python main.py

# Frontend (new terminal)
cd frontend
npm run dev

# Access application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

---

**Built with ❤️ using FastAPI, React, and AI**
