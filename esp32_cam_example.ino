/*
  Drowning Detection with ESP32-CAM
  Gửi hình ảnh từ camera lên API để detect tình trạng đuối nước
*/

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <base64.h>
#include <ArduinoJson.h>

// Cấu hình WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Cấu hình API
const char* apiUrl = "http://YOUR_SERVER_IP:5000/detect_base64";
const char* serverName = "YOUR_SERVER_IP";

// Cấu hình camera ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    22
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     4

// Biến toàn cục
unsigned long lastCaptureTime = 0;
const unsigned long captureInterval = 5000; // Chụp ảnh mỗi 5 giây
bool alertTriggered = false;

void setup() {
  Serial.begin(115200);
  Serial.println("Starting ESP32-CAM Drowning Detection...");
  
  // Cấu hình camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Cấu hình chất lượng ảnh
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Khởi tạo camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
  
  Serial.println("Camera initialized successfully");
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  
  // Test kết nối API và calibrate camera
  delay(2000);
  testAPIConnection();
  delay(1000);
  calibrateCamera();
}

void loop() {
  unsigned long currentTime = millis();
  
  // Chụp ảnh theo interval
  if (currentTime - lastCaptureTime >= captureInterval) {
    captureAndDetect();
    lastCaptureTime = currentTime;
  }
  
  delay(100);
}

void captureAndDetect() {
  Serial.println("Capturing image...");
  
  // Chụp ảnh từ camera
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  
  Serial.printf("Image captured: %dx%d %db\n", fb->width, fb->height, fb->len);
  
  // Encode base64
  String base64Image = base64::encode(fb->buf, fb->len);
  Serial.println("Image encoded to base64");
  
  // Gửi request đến API
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(apiUrl);
    http.addHeader("Content-Type", "application/json");
    
    // Tạo JSON payload
    String jsonData = "{\"image\":\"" + base64Image + "\"}";
    
    Serial.println("Sending request to API...");
    int httpResponseCode = http.POST(jsonData);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("HTTP Response code: " + String(httpResponseCode));
      Serial.println("Response: " + response);
      
      // Parse JSON response
      parseResponse(response);
      
    } else {
      Serial.println("Error on sending POST: " + http.errorToString(httpResponseCode));
    }
    
    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }
  
  // Giải phóng buffer
  esp_camera_fb_return(fb);
}

void parseResponse(String response) {
  // Parse JSON response
  DynamicJsonDocument doc(2048);  // Tăng buffer size cho distance info
  DeserializationError error = deserializeJson(doc, response);
  
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Lấy thông tin từ response
  bool success = doc["success"];
  int detectedObjects = doc["detected_objects"];
  bool alertTriggered = doc["alert_triggered"];
  bool distanceEnabled = doc["distance_estimation_enabled"];
  
  Serial.println("=== Detection Results ===");
  Serial.println("Success: " + String(success));
  Serial.println("Detected objects: " + String(detectedObjects));
  Serial.println("Alert triggered: " + String(alertTriggered));
  Serial.println("Distance estimation: " + String(distanceEnabled));
  
  // Xử lý thông tin khoảng cách
  if (distanceEnabled && doc.containsKey("distance_info")) {
    JsonArray distanceArray = doc["distance_info"];
    Serial.println("Distance Information:");
    
    for (JsonObject obj : distanceArray) {
      int objectId = obj["object_id"];
      int classId = obj["class_id"];
      float distanceM = obj["distance_m"];
      String position = obj["position"].as<String>();
      
      Serial.print("  Object ");
      Serial.print(objectId);
      Serial.print(" (Class ");
      Serial.print(classId);
      Serial.print("): ");
      Serial.print(distanceM);
      Serial.print("m - ");
      Serial.println(position);
      
      // Xử lý theo khoảng cách
      if (distanceM < 2.0) {
        Serial.println("⚠️  WARNING: Person very close!");
      } else if (distanceM < 5.0) {
        Serial.println("⚠️  WARNING: Person close!");
      }
    }
  }
  
  // Xử lý cảnh báo
  if (alertTriggered) {
    Serial.println("🚨 DROWNING ALERT! 🚨");
    // Có thể thêm code để bật LED, buzzer, etc.
    handleAlert();
  }
  
  Serial.println("========================");
}

void handleAlert() {
  // Xử lý khi có cảnh báo đuối nước
  Serial.println("Emergency alert - Drowning detected!");
  
  // Có thể thêm:
  // - Bật LED đỏ
  // - Kích hoạt buzzer
  // - Gửi thêm thông tin
  // - Lưu log
}

// Hàm test kết nối API
void testAPIConnection() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin("http://" + String(serverName) + ":5000/health");
    
    int httpResponseCode = http.GET();
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("API Health Check: " + response);
    } else {
      Serial.println("Error on HTTP request");
    }
    
    http.end();
  }
}

// Hàm calibrate camera
void calibrateCamera() {
  Serial.println("Starting camera calibration...");
  
  // Chụp ảnh calibration
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed during calibration");
    return;
  }
  
  // Encode base64
  String base64Image = base64::encode(fb->buf, fb->len);
  
  // Gửi request calibration
  HTTPClient http;
  http.begin("http://" + String(serverName) + ":5000/calibrate_auto");
  http.addHeader("Content-Type", "application/json");
  
  // Thông số calibration (cần điều chỉnh theo thực tế)
  String calibrationData = "{\"reference_distance_cm\":100,\"reference_width_cm\":50,\"reference_width_pixels\":200}";
  
  int httpResponseCode = http.POST(calibrationData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Calibration response: " + response);
    
    // Parse response
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error && doc["success"]) {
      Serial.println("Camera calibrated successfully!");
      float focalLength = doc["focal_length"];
      Serial.print("Focal length: ");
      Serial.println(focalLength);
    } else {
      Serial.println("Calibration failed!");
    }
  } else {
    Serial.println("Error during calibration");
  }
  
  http.end();
  esp_camera_fb_return(fb);
} 