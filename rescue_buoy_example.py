#!/usr/bin/env python3
"""
Example code cho phao cứu hộ tự động
Phao sẽ nhận tọa độ từ API và tự động điều khiển đến vị trí người gặp nạn
"""

import requests
import time
import json
import math

class RescueBuoy:
    """
    Class điều khiển phao cứu hộ tự động
    """
    
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
        self.current_position = {"x": 0, "y": 0, "z": 0}  # Vị trí hiện tại của phao
        self.is_deployed = False
        self.battery_level = 100.0
        self.status = "IDLE"
        
    def get_rescue_coordinates(self, distance_info, environment_data=None):
        """
        Lấy tọa độ cứu hộ từ API
        
        Args:
            distance_info (list): Thông tin khoảng cách từ detect
            environment_data (dict): Thông số môi trường
        """
        if environment_data is None:
            environment_data = {
                "water_level": 0.0,
                "current_direction": 0.0,
                "current_speed": 0.0,
                "camera_height": 5.0,
                "camera_angle": 0.0
            }
        
        payload = {
            "distance_info": distance_info,
            **environment_data
        }
        
        try:
            response = requests.post(f"{self.api_url}/rescue_coordinates", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting rescue coordinates: {response.text}")
                return None
        except Exception as e:
            print(f"Error connecting to API: {e}")
            return None
    
    def get_simple_commands(self, distance_m, angle_x_degrees, angle_y_degrees):
        """
        Lấy lệnh điều khiển đơn giản cho một target
        """
        payload = {
            "distance_m": distance_m,
            "angle_x_degrees": angle_x_degrees,
            "angle_y_degrees": angle_y_degrees
        }
        
        try:
            response = requests.post(f"{self.api_url}/rescue_commands", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting rescue commands: {response.text}")
                return None
        except Exception as e:
            print(f"Error connecting to API: {e}")
            return None
    
    def execute_rescue_mission(self, rescue_target):
        """
        Thực hiện nhiệm vụ cứu hộ
        
        Args:
            rescue_target (dict): Thông tin target cần cứu
        """
        print(f"🚨 Starting rescue mission for target {rescue_target['object_id']}")
        print(f"Priority: {rescue_target['urgency']['level']}")
        print(f"Description: {rescue_target['urgency']['description']}")
        
        # Lấy thông tin điều khiển
        commands = rescue_target['commands']
        coords = rescue_target['coordinates']
        control = rescue_target['control']
        
        print(f"Target coordinates: X={coords['x_m']}m, Y={coords['y_m']}m, Z={coords['z_m']}m")
        print(f"Distance to target: {coords['distance_m']}m")
        print(f"Target heading: {control['target_angle_degrees']}°")
        print(f"Optimal speed: {control['speed_mps']} m/s")
        print(f"Estimated time: {control['estimated_time_seconds']}s")
        
        # Thực hiện điều khiển phao
        self._navigate_to_target(commands)
        
        # Thực hiện cứu hộ
        self._perform_rescue(commands)
        
        # Trở về vị trí ban đầu
        self._return_to_base()
        
        print("✅ Rescue mission completed!")
    
    def _navigate_to_target(self, commands):
        """
        Điều hướng phao đến target
        """
        print("🧭 Navigating to target...")
        
        target_coords = commands['target_coordinates']
        movement = commands['movement']
        
        # Điều khiển hướng
        print(f"Setting heading to {movement['heading']}°")
        self._set_heading(movement['heading'])
        
        # Điều khiển tốc độ
        print(f"Setting speed to {movement['speed']} m/s")
        self._set_speed(movement['speed'])
        
        # Điều khiển độ sâu
        print(f"Setting depth mode: {movement['depth_mode']}")
        self._set_depth_mode(movement['depth_mode'])
        
        # Di chuyển đến target
        distance = commands['navigation']['distance_to_target']
        estimated_time = commands['control']['estimated_time_seconds']
        
        print(f"Moving {distance}m to target (estimated {estimated_time}s)...")
        time.sleep(estimated_time)  # Simulate movement time
        
        # Cập nhật vị trí
        self.current_position = target_coords
        print(f"Reached target at {target_coords}")
    
    def _perform_rescue(self, commands):
        """
        Thực hiện cứu hộ
        """
        print("🛟 Performing rescue operation...")
        
        # Kiểm tra an toàn
        if commands['safety']['battery_check']:
            self._check_battery()
        
        if commands['safety']['obstacle_avoidance']:
            self._avoid_obstacles()
        
        # Thực hiện cứu hộ
        print("Deploying rescue equipment...")
        time.sleep(2)  # Simulate rescue time
        
        print("Securing victim...")
        time.sleep(3)  # Simulate securing time
        
        print("Rescue operation completed")
    
    def _return_to_base(self):
        """
        Trở về vị trí ban đầu
        """
        print("🏠 Returning to base...")
        
        # Điều khiển về vị trí gốc
        self._set_heading(0)  # Hướng về gốc
        self._set_speed(2.0)  # Tốc độ trung bình
        
        # Tính thời gian về
        distance_home = math.sqrt(self.current_position['x']**2 + self.current_position['y']**2)
        time_home = distance_home / 2.0
        
        print(f"Returning {distance_home}m to base (estimated {time_home}s)...")
        time.sleep(time_home)  # Simulate return time
        
        # Reset vị trí
        self.current_position = {"x": 0, "y": 0, "z": 0}
        self._set_speed(0)  # Dừng
        
        print("Returned to base successfully")
    
    def _set_heading(self, heading_degrees):
        """
        Điều khiển hướng phao
        """
        print(f"  → Setting heading to {heading_degrees}°")
        # Code điều khiển servo/motor cho hướng
    
    def _set_speed(self, speed_mps):
        """
        Điều khiển tốc độ phao
        """
        print(f"  → Setting speed to {speed_mps} m/s")
        # Code điều khiển motor cho tốc độ
    
    def _set_depth_mode(self, depth_mode):
        """
        Điều khiển độ sâu phao
        """
        print(f"  → Setting depth mode: {depth_mode}")
        # Code điều khiển ballast/pump cho độ sâu
    
    def _check_battery(self):
        """
        Kiểm tra pin
        """
        self.battery_level -= 5  # Giảm pin khi hoạt động
        print(f"  → Battery level: {self.battery_level}%")
        
        if self.battery_level < 20:
            print("⚠️  Low battery warning!")
    
    def _avoid_obstacles(self):
        """
        Tránh chướng ngại vật
        """
        print("  → Obstacle avoidance active")
        # Code cảm biến và tránh chướng ngại vật
    
    def deploy_buoy(self):
        """
        Triển khai phao
        """
        print("🚀 Deploying rescue buoy...")
        self.is_deployed = True
        self.status = "DEPLOYED"
        print("Rescue buoy deployed and ready for missions")
    
    def get_status(self):
        """
        Lấy trạng thái phao
        """
        return {
            "status": self.status,
            "position": self.current_position,
            "battery": self.battery_level,
            "deployed": self.is_deployed
        }

# Example usage
def main():
    print("🌊 Rescue Buoy Control System")
    print("=" * 40)
    
    # Khởi tạo phao
    buoy = RescueBuoy()
    
    # Triển khai phao
    buoy.deploy_buoy()
    
    # Simulate detection data
    distance_info = [
        {
            "object_id": 0,
            "class_id": 0,  # Drowning person
            "confidence": 0.85,
            "distance_m": 15.5,
            "angle_x_degrees": 10.2,
            "angle_y_degrees": -5.1
        }
    ]
    
    # Lấy tọa độ cứu hộ
    print("\n📡 Getting rescue coordinates...")
    rescue_data = buoy.get_rescue_coordinates(distance_info)
    
    if rescue_data and rescue_data['success']:
        print(f"Found {rescue_data['total_targets']} rescue targets")
        print(f"Highest priority: {rescue_data['highest_priority']}")
        
        # Thực hiện cứu hộ cho target đầu tiên
        if rescue_data['rescue_targets']:
            target = rescue_data['rescue_targets'][0]
            buoy.execute_rescue_mission(target)
    
    # Hiển thị trạng thái cuối
    print("\n📊 Final Status:")
    status = buoy.get_status()
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main() 