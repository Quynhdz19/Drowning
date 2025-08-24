/*
  Rescue Buoy Arduino Controller
  Điều khiển phao cứu hộ tự động dựa trên tọa độ từ API
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Servo.h>

// Cấu hình WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* apiUrl = "http://YOUR_SERVER_IP:5000";

// Pin definitions
#define MOTOR_FORWARD_PIN 26
#define MOTOR_BACKWARD_PIN 27
#define MOTOR_SPEED_PIN 25
#define SERVO_HEADING_PIN 32
#define DEPTH_SERVO_PIN 33
#define BUZZER_PIN 14
#define LED_RED_PIN 12
#define LED_GREEN_PIN 13
#define LED_BLUE_PIN 15

// Servo objects
Servo headingServo;
Servo depthServo;

// Biến trạng thái
struct BuoyStatus {
  float currentX = 0.0;
  float currentY = 0.0;
  float currentZ = 0.0;
  float batteryLevel = 100.0;
  String status = "IDLE";
  bool isDeployed = false;
  int currentHeading = 0;
  float currentSpeed = 0.0;
} buoyStatus;

// Cấu hình
const int MAX_SPEED = 255;
const int MIN_SPEED = 0;
const int SERVO_MIN_ANGLE = 0;
const int SERVO_MAX_ANGLE = 180;
const float BATTERY_DRAIN_RATE = 0.1; // % per second

void setup() {
  Serial.begin(115200);
  Serial.println("🌊 Rescue Buoy Controller Starting...");
  
  // Khởi tạo pins
  initializePins();
  
  // Kết nối WiFi
  connectToWiFi();
  
  // Khởi tạo servo
  initializeServos();
  
  // Test hệ thống
  systemTest();
  
  Serial.println("Rescue Buoy ready for missions!");
}

void loop() {
  // Kiểm tra WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectToWiFi();
  }
  
  // Cập nhật trạng thái
  updateBattery();
  updateStatus();
  
  // Chờ lệnh từ API hoặc cảm biến
  if (buoyStatus.isDeployed) {
    // Có thể thêm logic để lắng nghe lệnh từ API
    delay(1000);
  }
  
  delay(100);
}

void initializePins() {
  // Motor pins
  pinMode(MOTOR_FORWARD_PIN, OUTPUT);
  pinMode(MOTOR_BACKWARD_PIN, OUTPUT);
  pinMode(MOTOR_SPEED_PIN, OUTPUT);
  
  // LED pins
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_BLUE_PIN, OUTPUT);
  
  // Buzzer pin
  pinMode(BUZZER_PIN, OUTPUT);
  
  Serial.println("Pins initialized");
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void initializeServos() {
  headingServo.attach(SERVO_HEADING_PIN);
  depthServo.attach(DEPTH_SERVO_PIN);
  
  // Set initial positions
  headingServo.write(90);  // Center
  depthServo.write(90);    // Surface level
  
  Serial.println("Servos initialized");
}

void systemTest() {
  Serial.println("Running system test...");
  
  // Test LEDs
  testLEDs();
  
  // Test buzzer
  testBuzzer();
  
  // Test servos
  testServos();
  
  // Test motors
  testMotors();
  
  Serial.println("System test completed!");
}

void testLEDs() {
  Serial.println("Testing LEDs...");
  digitalWrite(LED_RED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_RED_PIN, LOW);
  
  digitalWrite(LED_GREEN_PIN, HIGH);
  delay(500);
  digitalWrite(LED_GREEN_PIN, LOW);
  
  digitalWrite(LED_BLUE_PIN, HIGH);
  delay(500);
  digitalWrite(LED_BLUE_PIN, LOW);
}

void testBuzzer() {
  Serial.println("Testing buzzer...");
  tone(BUZZER_PIN, 1000, 500);
  delay(500);
}

void testServos() {
  Serial.println("Testing servos...");
  headingServo.write(0);
  delay(500);
  headingServo.write(180);
  delay(500);
  headingServo.write(90);
  
  depthServo.write(0);
  delay(500);
  depthServo.write(180);
  delay(500);
  depthServo.write(90);
}

void testMotors() {
  Serial.println("Testing motors...");
  setMotorSpeed(50);
  delay(1000);
  setMotorSpeed(0);
}

// API Functions
bool getRescueCommands(float distance_m, float angle_x, float angle_y) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return false;
  }
  
  HTTPClient http;
  http.begin(String(apiUrl) + "/rescue_commands");
  http.addHeader("Content-Type", "application/json");
  
  // Tạo JSON payload
  String payload = "{\"distance_m\":" + String(distance_m) + 
                   ",\"angle_x_degrees\":" + String(angle_x) + 
                   ",\"angle_y_degrees\":" + String(angle_y) + "}";
  
  Serial.println("Sending request: " + payload);
  
  int httpResponseCode = http.POST(payload);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Response: " + response);
    
    // Parse JSON response
    DynamicJsonDocument doc(2048);
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error && doc["success"]) {
      // Thực hiện lệnh cứu hộ
      executeRescueCommands(doc["commands"]);
      return true;
    } else {
      Serial.println("Failed to parse response");
    }
  } else {
    Serial.println("Error on HTTP request");
  }
  
  http.end();
  return false;
}

void executeRescueCommands(JsonObject commands) {
  Serial.println("🚨 Executing rescue commands...");
  
  // Lấy thông tin điều khiển
  JsonObject targetCoords = commands["target_coordinates"];
  JsonObject movement = commands["movement"];
  JsonObject mission = commands["mission"];
  
  float targetX = targetCoords["x"];
  float targetY = targetCoords["y"];
  float targetZ = targetCoords["z"];
  float heading = movement["heading"];
  float speed = movement["speed"];
  String depthMode = movement["depth_mode"].as<String>();
  String priority = mission["priority"].as<String>();
  
  Serial.println("Target: X=" + String(targetX) + "m, Y=" + String(targetY) + "m, Z=" + String(targetZ) + "m");
  Serial.println("Heading: " + String(heading) + "°, Speed: " + String(speed) + " m/s");
  Serial.println("Priority: " + priority);
  
  // Thực hiện điều khiển
  navigateToTarget(heading, speed, depthMode);
  
  // Thực hiện cứu hộ
  performRescue();
  
  // Trở về
  returnToBase();
  
  Serial.println("✅ Rescue mission completed!");
}

void navigateToTarget(float heading, float speed, String depthMode) {
  Serial.println("🧭 Navigating to target...");
  
  // Set heading
  setHeading(heading);
  
  // Set speed
  setMotorSpeed(speed * 50); // Convert m/s to PWM (0-255)
  
  // Set depth
  setDepthMode(depthMode);
  
  // Simulate movement time (trong thực tế sẽ dùng GPS/IMU)
  delay(5000);
  
  // Stop
  setMotorSpeed(0);
  
  Serial.println("Reached target");
}

void performRescue() {
  Serial.println("🛟 Performing rescue operation...");
  
  // Bật LED đỏ để báo hiệu cứu hộ
  digitalWrite(LED_RED_PIN, HIGH);
  
  // Phát âm thanh cảnh báo
  tone(BUZZER_PIN, 2000, 2000);
  
  // Simulate rescue time
  delay(3000);
  
  // Tắt LED và buzzer
  digitalWrite(LED_RED_PIN, LOW);
  noTone(BUZZER_PIN);
  
  Serial.println("Rescue operation completed");
}

void returnToBase() {
  Serial.println("🏠 Returning to base...");
  
  // Bật LED xanh
  digitalWrite(LED_GREEN_PIN, HIGH);
  
  // Set heading về gốc (0°)
  setHeading(0);
  
  // Set speed trung bình
  setMotorSpeed(100);
  
  // Simulate return time
  delay(3000);
  
  // Stop và tắt LED
  setMotorSpeed(0);
  digitalWrite(LED_GREEN_PIN, LOW);
  
  Serial.println("Returned to base");
}

// Control Functions
void setHeading(float heading) {
  // Map heading (0-360°) to servo angle (0-180°)
  int servoAngle = map(heading, 0, 360, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE);
  headingServo.write(servoAngle);
  buoyStatus.currentHeading = heading;
  
  Serial.println("Set heading to " + String(heading) + "° (servo: " + String(servoAngle) + ")");
}

void setMotorSpeed(float speed) {
  // Limit speed
  speed = constrain(speed, MIN_SPEED, MAX_SPEED);
  
  if (speed > 0) {
    digitalWrite(MOTOR_FORWARD_PIN, HIGH);
    digitalWrite(MOTOR_BACKWARD_PIN, LOW);
  } else if (speed < 0) {
    digitalWrite(MOTOR_FORWARD_PIN, LOW);
    digitalWrite(MOTOR_BACKWARD_PIN, HIGH);
    speed = abs(speed);
  } else {
    digitalWrite(MOTOR_FORWARD_PIN, LOW);
    digitalWrite(MOTOR_BACKWARD_PIN, LOW);
  }
  
  analogWrite(MOTOR_SPEED_PIN, speed);
  buoyStatus.currentSpeed = speed;
  
  Serial.println("Set motor speed to " + String(speed));
}

void setDepthMode(String mode) {
  int servoAngle = 90; // Default surface level
  
  if (mode == "DIVE_DEEP") {
    servoAngle = 180;
  } else if (mode == "DIVE_SHALLOW") {
    servoAngle = 135;
  } else if (mode == "FLOAT_HIGH") {
    servoAngle = 45;
  } else {
    servoAngle = 90; // SURFACE_LEVEL
  }
  
  depthServo.write(servoAngle);
  Serial.println("Set depth mode: " + mode + " (servo: " + String(servoAngle) + ")");
}

void updateBattery() {
  // Simulate battery drain
  buoyStatus.batteryLevel -= BATTERY_DRAIN_RATE * 0.1; // 0.1s interval
  
  if (buoyStatus.batteryLevel < 20) {
    digitalWrite(LED_RED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_RED_PIN, LOW);
  }
}

void updateStatus() {
  // Update status based on current state
  if (buoyStatus.currentSpeed > 0) {
    buoyStatus.status = "MOVING";
  } else if (buoyStatus.isDeployed) {
    buoyStatus.status = "DEPLOYED";
  } else {
    buoyStatus.status = "IDLE";
  }
}

void deployBuoy() {
  Serial.println("🚀 Deploying rescue buoy...");
  buoyStatus.isDeployed = true;
  buoyStatus.status = "DEPLOYED";
  
  // Bật LED xanh
  digitalWrite(LED_GREEN_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_GREEN_PIN, LOW);
  
  Serial.println("Rescue buoy deployed!");
}

// Serial command interface
void handleSerialCommands() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "DEPLOY") {
      deployBuoy();
    } else if (command == "STATUS") {
      printStatus();
    } else if (command.startsWith("RESCUE")) {
      // Format: RESCUE distance angle_x angle_y
      // Example: RESCUE 15.5 10.2 -5.1
      parseRescueCommand(command);
    } else if (command == "TEST") {
      systemTest();
    } else {
      Serial.println("Unknown command: " + command);
    }
  }
}

void parseRescueCommand(String command) {
  // Parse: RESCUE distance angle_x angle_y
  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);
  int thirdSpace = command.indexOf(' ', secondSpace + 1);
  
  if (firstSpace > 0 && secondSpace > 0 && thirdSpace > 0) {
    float distance = command.substring(firstSpace + 1, secondSpace).toFloat();
    float angle_x = command.substring(secondSpace + 1, thirdSpace).toFloat();
    float angle_y = command.substring(thirdSpace + 1).toFloat();
    
    Serial.println("Executing rescue: " + String(distance) + "m, " + String(angle_x) + "°, " + String(angle_y) + "°");
    getRescueCommands(distance, angle_x, angle_y);
  } else {
    Serial.println("Invalid RESCUE command format. Use: RESCUE distance angle_x angle_y");
  }
}

void printStatus() {
  Serial.println("=== Buoy Status ===");
  Serial.println("Status: " + buoyStatus.status);
  Serial.println("Position: X=" + String(buoyStatus.currentX) + "m, Y=" + String(buoyStatus.currentY) + "m, Z=" + String(buoyStatus.currentZ) + "m");
  Serial.println("Battery: " + String(buoyStatus.batteryLevel) + "%");
  Serial.println("Heading: " + String(buoyStatus.currentHeading) + "°");
  Serial.println("Speed: " + String(buoyStatus.currentSpeed));
  Serial.println("Deployed: " + String(buoyStatus.isDeployed ? "Yes" : "No"));
  Serial.println("==================");
} 