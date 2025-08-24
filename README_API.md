# Drowning Detection API

API để detect tình trạng đuối nước từ hình ảnh camera, được thiết kế để tích hợp với vi mạch.

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements_api.txt
```

2. Đảm bảo file model `best.pt` có trong thư mục gốc.

## Chạy API

```bash
python api.py
```

API sẽ chạy trên `http://localhost:5000`

## Endpoints

### 1. Health Check
```
GET /health
```
Kiểm tra trạng thái API và model.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": 1234567890.123
}
```

### 2. Detect Drowning (File Upload)
```
POST /detect
Content-Type: multipart/form-data
```

**Parameters:**
- `image`: File hình ảnh (jpg, png, etc.)
- `confidence` (query param): Ngưỡng confidence (0.0-1.0, default: 0.25)

**Response:**
```json
{
  "success": true,
  "detected_objects": 1,
  "classes": [0],
  "alert_triggered": false,
  "confidence": 0.25,
  "timestamp": 1234567890.123
}
```

### 3. Detect Drowning (Base64)
```
POST /detect_base64
Content-Type: application/json
```

**Request Body:**
```json
{
  "image": "base64_encoded_image_string"
}
```

**Parameters:**
- `confidence` (query param): Ngưỡng confidence (0.0-1.0, default: 0.25)
- `estimate_distance` (query param): Có ước tính khoảng cách hay không (true/false, default: true)

**Response with Distance:**
```json
{
  "success": true,
  "detected_objects": 1,
  "classes": [0],
  "alert_triggered": false,
  "confidence": 0.25,
  "timestamp": 1234567890.123,
  "distance_estimation_enabled": true,
  "distance_info": [
    {
      "object_id": 0,
      "class_id": 0,
      "confidence": 0.85,
      "bbox": [100, 150, 200, 300],
      "distance_cm": 250.5,
      "distance_m": 2.51,
      "center_x": 150.0,
      "center_y": 225.0,
      "angle_x_degrees": 5.2,
      "angle_y_degrees": -2.1,
      "position": "close (2.5m), center center"
    }
  ]
}
```

### 4. Calibrate Camera
```
POST /calibrate_auto
Content-Type: application/json
```

**Request Body:**
```json
{
  "reference_distance_cm": 100,
  "reference_width_cm": 50,
  "reference_width_pixels": 200
}
```

**Response:**
```json
{
  "success": true,
  "message": "Camera calibrated successfully",
  "focal_length": 400.0,
  "reference_width_pixels": 200
}
```

### 5. Rescue Coordinates
```
POST /rescue_coordinates
Content-Type: application/json
```

**Request Body:**
```json
{
  "distance_info": [
    {
      "object_id": 0,
      "class_id": 0,
      "confidence": 0.85,
      "distance_m": 15.5,
      "angle_x_degrees": 10.2,
      "angle_y_degrees": -5.1
    }
  ],
  "water_level": 0.0,
  "current_direction": 45.0,
  "current_speed": 0.5,
  "camera_height": 5.0,
  "camera_angle": 0.0
}
```

**Response:**
```json
{
  "success": true,
  "rescue_targets": [
    {
      "object_id": 0,
      "class_id": 0,
      "confidence": 0.85,
      "coordinates": {
        "x_m": 12.5,
        "y_m": 8.2,
        "z_m": -2.1,
        "distance_m": 14.8
      },
      "control": {
        "target_angle_degrees": 56.8,
        "target_angle_radians": 0.991,
        "speed_mps": 3.5,
        "estimated_time_seconds": 4.2
      },
      "urgency": {
        "level": "HIGH",
        "priority": 2,
        "description": "Người gặp nạn ở gần - Cần cứu hộ nhanh chóng"
      },
      "commands": {
        "command_type": "RESCUE_MISSION",
        "target_coordinates": {
          "x": 12.5,
          "y": 8.2,
          "z": -2.1
        },
        "movement": {
          "heading": 56.8,
          "speed": 3.5,
          "depth_mode": "DIVE_SHALLOW"
        },
        "mission": {
          "priority": "HIGH",
          "estimated_duration": 4.2,
          "auto_return": true,
          "emergency_contact": true
        }
      }
    }
  ],
  "total_targets": 1,
  "highest_priority": "HIGH"
}
```

### 6. Simple Rescue Commands
```
POST /rescue_commands
Content-Type: application/json
```

**Request Body:**
```json
{
  "distance_m": 15.5,
  "angle_x_degrees": 10.2,
  "angle_y_degrees": -5.1
}
```

### 7. Configuration
```
GET /config
POST /config
```

**GET Response:**
```json
{
  "account_sid": "your_twilio_sid",
  "auth_token": "your_twilio_token",
  "from_": "+1234567890",
  "to_": "+0987654321",
  "imgbb_api": "your_imgbb_key",
  "alertmsg": "Drowning Alert!"
}
```

**POST Request Body:**
```json
{
  "account_sid": "new_sid",
  "auth_token": "new_token",
  "from_": "+1234567890",
  "to_": "+0987654321"
}
```

## Ước tính Khoảng cách

API hỗ trợ ước tính khoảng cách từ camera đến đối tượng được detect. Để sử dụng tính năng này:

### 1. Calibrate Camera
Trước khi sử dụng, cần calibrate camera để có thông số chính xác:

```python
import requests

# Calibrate với thông số cố định
calibration_data = {
    "reference_distance_cm": 100,  # Khoảng cách thực tế đến reference object
    "reference_width_cm": 50,      # Chiều rộng thực tế của reference object
    "reference_width_pixels": 200  # Chiều rộng reference object trong ảnh (pixel)
}

response = requests.post("http://localhost:5000/calibrate_auto", json=calibration_data)
print(response.json())
```

### 2. Cách tính khoảng cách
- **Dựa trên chiều rộng**: Sử dụng chiều rộng của đối tượng trong ảnh
- **Dựa trên chiều cao**: Sử dụng chiều cao của người (mặc định 170cm)
- **Vị trí trung tâm**: Tính góc lệch từ trung tâm ảnh

### 3. Thông tin trả về
- `distance_cm`: Khoảng cách tính bằng cm
- `distance_m`: Khoảng cách tính bằng mét
- `angle_x_degrees`: Góc lệch theo trục X
- `angle_y_degrees`: Góc lệch theo trục Y
- `position`: Mô tả vị trí (ví dụ: "close (2.5m), center center")

## Hệ thống Phao Cứu hộ Tự động

API hỗ trợ tính toán tọa độ chính xác cho phao cứu hộ tự động. Phao sẽ nhận tọa độ và tự động điều khiển đến vị trí người gặp nạn.

### Cách hoạt động:

1. **Camera detect** → Gửi hình ảnh lên API
2. **API tính toán** → Tọa độ 3D + lệnh điều khiển
3. **Phao nhận lệnh** → Tự động di chuyển đến target
4. **Thực hiện cứu hộ** → Triển khai thiết bị cứu hộ
5. **Trở về** → Tự động về vị trí ban đầu

### Thông tin điều khiển phao:

- **Tọa độ 3D**: X, Y, Z (mét)
- **Hướng di chuyển**: Heading (độ)
- **Tốc độ**: Speed (m/s)
- **Độ sâu**: Depth mode (SURFACE_LEVEL, DIVE_SHALLOW, DIVE_DEEP, FLOAT_HIGH)
- **Mức độ ưu tiên**: CRITICAL, HIGH, MEDIUM, LOW

### Example Python cho phao:

```python
import requests

# Lấy tọa độ cứu hộ
distance_info = [
    {
        "object_id": 0,
        "class_id": 0,
        "distance_m": 15.5,
        "angle_x_degrees": 10.2,
        "angle_y_degrees": -5.1
    }
]

response = requests.post("http://localhost:5000/rescue_coordinates", 
                        json={"distance_info": distance_info})

if response.status_code == 200:
    data = response.json()
    target = data['rescue_targets'][0]
    
    # Lệnh điều khiển phao
    commands = target['commands']
    print(f"Move to: X={commands['target_coordinates']['x']}m")
    print(f"         Y={commands['target_coordinates']['y']}m")
    print(f"         Z={commands['target_coordinates']['z']}m")
    print(f"Heading: {commands['movement']['heading']}°")
    print(f"Speed: {commands['movement']['speed']} m/s")
    print(f"Priority: {commands['mission']['priority']}")
```

### Chạy example phao:

```bash
python rescue_buoy_example.py
```

## Sử dụng với Vi mạch

### Arduino/ESP32 Example (C++)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <base64.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* apiUrl = "http://YOUR_SERVER_IP:5000/detect_base64";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  // Chụp ảnh từ camera
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  
  // Encode base64
  String base64Image = base64::encode(fb->buf, fb->len);
  
  // Gửi request
  HTTPClient http;
  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");
  
  String jsonData = "{\"image\":\"" + base64Image + "\"}";
  int httpResponseCode = http.POST(jsonData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Response: " + response);
    
    // Parse JSON response
    // Kiểm tra alert_triggered
  }
  
  http.end();
  esp_camera_fb_return(fb);
  
  delay(5000); // Chụp ảnh mỗi 5 giây
}
```

### Python Example (Raspberry Pi)

```python
import requests
import base64
import cv2
import time

API_URL = "http://YOUR_SERVER_IP:5000/detect_base64"

def capture_and_detect():
    # Chụp ảnh từ camera
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Failed to capture image")
        return
    
    # Encode base64
    _, buffer = cv2.imencode('.jpg', frame)
    base64_image = base64.b64encode(buffer).decode('utf-8')
    
    # Gửi request
    data = {'image': base64_image}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(API_URL, json=data, headers=headers)
        result = response.json()
        
        print(f"Detected objects: {result['detected_objects']}")
        print(f"Classes: {result['classes']}")
        print(f"Alert triggered: {result['alert_triggered']}")
        
        # Hiển thị thông tin khoảng cách
        if result.get('distance_estimation_enabled') and 'distance_info' in result:
            print("Distance information:")
            for obj in result['distance_info']:
                print(f"  Object {obj['object_id']}: {obj['position']}")
                print(f"    Distance: {obj['distance_m']:.2f}m")
                print(f"    Angle: {obj['angle_x_degrees']:.1f}° horizontal, {obj['angle_y_degrees']:.1f}° vertical")
        
    except Exception as e:
        print(f"Error: {e}")

# Chạy liên tục
while True:
    capture_and_detect()
    time.sleep(5)
```

## Logic Cảnh báo

API sẽ tự động gửi cảnh báo khi:
1. Detect được class 0 (drowning) trong ít nhất 5 frame liên tiếp
2. Class 0 xuất hiện nhiều nhất trong 10 giây gần nhất
3. Chưa gửi cảnh báo trong 30 giây trước đó (cooldown)

## Test API

Chạy file test để kiểm tra API:

```bash
python test_api.py
```

## Lưu ý

- API hỗ trợ CORS để vi mạch có thể gọi từ domain khác
- Hình ảnh được lưu tạm thời trong thư mục `runs/detect/`
- Cần cấu hình Twilio để gửi SMS cảnh báo
- Có thể điều chỉnh ngưỡng confidence và thời gian cooldown trong code 