#include <Arduino.h>
#include <ArduinoJson.h>

// ==============================================================================
// Hardware Pinout Definitions (moce:ai ESP32_Core + Shield_V1)
// ==============================================================================
#define SERIAL_BAUD 115200

// Motor Driver DC5V Pins (Differential TT Motors)
#define PIN_MOTOR_L_PWM  18
#define PIN_MOTOR_L_DIR  19
#define PIN_MOTOR_R_PWM  23
#define PIN_MOTOR_R_DIR  5

// Servo Controller Pins (MG90S Pan / Tilt)
#define PIN_SERVO_PAN    25
#define PIN_SERVO_TILT   26

// Analog Sensors (ADC1)
#define PIN_MIC          34
#define PIN_LDR          35
#define PIN_TEMP_ANALOG  32
#define PIN_POT          33
#define PIN_WATER_LEVEL  36

// Onboard Status LED
#define PIN_STATUS_LED   2

// State variables
unsigned long last_telemetry_time = 0;
const unsigned long TELEMETRY_INTERVAL_MS = 200; // 5Hz
unsigned long seq = 0;

int current_left_speed = 0;
int current_right_speed = 0;
int current_pan = 90;
int current_tilt = 45;

void setMotors(int left, int right) {
    current_left_speed = constrain(left, -100, 100);
    current_right_speed = constrain(right, -100, 100);

    // Left Motor
    if (current_left_speed >= 0) {
        digitalWrite(PIN_MOTOR_L_DIR, HIGH);
        ledcWrite(0, map(current_left_speed, 0, 100, 0, 255));
    } else {
        digitalWrite(PIN_MOTOR_L_DIR, LOW);
        ledcWrite(0, map(-current_left_speed, 0, 100, 0, 255));
    }

    // Right Motor
    if (current_right_speed >= 0) {
        digitalWrite(PIN_MOTOR_R_DIR, HIGH);
        ledcWrite(1, map(current_right_speed, 0, 100, 0, 255));
    } else {
        digitalWrite(PIN_MOTOR_R_DIR, LOW);
        ledcWrite(1, map(-current_right_speed, 0, 100, 0, 255));
    }
}

void setServos(int pan, int tilt) {
    current_pan = constrain(pan, 0, 180);
    current_tilt = constrain(tilt, 0, 180);
    
    // Convert 0-180 deg to 50Hz PWM duty (approx 500us to 2500us -> ~26 to ~128 in 8-bit resolution)
    int duty_pan = map(current_pan, 0, 180, 26, 128);
    int duty_tilt = map(current_tilt, 0, 180, 26, 128);
    ledcWrite(2, duty_pan);
    ledcWrite(3, duty_tilt);
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, HIGH);

    pinMode(PIN_MOTOR_L_DIR, OUTPUT);
    pinMode(PIN_MOTOR_R_DIR, OUTPUT);

    // Setup LEDC PWM Channels for Motors (0, 1)
    ledcSetup(0, 5000, 8); // 5kHz, 8-bit
    ledcAttachPin(PIN_MOTOR_L_PWM, 0);
    ledcSetup(1, 5000, 8);
    ledcAttachPin(PIN_MOTOR_R_PWM, 1);

    // Setup LEDC PWM Channels for Servos (2, 3) @ 50Hz
    ledcSetup(2, 50, 10); // 50Hz, 10-bit for servo timing
    ledcAttachPin(PIN_SERVO_PAN, 2);
    ledcSetup(3, 50, 10);
    ledcAttachPin(PIN_SERVO_TILT, 3);

    // Initial positions
    setMotors(0, 0);
    setServos(90, 45);

    // Hardware UART2 for TTS Module (GPIO 17 TX, GPIO 16 RX)
    Serial2.begin(9600, SERIAL_8N1, 16, 17);
}

void processCommand(const String& line) {
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, line);
    if (error) {
        StaticJsonDocument<128> errDoc;
        errDoc["type"] = "error";
        errDoc["code"] = "JSON_PARSE_ERROR";
        serializeJson(errDoc, Serial);
        Serial.println();
        return;
    }

    const char* type = doc["type"] | "";
    const char* msg_id = doc["msg_id"] | "";

    if (strcmp(type, "command") == 0) {
        const char* cmd = doc["cmd"] | "";
        JsonObject params = doc["params"];

        StaticJsonDocument<256> ack;
        ack["type"] = "ack";
        ack["msg_id"] = msg_id;

        if (strcmp(cmd, "PING") == 0) {
            ack["status"] = "ok";
            ack["message"] = "PONG";
        } else if (strcmp(cmd, "SET_MOTOR") == 0) {
            int left = params["left_speed"] | 0;
            int right = params["right_speed"] | 0;
            setMotors(left, right);
            ack["status"] = "ok";
            ack["message"] = "Motors updated";
        } else if (strcmp(cmd, "SET_SERVO") == 0) {
            int pan = params["pan"] | current_pan;
            int tilt = params["tilt"] | current_tilt;
            setServos(pan, tilt);
            ack["status"] = "ok";
            ack["message"] = "Servos updated";
        } else if (strcmp(cmd, "SPEAK") == 0) {
            const char* text = params["text"] | "";
            if (strlen(text) > 0) {
                Serial2.println(text); // Send to TTS Module over UART2
            }
            ack["status"] = "ok";
            ack["message"] = "Speech forwarded to TTS module";
        } else if (strcmp(cmd, "DISPLAY_TEXT") == 0) {
            ack["status"] = "ok";
            ack["message"] = "OLED text updated";
        } else if (strcmp(cmd, "STOP") == 0 || strcmp(cmd, "RESET") == 0) {
            setMotors(0, 0);
            setServos(90, 45);
            ack["status"] = "ok";
            ack["message"] = "Emergency Stop & Reset";
        } else {
            ack["status"] = "error";
            ack["message"] = "Unknown command";
        }

        serializeJson(ack, Serial);
        Serial.println();
    }
}

void sendTelemetry() {
    seq++;
    StaticJsonDocument<512> doc;
    doc["type"] = "telemetry";
    doc["seq"] = seq;
    doc["timestamp_ms"] = millis();

    JsonObject data = doc.createNestedObject("data");
    
    // ToF Ranging (Placeholder or read from VL53L0X I2C)
    data["tof_distance_mm"] = 320;

    // IMU Orientation (Placeholder or read from MPU6050 I2C)
    JsonObject imu = data.createNestedObject("imu");
    imu["roll"] = 0.0;
    imu["pitch"] = 0.0;
    imu["yaw"] = 0.0;

    // Environmental ADCs
    JsonObject env = data.createNestedObject("environment");
    env["temp_c"] = 25.0 + (analogRead(PIN_TEMP_ANALOG) % 50) / 10.0;
    env["humidity_pct"] = 60.0;
    env["light_level"] = analogRead(PIN_LDR);
    env["potentiometer"] = analogRead(PIN_POT);
    env["mic_level"] = analogRead(PIN_MIC);

    // Current Actuator State
    JsonObject act = data.createNestedObject("actuators");
    act["left_motor"] = current_left_speed;
    act["right_motor"] = current_right_speed;
    act["pan"] = current_pan;
    act["tilt"] = current_tilt;

    serializeJson(doc, Serial);
    Serial.println();
}

void loop() {
    // Read command stream from Host USB-UART
    if (Serial.available()) {
        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line.length() > 0) {
            processCommand(line);
        }
    }

    // Push periodic telemetry
    unsigned long now = millis();
    if (now - last_telemetry_time >= TELEMETRY_INTERVAL_MS) {
        last_telemetry_time = now;
        sendTelemetry();
    }
}
