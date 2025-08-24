import requests
import base64
import json
from PIL import Image
import io

# URL của API
API_BASE_URL = "http://localhost:5000"

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_detect_with_file():
    """Test detect với file upload"""
    print("Testing detect with file upload...")
    
    # Sử dụng hình ảnh mẫu
    image_path = "images/img1.jpg"
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(f"{API_BASE_URL}/detect", files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_detect_with_base64():
    """Test detect với base64"""
    print("Testing detect with base64...")
    
    # Đọc và encode hình ảnh thành base64
    image_path = "images/img1.jpg"
    with open(image_path, 'rb') as f:
        image_data = f.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
    
    # Gửi request
    data = {'image': base64_image}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{API_BASE_URL}/detect_base64", json=data, headers=headers)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {result}")
    
    # Kiểm tra thông tin khoảng cách
    if 'distance_info' in result:
        print("Distance estimation results:")
        for obj in result['distance_info']:
            print(f"  Object {obj['object_id']}: {obj['position']}")
    print()

def test_config():
    """Test config endpoint"""
    print("Testing config...")
    
    # Get config
    response = requests.get(f"{API_BASE_URL}/config")
    print(f"Get config - Status: {response.status_code}")
    print(f"Get config - Response: {response.json()}")
    print()
    
    # Set config
    config_data = {
        "account_sid": "test_sid",
        "auth_token": "test_token",
        "from_": "+1234567890",
        "to_": "+0987654321"
    }
    response = requests.post(f"{API_BASE_URL}/config", json=config_data)
    print(f"Set config - Status: {response.status_code}")
    print(f"Set config - Response: {response.json()}")
    print()

def test_calibration():
    """Test calibration endpoint"""
    print("Testing calibration...")
    
    # Test auto calibration
    calibration_data = {
        "reference_distance_cm": 100,
        "reference_width_cm": 50,
        "reference_width_pixels": 200
    }
    response = requests.post(f"{API_BASE_URL}/calibrate_auto", json=calibration_data)
    print(f"Auto calibration - Status: {response.status_code}")
    print(f"Auto calibration - Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("=== Testing Drowning Detection API ===\n")
    
    try:
        test_health()
        test_calibration()  # Calibrate trước khi test detect
        test_detect_with_file()
        test_detect_with_base64()
        test_config()
        
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Make sure the API server is running on localhost:5000")
    except Exception as e:
        print(f"Error: {e}") 