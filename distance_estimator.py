import cv2
import numpy as np
import math

class DistanceEstimator:
    """
    Class để ước tính khoảng cách từ camera đến đối tượng
    """
    
    def __init__(self, known_width=50, focal_length=None, camera_matrix=None, dist_coeffs=None):
        """
        Khởi tạo DistanceEstimator
        
        Args:
            known_width (float): Chiều rộng thực tế của đối tượng (cm)
            focal_length (float): Tiêu cự camera (pixel)
            camera_matrix (np.array): Ma trận camera calibration
            dist_coeffs (np.array): Hệ số distortion
        """
        self.known_width = known_width
        self.focal_length = focal_length
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        
        # Nếu không có focal_length, sẽ tính từ known_width
        if self.focal_length is None:
            self.focal_length = None  # Sẽ được tính khi có reference object
    
    def calculate_focal_length(self, reference_width_pixels, reference_distance_cm):
        """
        Tính focal length từ reference object
        
        Args:
            reference_width_pixels (float): Chiều rộng reference object trong ảnh (pixel)
            reference_distance_cm (float): Khoảng cách thực tế đến reference object (cm)
        """
        self.focal_length = (reference_width_pixels * reference_distance_cm) / self.known_width
        print(f"Focal length calculated: {self.focal_length:.2f} pixels")
        return self.focal_length
    
    def estimate_distance_from_width(self, object_width_pixels):
        """
        Ước tính khoảng cách dựa trên chiều rộng đối tượng
        
        Args:
            object_width_pixels (float): Chiều rộng đối tượng trong ảnh (pixel)
            
        Returns:
            float: Khoảng cách ước tính (cm)
        """
        if self.focal_length is None:
            raise ValueError("Focal length not set. Use calculate_focal_length() first.")
        
        distance = (self.known_width * self.focal_length) / object_width_pixels
        return distance
    
    def estimate_distance_from_height(self, object_height_pixels, known_height=170):
        """
        Ước tính khoảng cách dựa trên chiều cao người (trung bình 170cm)
        
        Args:
            object_height_pixels (float): Chiều cao đối tượng trong ảnh (pixel)
            known_height (float): Chiều cao thực tế của người (cm)
            
        Returns:
            float: Khoảng cách ước tính (cm)
        """
        if self.focal_length is None:
            raise ValueError("Focal length not set. Use calculate_focal_length() first.")
        
        distance = (known_height * self.focal_length) / object_height_pixels
        return distance
    
    def estimate_distance_from_bbox(self, bbox, method='width'):
        """
        Ước tính khoảng cách từ bounding box
        
        Args:
            bbox (list): [x1, y1, x2, y2] hoặc [x_center, y_center, width, height]
            method (str): 'width' hoặc 'height'
            
        Returns:
            float: Khoảng cách ước tính (cm)
        """
        if len(bbox) == 4:
            if method == 'width':
                width = bbox[2] - bbox[0]  # x2 - x1
                return self.estimate_distance_from_width(width)
            elif method == 'height':
                height = bbox[3] - bbox[1]  # y2 - y1
                return self.estimate_distance_from_height(height)
        
        return None
    
    def estimate_distance_from_center(self, bbox, image_width, image_height):
        """
        Ước tính khoảng cách dựa trên vị trí trung tâm của đối tượng
        
        Args:
            bbox (list): [x1, y1, x2, y2]
            image_width (int): Chiều rộng ảnh
            image_height (int): Chiều cao ảnh
            
        Returns:
            dict: Thông tin khoảng cách và vị trí
        """
        if len(bbox) != 4:
            return None
        
        # Tính trung tâm đối tượng
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        
        # Tính khoảng cách từ trung tâm ảnh
        image_center_x = image_width / 2
        image_center_y = image_height / 2
        
        # Tính góc lệch
        angle_x = math.atan2(center_x - image_center_x, self.focal_length) * 180 / math.pi
        angle_y = math.atan2(center_y - image_center_y, self.focal_length) * 180 / math.pi
        
        # Ước tính khoảng cách
        distance = self.estimate_distance_from_bbox(bbox)
        
        return {
            'distance_cm': distance,
            'distance_m': distance / 100 if distance else None,
            'center_x': center_x,
            'center_y': center_y,
            'angle_x_degrees': angle_x,
            'angle_y_degrees': angle_y,
            'position': self._get_position_description(angle_x, angle_y, distance)
        }
    
    def _get_position_description(self, angle_x, angle_y, distance):
        """
        Mô tả vị trí đối tượng
        """
        if distance is None:
            return "Unknown"
        
        # Mô tả hướng
        direction_x = "center"
        if angle_x > 10:
            direction_x = "right"
        elif angle_x < -10:
            direction_x = "left"
        
        direction_y = "center"
        if angle_y > 10:
            direction_y = "below"
        elif angle_y < -10:
            direction_y = "above"
        
        # Mô tả khoảng cách
        if distance < 100:
            distance_desc = "very close"
        elif distance < 300:
            distance_desc = "close"
        elif distance < 500:
            distance_desc = "medium"
        elif distance < 1000:
            distance_desc = "far"
        else:
            distance_desc = "very far"
        
        return f"{distance_desc} ({distance:.1f}m), {direction_x} {direction_y}"
    
    def calibrate_with_reference(self, reference_image_path, reference_distance_cm, reference_width_cm=None):
        """
        Calibrate camera với reference object
        
        Args:
            reference_image_path (str): Đường dẫn ảnh reference
            reference_distance_cm (float): Khoảng cách thực tế đến reference object
            reference_width_cm (float): Chiều rộng thực tế của reference object
        """
        # Đọc ảnh reference
        image = cv2.imread(reference_image_path)
        if image is None:
            raise ValueError(f"Cannot read image: {reference_image_path}")
        
        # Hiển thị ảnh để người dùng chọn reference object
        print("Please select the reference object in the image.")
        print("Click and drag to create a rectangle around the reference object.")
        
        # Tạo window để chọn ROI
        roi = cv2.selectROI("Select Reference Object", image, False)
        cv2.destroyAllWindows()
        
        if roi[2] > 0 and roi[3] > 0:
            reference_width_pixels = roi[2]
            if reference_width_cm:
                self.known_width = reference_width_cm
            
            self.calculate_focal_length(reference_width_pixels, reference_distance_cm)
            print(f"Calibration completed. Focal length: {self.focal_length:.2f}")
        else:
            print("No valid ROI selected.")

# Hàm tiện ích để tính khoảng cách từ YOLO results
def estimate_distances_from_yolo_results(results, image_shape, distance_estimator, method='width'):
    """
    Ước tính khoảng cách cho tất cả đối tượng được detect
    
    Args:
        results: YOLO results object
        image_shape (tuple): (height, width) của ảnh
        distance_estimator: DistanceEstimator instance
        method (str): 'width' hoặc 'height'
        
    Returns:
        list: Danh sách thông tin khoảng cách cho mỗi đối tượng
    """
    distances = []
    
    if results and len(results) > 0:
        boxes = results[0].boxes
        if boxes is not None and len(boxes) > 0:
            for i, box in enumerate(boxes):
                # Lấy bounding box
                bbox = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                confidence = box.conf[0].cpu().numpy()
                class_id = int(box.cls[0].cpu().numpy())
                
                # Ước tính khoảng cách
                distance_info = distance_estimator.estimate_distance_from_center(
                    bbox, image_shape[1], image_shape[0]
                )
                
                if distance_info:
                    distance_info.update({
                        'object_id': i,
                        'class_id': class_id,
                        'confidence': float(confidence),
                        'bbox': bbox.tolist()
                    })
                    distances.append(distance_info)
    
    return distances 