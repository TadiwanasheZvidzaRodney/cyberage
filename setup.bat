@echo off
echo ===================================================
echo      CyberAge Local Development Setup Script
echo ===================================================
echo.

echo [1/4] Checking prerequisites...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.10+.
    exit /b 1
)
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Node.js/npm is not installed or not in PATH. Please install Node.js 18+.
    exit /b 1
)
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Docker is not installed or not in PATH. Please install Docker Desktop.
    exit /b 1
)

echo.
echo [2/4] Setting up Backend...
cd backend
if not exist "venv\" (
    echo Creating Python virtual environment...
    python -m venv venv
)
echo Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Generating Prisma Client...
prisma generate
prisma db push

if not exist ".env" (
    echo Creating template .env file...
    echo GROQ_API_KEY=your_key_here > .env
    echo Please remember to update backend/.env with your actual GROQ_API_KEY.
)
cd ..

echo.
echo [3/4] Building Docker Sandbox Images...
cd backend\tools\sandbox
echo Building cyberage-dns-enum...
docker build -t cyberage-dns-enum -f Dockerfile.dns .
echo Building cyberage-nmap...
docker build -t cyberage-nmap -f Dockerfile.nmap .
echo Building cyberage-nuclei...
docker build -t cyberage-nuclei -f Dockerfile.nuclei .
cd ..\..\..

echo.
echo [4/4] Setting up Frontend...
cd frontend
echo Installing frontend dependencies...
call npm install
cd ..

echo.
echo ===================================================
echo Setup Complete! 🚀
echo ===================================================
echo To run the platform:
echo 1. Update backend/.env with your GROQ_API_KEY
echo 2. Terminal 1: cd backend ^& venv\Scripts\activate ^& uvicorn main:app --reload
echo 3. Terminal 2: cd frontend ^& npm run dev
echo ===================================================
pause
