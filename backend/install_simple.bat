@echo off
echo ========================================
echo SmartCloud Vault - Simple Installation
echo ========================================
echo.
echo Installing packages without strict version pinning...
echo This allows pip to find compatible versions for your Python.
echo.

echo [1/4] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/4] Installing core dependencies...
pip install fastapi uvicorn[standard] python-multipart pydantic pydantic-settings python-dotenv aiofiles

echo.
echo [3/4] Installing database and utilities...
pip install pymongo motor python-jose[cryptography] passlib[bcrypt] PyPDF2 python-docx cryptography reportlab Pillow

echo.
echo [4/4] Skipping AI packages (optional - app works without them)...
echo The app will use regex-only detection which is sufficient for most cases.

echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo Core features installed successfully.
echo The app will run with regex detection (no AI models needed).
echo.
echo Next steps:
echo 1. copy .env.example .env
echo 2. net start MongoDB
echo 3. python main.py
echo.
pause
