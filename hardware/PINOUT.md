# Hardware Pinout & Wiring Specification

Target MCU: **ESP32 DevKit / Arduino Compatible**

## 1. Pin Assignment Table

| Pin Name | GPIO | Type | Connected Peripheral | Voltage | Notes |
| --- | --- | --- | --- | --- | --- |
| TX0 | GPIO 1 | UART TX | Host USB-UART Bridge | 3.3V | Default serial telemetry |
| RX0 | GPIO 3 | UART RX | Host USB-UART Bridge | 3.3V | Default serial commands |
| SDA | GPIO 21 | I2C Data | Sensor Bus (OLED / IMU) | 3.3V | 4.7kΩ pull-up to 3.3V |
| SCL | GPIO 22 | I2C Clock | Sensor Bus (OLED / IMU) | 3.3V | 4.7kΩ pull-up to 3.3V |
| PWM_1 | GPIO 18 | PWM Out | Actuator / Servo 1 | 5V / 3.3V | 50Hz for servo |
| LED_STATUS | GPIO 2 | Digital Out | Onboard / Indicator LED | 3.3V | High = Active |
| BTN_IN | GPIO 0 | Digital In | Emergency / Action Button | 3.3V | Active Low (Pull-up) |

## 2. Power Requirements

- **MCU Logic**: 3.3V regulated from USB 5V.
- **High-current Actuators (Motors/Servos)**: Powered via dedicated 5V/External rail with common ground to MCU. Do not draw high current directly from MCU 3.3V pin.
