# Hardware Pinout & Wiring Specification

主控平台：**ESP32_Core / moce:ai + ESP32_Shield_V1**  
電壓規範：核心邏輯 3.3V，動力與舵機 5V（由 Power_Management_V1 穩壓輸出）

---

## 1. 核心引腳分配 (Pin Assignments)

### 1.1 I2C 總線 (共用同一組 I2C，靠各模組位址區分)
- **SDA**: `GPIO 21` (外加 4.7kΩ 上拉電阻至 3.3V)
- **SCL**: `GPIO 22` (外加 4.7kΩ 上拉電阻至 3.3V)
- **掛載裝置**：
  1. `0.96 OLED (SSD1306)` (預設位址: `0x3C`)
  2. `IMU Module (MPU6050)` (預設位址: `0x68` 或 `0x69`)
  3. `ToF Laser Ranging (VL53L4CD)` (位址: `0x29`, model register: `0xEB`)
  4. `Temp&Humidity Sensor (SHT/AHT)` (預設位址: `0x38` 或 `0x44`)

### 1.2 輔助通訊串口 (UART)
- **USB-UART 主通訊 (對主機/Agent)**：
  - `TX0 (GPIO 1)` / `RX0 (GPIO 3)` @ 115200 bps
- **硬體串口 2 (對 TTS Module 語音模組 / CH32 橋接)**：
  - `TXD1 (GPIO 17)` $\rightarrow$ TTS Module RX
  - `RXD1 (GPIO 16)` $\leftarrow$ TTS Module TX (可選) @ 9600 或 115200 bps

### 1.3 馬達驅動 (Motor_Driver_Module_DC5V - 差速輪)
- **MOTOR1 (左輪 TT 馬達)**：
  - `PWMA`: `GPIO 25`
  - `AIN1 / AIN2`: `GPIO 27 / 14`
- **MOTOR2 (右輪 TT 馬達)**：
  - `PWMB`: `GPIO 26`
  - `BIN1 / BIN2`: `GPIO 12 / 13`

MOTOR1/2 對應實際左右與正反轉待架空校正，以上 A/B 訊號來自主板原理圖。

### 1.4 舵機控制 (Servo Controller Module - 雲台 Pan / Tilt)
- **PWM1 SERVO (Pan，待實測)**: `GPIO 32` (50Hz PWM)
- **PWM2 SERVO (Tilt，待實測)**: `GPIO 33` (50Hz PWM)

### 1.5 模擬類比輸入 (ADC Channel 1 - 避開 WiFi 衝突的 ADC2)
- **Microphone Module (音量感測)**: `GPIO 34 (ADC1_CH6)`
- **LDR_Module (光敏電阻)**: `GPIO 35 (ADC1_CH7)`
- **Thermistor / Temp (熱敏電阻)**: `GPIO 32 (ADC1_CH4)`
- **Potentiometer / 旋鈕**: `GPIO 33 (ADC1_CH5)`
- **Water_Level_Sensor**: `GPIO 36 / SENSOR_VP (ADC1_CH0)`

---

## 2. 接線圖解與防呆

```text
[ 11.1V 3S 電池 ]
       │
       ▼ (DC / XT30)
[ Power_Management_V1 ]
  ├── 5V Rail (高電流) ───────► [ Motor Driver DC5V ] ──► [ TT 馬達左右輪 ×2 ]
  │                           └──► [ Servo Controller ]  ──► [ MG90S 舵機 ×2 ]
  │
  └── 3.3V Rail (乾淨邏輯) ───► [ ESP32_Core / Shield_V1 ]
                                ├── I2C Bus (GPIO 21/22) ──► OLED / IMU / ToF / 溫濕度
                                ├── UART2 (TX GPIO17 / RX GPIO16) ──► TTS 語音播報模組
                                └── ADC Inputs (GPIO 32~36) ─► Mic / 光敏 / 旋鈕
```
