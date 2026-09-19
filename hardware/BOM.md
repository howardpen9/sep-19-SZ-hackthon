# Bill of Materials (BOM) & Inventory Status

Updated: 2026-09-19 (Shenzhen Hackathon)

## 1. Core Compute & Power Architecture

| Item | Module / Part # | Qty | Status | Interfaces / Rails | Notes & Power Warning |
|---|---|---|---|---|---|
| 1 | **ESP32_Core / moce:ai** | 1 | ✅ 確認 | Type-C, SHIELD 雙排針 | 主控 MCU，負責感測、通訊與運算編排 |
| 2 | **ESP32_Shield_V1** | 1 | ✅ 確認 | 排母插座、各模組接腳引出 | 底板轉接擴展板 |
| 3 | **Power_Management_V1** | 1 | ✅ 確認 (背面) | 11.1V IN, 5V / 3.3V OUT | ⚠️ 必經降壓！嚴禁將 11.1V 直接送入 5V/3.3V 模組 |
| 4 | **11.1V 3S 電池包** | 1 | ⚠️ 待核標籤 | XT30/XT60/DC 插頭 | 總電源輸入；需注意充放電保護與接頭極性 |

---

## 2. 執行機構 (Actuators & Motion)

| Item | Module / Part # | Qty | Status | Control Pin / Protocol | Electrical Specs |
|---|---|---|---|---|---|
| 5 | **Motor_Driver_Module_DC5V** | 1 | ✅ 確認 | MOTOR1 / MOTOR2 輸出 | 雙路直流電機驅動，接 TT 減速馬達 |
| 6 | **TT 減速馬達 + 橡膠輪** | 2 | ✅ 確認 | 兩線 (正/負) × 2 | 左右差速驅動小車底盤；先對線序確認轉向 |
| 7 | **Servo Controller Module** | 1 | ✅ 確認 | A1 / A2 SERVO_OUT_5V | 專用 5V 舵機控制板，隔離大電流突波 |
| 8 | **TowerPro MG90S 舵機** | 1~2 | ⚠️ 確認 1 顆 (待補 1) | 3-Pin (棕 GND, 紅 5V, 黃 PWM) | 雲台俯仰/水平控制 (4.8~6V 供電，嚴禁接 11.1V) |

---

## 3. 感測器模組 (Sensory Suite)

| Item | Module / Part # | Qty | Status | Interface / Pins | 用途 / 規格 |
|---|---|---|---|---|---|
| 9 | **IMU Module** | 1 | ⚠️ 半確認 (待近拍晶片) | I2C (SDA / SCL) | 六軸姿態檢測 (MPU6050 / LSM6DS 類) |
| 10 | **Laser_Ranging (ToF)** | 1 | ⚠️ 高度疑似 VL53L0X/L1X | I2C + 5V/GND/IO1/XSHUT | 前向障礙物精準毫米級測距 |
| 11 | **Microphone Module** | 1 | ✅ 確認 | Analog / Digital / I2S | 環境音量檢測、聲音事件捕捉 |
| 12 | **Temp&Humidity_Sensor** | 1 | ✅ 新增確認 (SHT/AHT/DHT) | I2C 或 單線數位 (IO) | 環境溫濕度採集 |
| 13 | **LDR_Module (光敏電阻)** | 1 | ✅ 新增確認 | Analog AO / Digital DO | 環境光照感測 |
| 14 | **Thermistor_Module (熱敏電阻)** | 1 | ✅ 新增確認 | Analog AO / Digital DO | 溫度監控 |
| 15 | **Water_Level_Sensor** | 1 | ✅ 前文已確認 | Analog AO | 液位 / 浸水感測 |
| 16 | **Potentiometer_Module** | 1 | ✅ 前文已確認 | 3-Pin (VCC/GND/ADC) | 實體旋鈕參數調校 / 人機互動輸入 |

---

## 4. 人機互動與音訊 (Display & Audio)

| Item | Module / Part # | Qty | Status | Interface | 用途 |
|---|---|---|---|---|---|
| 17 | **Text_to_Speech (TTS) Module** | 1 | ✅ 確認 | UART / Serial | 語音播報、智慧語音合成 |
| 18 | **0.96 OLED Display Module** | 1 | ✅ 確認 | I2C / FPC (SSD1306) | 表情顯示、IP/連線狀態、系統即時數據 |

---

## 5. 總線與通訊轉接板 (Bus Bridges)

| Item | Module / Part # | Qty | Status | Pinout | 用途 |
|---|---|---|---|---|---|
| 19 | **CH32 Module (I2C-CAN/UART)** | ≥3 | ✅ 確認 | 3V3 / GND / DIO / CLK / CAN IN / UART A | 模組間長距離通訊 / 協議橋接 |

---

## 6. 上電安全與檢查清單 (Safety Checklist)

1. **嚴禁 11.1V 直連邏輯板**：11.1V 鋰電池只能進 `Power_Management_V1` 的 BAT 輸入端，所有感測器與 ESP32 一律由穩壓後的 5V/3.3V 供電。
2. **MG90S 舵機接線**：
   - 棕色 (Brown) $\rightarrow$ GND
   - 紅色 (Red) $\rightarrow$ 5V (由 Servo Controller 供電，勿吃 ESP32 內部 3.3V LDO)
   - 黃色 (Yellow) $\rightarrow$ PWM 控制訊號線
3. **TT 馬達方向調試**：組裝後先低速發送 Forward，確認左右輪同向前進；若有單輪倒轉，直接反接該路馬達端子兩根線。
