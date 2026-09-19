#include <Arduino.h>
#include <ArduinoJson.h>

// Baud rate
#define SERIAL_BAUD 115200

// Pin definitions
#define PIN_STATUS_LED 2
#define PIN_BUTTON 0

// State
unsigned long last_telemetry_time = 0;
const unsigned long TELEMETRY_INTERVAL_MS = 1000;
unsigned long seq = 0;
int servo_angle = 90;

void setup() {
    Serial.begin(SERIAL_BAUD);
    pinMode(PIN_STATUS_LED, OUTPUT);
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    digitalWrite(PIN_STATUS_LED, HIGH);
}

void processCommand(const String& line) {
    StaticJsonDocument<256> doc;
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
        } else if (strcmp(cmd, "SET_ACTUATOR") == 0) {
            servo_angle = params["value"] | 90;
            ack["status"] = "ok";
            ack["message"] = "Actuator updated";
        } else if (strcmp(cmd, "RESET") == 0) {
            servo_angle = 90;
            ack["status"] = "ok";
            ack["message"] = "Reset complete";
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
    StaticJsonDocument<256> doc;
    doc["type"] = "telemetry";
    doc["seq"] = seq;
    doc["timestamp_ms"] = millis();

    JsonObject data = doc.createNestedObject("data");
    // Synthetic or read from actual pins/sensors
    data["temperature"] = 25.0 + (analogRead(A0) % 20) / 10.0;
    data["distance_cm"] = 20.0;
    data["button_pressed"] = (digitalRead(PIN_BUTTON) == LOW);
    data["servo_angle"] = servo_angle;

    serializeJson(doc, Serial);
    Serial.println();
}

void loop() {
    // Read commands from host
    if (Serial.available()) {
        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line.length() > 0) {
            processCommand(line);
        }
    }

    // Emit periodic telemetry
    unsigned long now = millis();
    if (now - last_telemetry_time >= TELEMETRY_INTERVAL_MS) {
        last_telemetry_time = now;
        sendTelemetry();
    }
}
