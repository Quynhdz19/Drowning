@echo off
echo 🌊 Drowning Detection API Setup
echo ================================

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✅ Python found

REM Kiểm tra pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is not installed. Please install pip.
    pause
    exit /b 1
)

echo ✅ pip found

REM Kiểm tra file model
if not exist "best.pt" (
    echo ❌ Model file 'best.pt' not found!
    echo Please make sure the model file exists in the current directory.
    pause
    exit /b 1
)

echo ✅ Model file 'best.pt' found

REM Tạo virtual environment nếu chưa có
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Kích hoạt virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Cài đặt dependencies
echo 📥 Installing dependencies...
pip install -r requirements_api.txt

REM Kiểm tra cài đặt
echo 🔍 Checking installation...
python -c "import flask, ultralytics, cv2, PIL; print('✅ All dependencies installed successfully')"

echo.
echo 🚀 Starting API server...
echo API will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Chạy API
python run_api.py --debug

pause 