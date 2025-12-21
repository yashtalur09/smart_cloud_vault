@echo off
echo ========================================
echo SmartCloud Vault - Backend Installation
echo ========================================
echo.

echo [Step 1/9] Installing core web framework...
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 python-multipart==0.0.6 python-dotenv==1.0.0 aiofiles==23.2.1 --only-binary :all:
if errorlevel 1 goto error

echo.
echo [Step 2/9] Installing data validation...
pip install pydantic==2.4.2 pydantic-settings==2.0.3 --only-binary :all:
if errorlevel 1 goto error

echo.
echo [Step 3/9] Installing database driver...
pip install pymongo==4.6.1 motor==3.3.2 --only-binary :all:
if errorlevel 1 goto error

echo.
echo [Step 4/9] Installing authentication...
pip install python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 --only-binary :all:
if errorlevel 1 goto error

echo.
echo [Step 5/9] Installing file processors...
pip install PyPDF2==3.0.1 python-docx==1.1.0 --only-binary :all:
if errorlevel 1 goto error

echo.
echo [Step 6/9] Installing security...
pip install cryptography==41.0.7 --only-binary :all:
if errorlevel 1 goto error

echo.
echo [Step 7/9] Installing reporting...
pip install reportlab==4.0.9 Pillow --only-binary :all:
if errorlevel 1 goto error

echo.
echo [Step 8/9] Installing AI packages...
pip install torch --index-url https://download.pytorch.org/whl/cpu --only-binary :all:
if errorlevel 1 (
    echo WARNING: PyTorch installation failed. App will run without AI detection.
)

pip install transformers sentencepiece --only-binary :all:
if errorlevel 1 (
    echo WARNING: Transformers installation failed. App will run without transformer models.
)

pip install spacy --only-binary :all:
if errorlevel 1 (
    echo WARNING: spaCy installation failed. App will run with regex detection only.
    goto skip_spacy
)

echo.
echo [Step 9/9] Downloading spaCy model...
python -m spacy download en_core_web_sm
if errorlevel 1 (
    echo WARNING: spaCy model download failed. App will run with regex detection only.
)

:skip_spacy
echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo Some AI packages may have failed, but the app will work with regex detection.
echo.
echo Next steps:
echo 1. Start MongoDB: net start MongoDB
echo 2. Copy environment file: copy .env.example .env
echo 3. Start backend: python main.py
echo.
goto end

:error
echo.
echo ========================================
echo ❌ Installation Failed!
echo ========================================
echo.
echo The installation stopped at an error.
echo Please share the error message above.
echo.
exit /b 1

:end
