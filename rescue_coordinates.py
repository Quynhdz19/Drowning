import math
import numpy as np

class RescueCoordinates:
    """
    Class để tính toán tọa độ chính xác cho phao cứu hộ
    """
    
    def __init__(self, camera_height=5.0, camera_angle=0.0):
        """
        Khởi tạo RescueCoordinates
        
        Args:
            camera_height (float): Chiều cao camera so với mặt nước (m)
            camera_angle (float): Góc nghiêng camera so với phương ngang (độ)
        """
        self.camera_height = camera_height
        self.camera_angle = math.radians(camera_angle)  # Chuyển sang radian
    
    def calculate_rescue_coordinates(self, distance_m, angle_x_degrees, angle_y_degrees, 
                                   water_level=0.0, current_direction=0.0, current_speed=0.0):
        """
        Tính toán tọa độ chính xác cho phao cứu hộ
        
        Args:
            distance_m (float): Khoảng cách từ camera đến người (m)
            angle_x_degrees (float): Góc lệch theo trục X (độ)
            angle_y_degrees (float): Góc lệch theo trục Y (độ)
            water_level (float): Mực nước so với camera (m, âm = dưới camera)
            current_direction (float): Hướng dòng chảy (độ, 0 = Bắc, 90 = Đông)
            current_speed (float): Tốc độ dòng chảy (m/s)
            
        Returns:
            dict: Tọa độ và thông tin điều khiển phao
        """
        # Chuyển góc sang radian
        angle_x = math.radians(angle_x_degrees)
        angle_y = math.radians(angle_y_degrees)
        
        # Tính toán tọa độ 3D
        # X: khoảng cách theo trục ngang
        x_distance = distance_m * math.cos(angle_y) * math.sin(angle_x)
        
        # Y: khoảng cách theo trục dọc (hướng camera nhìn)
        y_distance = distance_m * math.cos(angle_y) * math.cos(angle_x)
        
        # Z: độ cao so với mặt nước
        z_distance = distance_m * math.sin(angle_y) - self.camera_height + water_level
        
        # Tính toán ảnh hưởng của dòng chảy
        current_rad = math.radians(current_direction)
        current_x = current_speed * math.sin(current_rad)
        current_y = current_speed * math.cos(current_rad)
        
        # Điều chỉnh tọa độ do dòng chảy (ước tính thời gian phao đến)
        estimated_time = distance_m / 2.0  # Ước tính thời gian phao di chuyển (m/s)
        drift_x = current_x * estimated_time
        drift_y = current_y * estimated_time
        
        # Tọa độ cuối cùng cho phao
        final_x = x_distance + drift_x
        final_y = y_distance + drift_y
        
        # Tính góc điều khiển phao
        target_angle = math.degrees(math.atan2(final_x, final_y))
        if target_angle < 0:
            target_angle += 360
        
        # Tính khoảng cách thực tế cần di chuyển
        actual_distance = math.sqrt(final_x**2 + final_y**2)
        
        # Phân loại mức độ khẩn cấp
        urgency_level = self._calculate_urgency_level(distance_m, z_distance)
        
        # Thông tin điều khiển phao
        rescue_info = {
            "coordinates": {
                "x_m": round(final_x, 2),
                "y_m": round(final_y, 2),
                "z_m": round(z_distance, 2),
                "distance_m": round(actual_distance, 2)
            },
            "control": {
                "target_angle_degrees": round(target_angle, 1),
                "target_angle_radians": round(math.radians(target_angle), 3),
                "speed_mps": self._calculate_optimal_speed(actual_distance, urgency_level),
                "estimated_time_seconds": round(actual_distance / 2.0, 1)
            },
            "environment": {
                "current_drift_x": round(drift_x, 2),
                "current_drift_y": round(drift_y, 2),
                "current_speed": current_speed,
                "current_direction": current_direction
            },
            "urgency": {
                "level": urgency_level,
                "priority": self._get_priority(urgency_level),
                "description": self._get_urgency_description(urgency_level)
            },
            "navigation": {
                "heading_degrees": round(target_angle, 1),
                "distance_to_target": round(actual_distance, 2),
                "depth_adjustment": self._calculate_depth_adjustment(z_distance)
            }
        }
        
        return rescue_info
    
    def _calculate_urgency_level(self, distance_m, depth_m):
        """
        Tính toán mức độ khẩn cấp
        """
        # Khoảng cách càng gần càng khẩn cấp
        distance_factor = max(0, 1 - (distance_m / 50.0))  # 50m là khoảng cách tối đa
        
        # Độ sâu càng lớn càng khẩn cấp
        depth_factor = min(1.0, abs(depth_m) / 3.0)  # 3m là độ sâu tối đa
        
        urgency = (distance_factor * 0.7 + depth_factor * 0.3)
        
        if urgency > 0.8:
            return "CRITICAL"
        elif urgency > 0.6:
            return "HIGH"
        elif urgency > 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_priority(self, urgency_level):
        """
        Lấy mức độ ưu tiên
        """
        priorities = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4
        }
        return priorities.get(urgency_level, 4)
    
    def _get_urgency_description(self, urgency_level):
        """
        Mô tả mức độ khẩn cấp
        """
        descriptions = {
            "CRITICAL": "Người gặp nạn ở rất gần và sâu - Cần cứu hộ ngay lập tức!",
            "HIGH": "Người gặp nạn ở gần - Cần cứu hộ nhanh chóng",
            "MEDIUM": "Người gặp nạn ở khoảng cách trung bình",
            "LOW": "Người gặp nạn ở xa - Theo dõi và chuẩn bị cứu hộ"
        }
        return descriptions.get(urgency_level, "Không xác định")
    
    def _calculate_optimal_speed(self, distance_m, urgency_level):
        """
        Tính tốc độ tối ưu cho phao
        """
        base_speed = 2.0  # m/s
        
        if urgency_level == "CRITICAL":
            return min(5.0, base_speed * 2.5)  # Tối đa 5 m/s
        elif urgency_level == "HIGH":
            return min(4.0, base_speed * 2.0)
        elif urgency_level == "MEDIUM":
            return min(3.0, base_speed * 1.5)
        else:
            return base_speed
    
    def _calculate_depth_adjustment(self, depth_m):
        """
        Tính điều chỉnh độ sâu cho phao
        """
        if depth_m < -2.0:
            return "DIVE_DEEP"  # Lặn sâu
        elif depth_m < -0.5:
            return "DIVE_SHALLOW"  # Lặn nông
        elif depth_m > 0.5:
            return "FLOAT_HIGH"  # Nổi cao
        else:
            return "SURFACE_LEVEL"  # Mặt nước
    
    def get_rescue_commands(self, rescue_info):
        """
        Tạo lệnh điều khiển cho phao cứu hộ
        
        Args:
            rescue_info (dict): Thông tin cứu hộ từ calculate_rescue_coordinates
            
        Returns:
            dict: Lệnh điều khiển cho phao
        """
        coords = rescue_info["coordinates"]
        control = rescue_info["control"]
        urgency = rescue_info["urgency"]
        nav = rescue_info["navigation"]
        
        commands = {
            "command_type": "RESCUE_MISSION",
            "target_coordinates": {
                "x": coords["x_m"],
                "y": coords["y_m"],
                "z": coords["z_m"]
            },
            "movement": {
                "heading": nav["heading_degrees"],
                "speed": control["speed_mps"],
                "depth_mode": nav["depth_adjustment"]
            },
            "mission": {
                "priority": urgency["level"],
                "estimated_duration": control["estimated_time_seconds"],
                "auto_return": True,
                "emergency_contact": urgency["level"] in ["CRITICAL", "HIGH"]
            },
            "safety": {
                "max_speed": 5.0,
                "depth_limit": -10.0,
                "battery_check": True,
                "obstacle_avoidance": True
            }
        }
        
        return commands
    
    def calculate_multiple_targets(self, targets_list, water_level=0.0, 
                                 current_direction=0.0, current_speed=0.0):
        """
        Tính toán tọa độ cho nhiều người gặp nạn
        
        Args:
            targets_list (list): Danh sách các target [{"distance_m": x, "angle_x": y, "angle_y": z}, ...]
            water_level (float): Mực nước
            current_direction (float): Hướng dòng chảy
            current_speed (float): Tốc độ dòng chảy
            
        Returns:
            list: Danh sách thông tin cứu hộ cho từng target
        """
        rescue_targets = []
        
        for i, target in enumerate(targets_list):
            rescue_info = self.calculate_rescue_coordinates(
                target["distance_m"],
                target["angle_x_degrees"],
                target["angle_y_degrees"],
                water_level,
                current_direction,
                current_speed
            )
            
            rescue_info["target_id"] = i
            rescue_info["commands"] = self.get_rescue_commands(rescue_info)
            rescue_targets.append(rescue_info)
        
        # Sắp xếp theo mức độ ưu tiên
        rescue_targets.sort(key=lambda x: x["urgency"]["priority"])
        
        return rescue_targets 