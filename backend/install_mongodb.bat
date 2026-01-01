@echo off
echo ================================================================================
echo MongoDB Local Installation Helper
echo ================================================================================
echo.
echo This script will help you set up MongoDB locally to avoid SSL/TLS issues.
echo.
echo OPTION 1: Install MongoDB Community Server
echo ----------------------------------------
echo 1. Download MongoDB Community Server:
echo    https://www.mongodb.com/try/download/community
echo.
echo 2. Run the installer (use default settings)
echo.
echo 3. After installation, MongoDB will run as a Windows Service automatically
echo.
echo.
echo OPTION 2: Install via Chocolatey (if you have Chocolatey)
echo --------------------------------------------------------
echo    choco install mongodb
echo.
echo.
echo OPTION 3: Use Docker (if you have Docker Desktop)
echo -------------------------------------------------
echo    docker run -d -p 27017:27017 --name mongodb mongo:latest
echo.
echo.
echo ================================================================================
echo After Installation:
echo ================================================================================
echo.
echo 1. Your .env file is already configured for local MongoDB:
echo    MONGODB_URL=mongodb://localhost:27017
echo.
echo 2. Start your backend:
echo    python main.py
echo.
echo 3. MongoDB will be running on localhost:27017 (no SSL required!)
echo.
echo ================================================================================
echo.
pause
