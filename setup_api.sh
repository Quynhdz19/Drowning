#!/bin/bash

echo "🌊 Drowning Detection API Setup"
echo "================================"

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Kiểm tra pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

echo "✅ pip3 found"

# Kiểm tra file model
if [ ! -f "best.pt" ]; then
    echo "❌ Model file 'best.pt' not found!"
    echo "Please make sure the model file exists in the current directory."
    exit 1
fi

echo "✅ Model file 'best.pt' found"

# Tạo virtual environment nếu chưa có
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Kích hoạt virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Cài đặt dependencies
echo "📥 Installing dependencies..."
pip install -r requirements_api.txt

# Kiểm tra cài đặt
echo "🔍 Checking installation..."
python3 -c "import flask, ultralytics, cv2, PIL; print('✅ All dependencies installed successfully')"

echo ""
echo "🚀 Starting API server..."
echo "API will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Chạy API
python3 run_api.py --debug 