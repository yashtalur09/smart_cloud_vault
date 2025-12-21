# SmartCloud Vault - Quick Setup Guide

## ⚡ Quick Start (5 Minutes)

### Step 1: Prerequisites
- ✅ Python 3.9 or higher installed
- ✅ Node.js 16 or higher installed  
- ✅ MongoDB installed and running

### Step 2: Install Backend Dependencies

```bash
cd c:\cloud_el\smartcloud-vault\backend

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Setup environment
copy .env.example .env
```

### Step 3: Install Frontend Dependencies

```bash
cd ..\frontend

# Install packages
npm install
```

### Step 4: Start MongoDB

**Windows:** MongoDB should already be running as a service. If not:
```bash
# Check if running
sc query MongoDB

# Start if needed
net start MongoDB
```

**Linux/Mac:**
```bash
mongod --dbpath /path/to/data
```

### Step 5: Start the Application

**Terminal 1 - Backend:**
```bash
cd c:\cloud_el\smartcloud-vault\backend
venv\Scripts\activate
python main.py
```

You should see:
```
INFO - Starting SmartCloud Vault...
INFO - Connected to MongoDB: smartcloud_vault
INFO - Loading AI models (this may take a few minutes)...
INFO - AI models loaded successfully
INFO - Application startup complete.
INFO - Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd c:\cloud_el\smartcloud-vault\frontend
npm run dev
```

You should see:
```
VITE ready in X ms

➜  Local:   http://localhost:5173/
```

### Step 6: Access the Application

Open your browser and go to:
- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

---

## 🧪 Test the Application

### Upload a Sample File

1. Go to http://localhost:5173
2. Enter company name: "Acme Corp"
3. Select department: "HR"
4. Choose file: `docs/sample_files/sample_hr.txt`
5. Click "Upload & Scan"
6. Wait for scan to complete
7. View results showing:
   - Classification: **Restricted**
   - Detections: Names, emails, phone, SSN

### Protect the File

Click one of the protection buttons:
- "Mask Sensitive Data" - Replaces sensitive info with [REDACTED]
- "Encrypt File" - Encrypts the entire file
- "Mask & Encrypt" - Both protections

### View Analytics

1. Click "Dashboard" in navigation
2. Select "Acme Corp" from dropdown
3. View:
   - Total files: 1
   - Risk score
   - Classification chart
   - Department table

### Generate Report

1. On Dashboard, click "Download Report"
2. Wait for generation
3. PDF will download automatically
4. Open to see professional compliance report

### Get Recommendations

1. Click "Recommendations" in navigation
2. Select "Acme Corp"
3. Click "Generate New"
4. View AI-generated security policy recommendations

---

## 🔧 Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Error:** `Failed to connect to MongoDB`
```bash
# Check if MongoDB is running
sc query MongoDB  # Windows
mongod --version  # Linux/Mac

# Start MongoDB
net start MongoDB  # Windows
mongod --dbpath /data/db  # Linux/Mac
```

**Error:** `spaCy model not found`
```bash
python -m spacy download en_core_web_sm
```

### Frontend won't start

**Error:** `Cannot find module`
```bash
# Delete node_modules and reinstall
rm -rf node_modules
npm install
```

**Error:** `Port 5173 already in use`
```bash
# Kill process on port or change port in vite.config.js
```

### CORS Errors

If you see CORS errors in browser console:

1. Check that backend is running on port 8000
2. Verify `.env` has: `CORS_ORIGINS=http://localhost:5173`
3. Restart backend

### AI Models Taking Too Long

On first run, models download from internet:
- spaCy model: ~15MB
- HuggingFace model: ~500MB

This only happens once. Subsequent starts are fast.

---

## 📊 Verify Everything Works

Run this checklist:

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:5173
- [ ] Can upload a file
- [ ] Scan completes and shows results
- [ ] Classification appears
- [ ] Can apply protection
- [ ] Dashboard loads analytics
- [ ] Can download PDF report
- [ ] Recommendations page works

---

## 🎯 Next Steps

Once setup is complete:

1. **Try all sample files** in `docs/sample_files/`
2. **Upload your own files** to test detection
3. **Explore the API** at http://localhost:8000/docs
4. **Generate reports** for different companies/departments
5. **Review recommendations** for security insights

---

## 📞 Need Help?

- Check the main [README.md](../README.md) for detailed documentation
- Review API docs at http://localhost:8000/docs
- Check MongoDB logs for database issues
- View browser console for frontend errors
- Check backend terminal for API errors

---

## 🚀 Production Deployment Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=False`
- [ ] Configure MongoDB authentication
- [ ] Set up proper CORS origins
- [ ] Use environment-specific `.env` files
- [ ] Set up file size limits
- [ ] Configure backup strategy
- [ ] Set up monitoring/logging
- [ ] Use production WSGI server (gunicorn/uvicorn workers)
- [ ] Set up SSL/TLS
- [ ] Configure firewall rules

---

**You're all set! 🎉**

Start protecting your sensitive data with SmartCloud Vault!
