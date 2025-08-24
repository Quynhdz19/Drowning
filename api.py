from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import io
from PIL import Image
import os
import time
from collections import Counter
import settings
from helper import load_model, send_message, autoplay_audio
from distance_estimator import DistanceEstimator, estimate_distances_from_yolo_results
from rescue_coordinates import RescueCoordinates

app = Flask(__name__)
CORS(app)  # Cho phép CORS để vi mạch có thể gọi API

# Load model khi khởi động
model_path = 'best.pt'
try:
    model = load_model(model_path)
    print("Model loaded successfully!")
except Exception as ex:
    print(f"Error loading model: {ex}")
    model = None

# Khởi tạo distance estimator
distance_estimator = DistanceEstimator(known_width=50)  # Chiều rộng người trung bình ~50cm

# Khởi tạo rescue coordinates calculator
rescue_calculator = RescueCoordinates(camera_height=5.0, camera_angle=0.0)

# Biến để theo dõi thời gian và kết quả detect
detection_history = []
last_alert_time = 0
ALERT_COOLDOWN = 30  # Thời gian chờ giữa các cảnh báo (giây)

def detect_drowning(image, confidence=0.25, estimate_distance=True):
    """
    Detect drowning trong hình ảnh
    
    Args:
        image: PIL Image hoặc numpy array
        confidence: Ngưỡng confidence
        estimate_distance: Có ước tính khoảng cách hay không
    
    Returns:
        dict: Kết quả detect
    """
    global detection_history, last_alert_time, distance_estimator
    
    if model is None:
        return {"error": "Model not loaded"}
    
    try:
        # Xóa thư mục runs cũ
        directory = "runs/detect"
        if os.path.exists(directory):
            for entry in os.listdir(directory):
                path = os.path.join(directory, entry)
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
        
        # Thực hiện predict
        results = model.predict(image, conf=confidence, save=True, name='predict')
        
        # Lấy kết quả
        boxes = results[0].boxes
        detected_classes = []
        distance_info = []
        
        if boxes is not None and len(boxes) > 0:
            detected_classes = boxes.cls.cpu().numpy().tolist()
            
            # Ước tính khoảng cách nếu được yêu cầu
            if estimate_distance and distance_estimator.focal_length is not None:
                # Chuyển PIL Image sang numpy array để lấy shape
                if hasattr(image, 'size'):
                    image_shape = (image.size[1], image.size[0])  # (height, width)
                else:
                    image_shape = image.shape[:2]  # (height, width)
                
                distance_info = estimate_distances_from_yolo_results(
                    results, image_shape, distance_estimator, method='width'
                )
        
        # Thêm vào lịch sử
        current_time = time.time()
        detection_history.append({
            'time': current_time,
            'classes': detected_classes,
            'count': len(detected_classes)
        })
        
        # Chỉ giữ lịch sử trong 10 giây gần nhất
        detection_history = [d for d in detection_history if current_time - d['time'] <= 10]
        
        # Kiểm tra cảnh báo
        alert_triggered = False
        if len(detection_history) >= 5:  # Cần ít nhất 5 frame
            all_classes = []
            for d in detection_history:
                all_classes.extend(d['classes'])
            
            if all_classes:
                element_counts = Counter(all_classes)
                most_common_class = max(element_counts, key=element_counts.get)
                
                # Class 0 là drowning
                if most_common_class == 0 and current_time - last_alert_time > ALERT_COOLDOWN:
                    alert_triggered = True
                    last_alert_time = current_time
                    
                    # Gửi cảnh báo
                    try:
                        send_message()
                        print("Drowning alert sent!")
                    except Exception as e:
                        print(f"Error sending alert: {e}")
        
        # Tạo response
        response = {
            "success": True,
            "detected_objects": len(detected_classes),
            "classes": detected_classes,
            "alert_triggered": alert_triggered,
            "confidence": confidence,
            "timestamp": current_time
        }
        
        # Thêm thông tin khoảng cách nếu có
        if distance_info:
            response["distance_info"] = distance_info
            response["distance_estimation_enabled"] = True
        else:
            response["distance_estimation_enabled"] = False
        
        return response
        
    except Exception as e:
        return {"error": str(e)}

@app.route('/health', methods=['GET'])
def health_check():
    """Kiểm tra trạng thái API"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": time.time()
    })

@app.route('/detect', methods=['POST'])
def detect_image():
    """
    API endpoint để detect drowning trong hình ảnh
    
    Accepts:
    - JSON với base64 encoded image
    - Form data với file image
    """
    try:
        confidence = float(request.args.get('confidence', 0.25))
        
        # Kiểm tra content type
        if request.content_type and 'application/json' in request.content_type:
            # Nhận base64 image
            data = request.get_json()
            if not data or 'image' not in data:
                return jsonify({"error": "No image data provided"}), 400
            
            # Decode base64
            image_data = base64.b64decode(data['image'])
            image = Image.open(io.BytesIO(image_data))
            
        elif request.content_type and 'multipart/form-data' in request.content_type:
            # Nhận file upload
            if 'image' not in request.files:
                return jsonify({"error": "No image file provided"}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            image = Image.open(file.stream)
            
        else:
            return jsonify({"error": "Unsupported content type. Use JSON with base64 or multipart/form-data"}), 400
        
        # Thực hiện detect
        estimate_distance = request.args.get('estimate_distance', 'true').lower() == 'true'
        result = detect_drowning(image, confidence, estimate_distance)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/detect_base64', methods=['POST'])
def detect_base64():
    """
    API endpoint đơn giản chỉ nhận base64 image
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400
        
        # Decode base64
        image_data = base64.b64decode(data['image'])
        image = Image.open(io.BytesIO(image_data))
        
        # Thực hiện detect
        confidence = float(request.args.get('confidence', 0.25))
        estimate_distance = request.args.get('estimate_distance', 'true').lower() == 'true'
        result = detect_drowning(image, confidence, estimate_distance)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def config():
    """Cấu hình Twilio và các thông số khác"""
    if request.method == 'GET':
        return jsonify({
            "account_sid": settings.account_sid,
            "auth_token": settings.auth_token,
            "from_": settings.from_,
            "to_": settings.to_,
            "imgbb_api": settings.imgbb_api,
            "alertmsg": settings.alertmsg
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        if data:
            if 'account_sid' in data:
                settings.account_sid = data['account_sid']
            if 'auth_token' in data:
                settings.auth_token = data['auth_token']
            if 'from_' in data:
                settings.from_ = data['from_']
            if 'to_' in data:
                settings.to_ = data['to_']
            if 'imgbb_api' in data:
                settings.imgbb_api = data['imgbb_api']
            if 'alertmsg' in data:
                settings.alertmsg = data['alertmsg']
        
        return jsonify({"message": "Configuration updated successfully"})

@app.route('/calibrate', methods=['POST'])
def calibrate_camera():
    """
    Calibrate camera để tính khoảng cách chính xác
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Nhận thông số calibration
        reference_distance_cm = float(data.get('reference_distance_cm', 100))
        reference_width_cm = float(data.get('reference_width_cm', 50))
        
        # Nhận ảnh reference
        if 'reference_image' not in data:
            return jsonify({"error": "No reference image provided"}), 400
        
        # Decode base64 image
        image_data = base64.b64decode(data['reference_image'])
        image = Image.open(io.BytesIO(image_data))
        
        # Lưu ảnh tạm thời để calibration
        temp_path = "temp_calibration.jpg"
        image.save(temp_path)
        
        # Thực hiện calibration
        global distance_estimator
        distance_estimator.known_width = reference_width_cm
        
        # Hiển thị ảnh để người dùng chọn reference object
        print("Calibration: Please select reference object in the image")
        
        # Đọc ảnh với OpenCV để chọn ROI
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Tạo window để chọn ROI
        roi = cv2.selectROI("Select Reference Object", cv_image, False)
        cv2.destroyAllWindows()
        
        if roi[2] > 0 and roi[3] > 0:
            reference_width_pixels = roi[2]
            distance_estimator.calculate_focal_length(reference_width_pixels, reference_distance_cm)
            
            # Xóa file tạm
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify({
                "success": True,
                "message": "Camera calibrated successfully",
                "focal_length": distance_estimator.focal_length,
                "reference_width_pixels": reference_width_pixels
            })
        else:
            return jsonify({"error": "No valid reference object selected"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/calibrate_auto', methods=['POST'])
def calibrate_camera_auto():
    """
    Calibrate camera tự động với thông số cố định
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Nhận thông số calibration
        reference_distance_cm = float(data.get('reference_distance_cm', 100))
        reference_width_cm = float(data.get('reference_width_cm', 50))
        reference_width_pixels = float(data.get('reference_width_pixels', 200))
        
        # Thực hiện calibration
        global distance_estimator
        distance_estimator.known_width = reference_width_cm
        distance_estimator.calculate_focal_length(reference_width_pixels, reference_distance_cm)
        
        return jsonify({
            "success": True,
            "message": "Camera calibrated successfully",
            "focal_length": distance_estimator.focal_length,
            "reference_width_pixels": reference_width_pixels
        })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/rescue_coordinates', methods=['POST'])
def get_rescue_coordinates():
    """
    Tính toán tọa độ chính xác cho phao cứu hộ
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Lấy thông tin từ distance_info
        distance_info = data.get('distance_info', [])
        if not distance_info:
            return jsonify({"error": "No distance information provided"}), 400
        
        # Lấy thông số môi trường
        water_level = float(data.get('water_level', 0.0))
        current_direction = float(data.get('current_direction', 0.0))
        current_speed = float(data.get('current_speed', 0.0))
        camera_height = float(data.get('camera_height', 5.0))
        camera_angle = float(data.get('camera_angle', 0.0))
        
        # Cập nhật thông số camera nếu cần
        global rescue_calculator
        if camera_height != rescue_calculator.camera_height or camera_angle != math.degrees(rescue_calculator.camera_angle):
            rescue_calculator = RescueCoordinates(camera_height, camera_angle)
        
        # Tính toán tọa độ cho từng đối tượng
        rescue_targets = []
        for obj in distance_info:
            if 'distance_m' in obj and 'angle_x_degrees' in obj and 'angle_y_degrees' in obj:
                rescue_info = rescue_calculator.calculate_rescue_coordinates(
                    obj['distance_m'],
                    obj['angle_x_degrees'],
                    obj['angle_y_degrees'],
                    water_level,
                    current_direction,
                    current_speed
                )
                
                # Thêm thông tin đối tượng
                rescue_info['object_id'] = obj.get('object_id', 0)
                rescue_info['class_id'] = obj.get('class_id', 0)
                rescue_info['confidence'] = obj.get('confidence', 0.0)
                
                # Tạo lệnh điều khiển cho phao
                rescue_info['commands'] = rescue_calculator.get_rescue_commands(rescue_info)
                
                rescue_targets.append(rescue_info)
        
        # Sắp xếp theo mức độ ưu tiên
        rescue_targets.sort(key=lambda x: x['urgency']['priority'])
        
        return jsonify({
            "success": True,
            "rescue_targets": rescue_targets,
            "total_targets": len(rescue_targets),
            "highest_priority": rescue_targets[0]['urgency']['level'] if rescue_targets else None,
            "environment": {
                "water_level": water_level,
                "current_direction": current_direction,
                "current_speed": current_speed,
                "camera_height": camera_height,
                "camera_angle": camera_angle
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/rescue_commands', methods=['POST'])
def get_rescue_commands():
    """
    Tạo lệnh điều khiển đơn giản cho phao cứu hộ
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Lấy thông tin cơ bản
        distance_m = float(data.get('distance_m', 0))
        angle_x_degrees = float(data.get('angle_x_degrees', 0))
        angle_y_degrees = float(data.get('angle_y_degrees', 0))
        
        if distance_m <= 0:
            return jsonify({"error": "Invalid distance"}), 400
        
        # Tính toán tọa độ
        rescue_info = rescue_calculator.calculate_rescue_coordinates(
            distance_m, angle_x_degrees, angle_y_degrees
        )
        
        # Tạo lệnh điều khiển
        commands = rescue_calculator.get_rescue_commands(rescue_info)
        
        return jsonify({
            "success": True,
            "rescue_info": rescue_info,
            "commands": commands
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Drowning Detection API...")
    print("Available endpoints:")
    print("- GET  /health - Health check")
    print("- POST /detect - Detect drowning (accepts JSON or form data)")
    print("- POST /detect_base64 - Detect drowning (base64 only)")
    print("- GET/POST /config - Configure Twilio settings")
    print("- POST /calibrate - Calibrate camera with reference image")
    print("- POST /calibrate_auto - Auto calibrate camera with parameters")
    print("- POST /rescue_coordinates - Calculate rescue coordinates for multiple targets")
    print("- POST /rescue_commands - Generate rescue commands for single target")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 