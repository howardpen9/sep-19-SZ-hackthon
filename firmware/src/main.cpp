#include <Arduino.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <VL53L1X.h>
#include <vl53l4cd_class.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ==============================================================================
// Hardware Pinout Definitions (moce:ai ESP32_Core + Shield_V1)
// ==============================================================================
#define SERIAL_BAUD 115200
#define TTS_DEFAULT_BAUD 9600

// Motor Driver DC5V Pins (Differential TT Motors)
#define PIN_MOTOR_L_PWM  25
#define PIN_MOTOR_L_DIR  27
#define PIN_MOTOR_L_IN2  14
#define PIN_MOTOR_R_PWM  26
#define PIN_MOTOR_R_DIR  12
#define PIN_MOTOR_R_IN2  13

// Servo Controller Pins (MG90S Pan / Tilt)
#define PIN_SERVO_PAN    32
#define PIN_SERVO_TILT   33

// The microphone's AO lead is wired through UART_A and was verified by a
// hardware pin scan on GPIO12. GPIO12 is ADC2, so keep Wi-Fi disabled when
// relying on this mic input.
#define PIN_MIC          12
#define PIN_LDR          35
#define PIN_TEMP_ANALOG  32
#define PIN_POT          33
#define PIN_WATER_LEVEL  36

// Onboard Status LED
#define PIN_STATUS_LED   23

// State variables
unsigned long last_telemetry_time = 0;
const unsigned long TELEMETRY_INTERVAL_MS = 200; // 5Hz
unsigned long seq = 0;

int current_left_speed = 0;
int current_right_speed = 0;
unsigned long last_motor_command = 0;
const unsigned long MOTOR_TIMEOUT_MS = 500;
int current_pan = 90;
int current_tilt = 45;
Adafruit_VL53L0X tof;
bool tof_available = false;
VL53L1X tof_l1;
bool tof_l1_available = false;
VL53L4CD tof_l4(&Wire, -1);
bool tof_l4_available = false;
Adafruit_SSD1306 oled(128, 64, &Wire, -1);
bool oled_available = false;
uint8_t i2c_devices[16];
uint8_t i2c_device_count = 0;
int tof_l0_model_id = -1;
int tof_l1_model_id = -1;
unsigned long tts_baud = TTS_DEFAULT_BAUD;

void configureTts(unsigned long baud) {
    tts_baud = baud;
    Serial2.flush();
    // Arduino API order is RX pin, then TX pin.
    Serial2.begin(tts_baud, SERIAL_8N1, 16, 17);
}

void sendSyn6288(const uint8_t* text, size_t text_length) {
    // SYN6288: FD + 16-bit data length + command + parameter + text + XOR.
    // Data length includes command, parameter, text, and checksum.
    const uint16_t data_length = static_cast<uint16_t>(text_length + 3);
    const uint8_t length_high = static_cast<uint8_t>(data_length >> 8);
    const uint8_t length_low = static_cast<uint8_t>(data_length);
    const uint8_t command = 0x01;
    const uint8_t parameter = 0x01; // GBK text mode
    uint8_t checksum = 0xFD ^ length_high ^ length_low ^ command ^ parameter;
    Serial2.write(0xFD);
    Serial2.write(length_high);
    Serial2.write(length_low);
    Serial2.write(command);
    Serial2.write(parameter);
    Serial2.write(reinterpret_cast<const uint8_t*>(text), text_length);
    for (size_t i = 0; i < text_length; i++) {
        checksum ^= static_cast<uint8_t>(text[i]);
    }
    Serial2.write(checksum);
    Serial2.flush();
}

void sendSyn6288Ascii(const char* text) {
    sendSyn6288(reinterpret_cast<const uint8_t*>(text), strlen(text));
}

int hexDigit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

void scanI2cBus() {
    i2c_device_count = 0;
    for (uint8_t address = 1; address < 127; address++) {
        Wire.beginTransmission(address);
        if (Wire.endTransmission() == 0 && i2c_device_count < sizeof(i2c_devices)) {
            i2c_devices[i2c_device_count++] = address;
        }
    }
}

bool i2cAddressPresent(uint8_t address) {
    for (uint8_t i = 0; i < i2c_device_count; i++) {
        if (i2c_devices[i] == address) {
            return true;
        }
    }
    return false;
}

String captureTtsResponse(unsigned long timeout_ms, uint8_t &byte_count) {
    String response;
    byte_count = 0;
    const unsigned long started = millis();
    while (millis() - started < timeout_ms) {
        while (Serial2.available() && byte_count < 24) {
            const uint8_t value = Serial2.read();
            char hex[4];
            snprintf(hex, sizeof(hex), "%02X", value);
            if (response.length() > 0) response += " ";
            response += hex;
            byte_count++;
        }
        delay(1);
    }
    return response;
}

int readI2cRegister(uint8_t address, uint16_t reg, uint8_t register_width) {
    Wire.beginTransmission(address);
    if (register_width == 2) {
        Wire.write(static_cast<uint8_t>(reg >> 8));
    }
    Wire.write(static_cast<uint8_t>(reg));
    if (Wire.endTransmission(false) != 0 || Wire.requestFrom(static_cast<int>(address), 1) != 1) {
        return -1;
    }
    return Wire.read();
}

void showOledText(const char* line1, const char* line2) {
    if (!oled_available) {
        return;
    }
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    oled.setTextSize(2);
    oled.setCursor(0, 4);
    oled.println(line1);
    oled.setTextSize(1);
    oled.setCursor(0, 38);
    oled.println(line2);
    oled.display();
}

void setMotors(int left, int right) {
    // Bench calibration: bounded low-duty pulses, renewed only by motor commands.
    ledcWrite(0, 0);
    ledcWrite(1, 0);
    current_left_speed = constrain(left, -50, 50);
    current_right_speed = constrain(right, -50, 50);
    last_motor_command = millis();
    digitalWrite(PIN_MOTOR_L_IN2, current_left_speed < 0 ? HIGH : LOW);
    digitalWrite(PIN_MOTOR_R_IN2, current_right_speed < 0 ? HIGH : LOW);

    // Left Motor
    if (current_left_speed >= 0) {
        digitalWrite(PIN_MOTOR_L_DIR, current_left_speed > 0 ? HIGH : LOW);
        ledcWrite(0, map(current_left_speed, 0, 100, 0, 255));
    } else {
        digitalWrite(PIN_MOTOR_L_DIR, LOW);
        ledcWrite(0, map(-current_left_speed, 0, 100, 0, 255));
    }

    // Right Motor
    if (current_right_speed >= 0) {
        digitalWrite(PIN_MOTOR_R_DIR, current_right_speed > 0 ? HIGH : LOW);
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
    pinMode(PIN_MOTOR_L_IN2, OUTPUT);
    pinMode(PIN_MOTOR_R_IN2, OUTPUT);
    digitalWrite(PIN_MOTOR_L_DIR, LOW);
    digitalWrite(PIN_MOTOR_R_DIR, LOW);
    digitalWrite(PIN_MOTOR_L_IN2, LOW);
    digitalWrite(PIN_MOTOR_R_IN2, LOW);

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

    // UART_A schematic: GPIO17 is TXD1 (to TTS RX), GPIO16 is RXD1 (from TTS TX).
    configureTts(TTS_DEFAULT_BAUD);

    Wire.begin(21, 22);
    // Do not let an unplugged or miswired I2C module block the rover boot.
    Wire.setTimeOut(50);
    scanI2cBus();
    Wire.beginTransmission(0x29);
    const bool tof_detected = Wire.endTransmission() == 0;
    // Read-only silicon identity probes. VL53L0X model ID is at 0xC0 (0xEE);
    // VL53L1X model ID is at 0x010F (0xEA).
    if (tof_detected) {
        tof_l0_model_id = readI2cRegister(0x29, 0x00C0, 1);
        tof_l1_model_id = readI2cRegister(0x29, 0x010F, 2);
    }
    tof_available = tof_detected && tof.begin();
    if (tof_detected && !tof_available) {
        // Both VL53L0X and VL53L1X use I2C address 0x29 and expose IO1/XSHUT.
        // Try L1X only after L0X rejects the sensor identity.
        tof_l1.setTimeout(100);
        tof_l1_available = tof_l1.init();
        if (tof_l1_available) {
            tof_l1.setDistanceMode(VL53L1X::Long);
            tof_l1.setMeasurementTimingBudget(50000);
            tof_l1.startContinuous(50);
        }
    }
    if (tof_detected && !tof_available && !tof_l1_available && tof_l1_model_id == 0xEB) {
        tof_l4.begin();
        tof_l4_available = tof_l4.InitSensor() == 0;
        if (tof_l4_available) {
            tof_l4.VL53L4CD_SetRangeTiming(50, 0);
            tof_l4.VL53L4CD_StartRanging();
        }
    }

    oled_available = i2cAddressPresent(0x3C) && oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
    showOledText("MOCE:AI", oled_available ? "OLED ONLINE" : "OLED NOT FOUND");
}

void processCommand(const String& line) {
    StaticJsonDocument<2048> doc;
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
            const char* hex = params["gbk_hex"] | "";
            uint8_t bytes[200];
            size_t count = 0;
            bool valid = true;
            if (strlen(hex)) {
                const size_t n = strlen(hex);
                valid = n <= 400 && n % 2 == 0;
                for (size_t i = 0; valid && i < n; i += 2) {
                    int hi = hexDigit(hex[i]), lo = hexDigit(hex[i + 1]);
                    if (hi < 0 || lo < 0) valid = false;
                    else bytes[count++] = (hi << 4) | lo;
                }
            } else {
                count = strlen(text);
                valid = count > 0 && count <= sizeof(bytes);
                for (size_t i = 0; valid && i < count; ++i) {
                    bytes[i] = static_cast<uint8_t>(text[i]);
                    if (bytes[i] > 127) valid = false;
                }
            }
            if (valid && count > 0) {
                configureTts(TTS_DEFAULT_BAUD);
                while (Serial2.available()) Serial2.read();
                sendSyn6288(bytes, count);
                ack["status"] = "ok";
                ack["message"] = "SYN6288 GBK frame sent; playback not confirmed";
            } else {
                ack["status"] = "error";
                ack["message"] = "Use 1-200 GBK bytes in gbk_hex, or ASCII text";
            }
        } else if (strcmp(cmd, "TTS_DIAGNOSTIC") == 0) {
            setMotors(0, 0); // Diagnostic capture blocks for 500ms.
            const unsigned long requested_baud = params["baud"] | TTS_DEFAULT_BAUD;
            if (requested_baud != 9600 && requested_baud != 115200) {
                ack["status"] = "error";
                ack["message"] = "Unsupported TTS diagnostic baud; use 9600 or 115200";
            } else {
                configureTts(requested_baud);
                while (Serial2.available()) Serial2.read();
                // This targets the common SYN6288-compatible UART protocol.
                // ASCII avoids Chinese encoding as a confounding variable.
                sendSyn6288Ascii("HELLO");
                uint8_t rx_bytes = 0;
                const String response_hex = captureTtsResponse(500, rx_bytes);
                ack["status"] = "ok";
                ack["message"] = rx_bytes > 0
                    ? "TTS UART response captured"
                    : "TTS frame sent; no UART response within 500ms";
                ack["baud"] = tts_baud;
                ack["rx_bytes"] = rx_bytes;
                ack["rx_hex"] = response_hex;
            }
        } else if (strcmp(cmd, "DISPLAY_TEXT") == 0) {
            const char* line1 = params["line1"] | "";
            const char* line2 = params["line2"] | "";
            showOledText(line1, line2);
            ack["status"] = oled_available ? "ok" : "error";
            ack["message"] = oled_available ? "OLED text updated" : "OLED not detected at I2C 0x3C";
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
    
    // ToF Ranging. -1 means the module was not detected or returned an invalid range.
    int tof_distance_mm = -1;
    if (tof_available) {
        VL53L0X_RangingMeasurementData_t measure;
        tof.rangingTest(&measure, false);
        if (measure.RangeStatus != 4) {
            tof_distance_mm = measure.RangeMilliMeter;
        }
    } else if (tof_l1_available) {
        tof_distance_mm = tof_l1.read();
        if (tof_l1.timeoutOccurred()) {
            tof_distance_mm = -1;
        }
    } else if (tof_l4_available) {
        uint8_t ready = 0;
        if (tof_l4.VL53L4CD_CheckForDataReady(&ready) == 0 && ready) {
            VL53L4CD_Result_t measure;
            if (tof_l4.VL53L4CD_GetResult(&measure) == 0 && measure.range_status == 0) {
                tof_distance_mm = measure.distance_mm;
            }
            tof_l4.VL53L4CD_ClearInterrupt();
        }
    }
    if (tof_distance_mm >= 0 && tof_distance_mm < 150) {
        setMotors(0, 0);
    }
    data["tof_distance_mm"] = tof_distance_mm;
    JsonArray i2c = data.createNestedArray("i2c_addresses");
    for (uint8_t i = 0; i < i2c_device_count; i++) {
        i2c.add(i2c_devices[i]);
    }
    JsonObject tof_probe = data.createNestedObject("tof_probe");
    tof_probe["l0x_model_id"] = tof_l0_model_id;
    tof_probe["l1x_model_id"] = tof_l1_model_id;

    // IMU Orientation (Placeholder or read from MPU6050 I2C)
    JsonObject imu = data.createNestedObject("imu");
    imu["roll"] = 0.0;
    imu["pitch"] = 0.0;
    imu["yaw"] = 0.0;

    // Environmental ADCs
    JsonObject env = data.createNestedObject("environment");
    env["temp_c"] = nullptr; // GPIO32 belongs to the servo, not a temperature ADC.
    env["humidity_pct"] = 60.0;
    env["light_level"] = analogRead(PIN_LDR);
    env["potentiometer"] = nullptr;
    env["mic_level"] = nullptr; // MIC is I2S; GPIO12 now drives BIN1.

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
    if ((current_left_speed || current_right_speed) &&
        millis() - last_motor_command >= MOTOR_TIMEOUT_MS) setMotors(0, 0);
    // Read command stream from Host USB-UART
    static String line;
    static bool overflow = false;
    for (int n = 0; n < 128 && Serial.available(); ++n) {
        char c = Serial.read();
        if (c == '\n') {
            if (!overflow && line.length()) processCommand(line);
            line = "";
            overflow = false;
        } else if (line.length() < 2048 && !overflow) line += c;
        else overflow = true;
    }

    // Push periodic telemetry
    unsigned long now = millis();
    if (now - last_telemetry_time >= TELEMETRY_INTERVAL_MS) {
        last_telemetry_time = now;
        sendTelemetry();
    }
}
