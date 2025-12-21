# 🔐 SmartCloud Vault

**Sensitive Data Detection and Management System**

A comprehensive, AI-powered local application for detecting, classifying, and protecting sensitive data in files. Features advanced NLP-based detection, automated classification, data protection, compliance reporting, and security policy recommendations.

---

## ✨ Features

### Core Functionality
- **🤖 AI-Powered Detection**: Dual-layer detection using regex patterns and ML models (spaCy + HuggingFace Transformers)
- **📊 Automatic Classification**: Files categorized into Public, Internal, Confidential, or Restricted levels
- **🛡️ Data Protection**: Masking and encryption capabilities for sensitive information
- **📈 Advanced Analytics**: Company and department-level data analysis with risk scoring
- **💡 AI Recommendations**: Intelligent security policy suggestions based on data patterns
- **📄 Compliance Reports**: Professional PDF reports with charts, tables, and actionable insights

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
│   │   └── file_storage.py # Local file management
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
4. Choose a file (supports .txt, .csv, .pdf, .docx)
5. Click "Upload & Scan"
6. View detection results and classification

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

---

## 🚧 Future Enhancements

- [ ] Cloud storage integration (AWS S3, Azure Blob)
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
