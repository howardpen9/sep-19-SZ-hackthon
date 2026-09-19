# Product Requirements Document (PRD)

## 1. Project Summary

- **Event**: Shenzhen Hackathon (2026-09-19)
- **Project Name**: Moce:AI Multimodal Edge Rover & Intelligent Control Station
- **Hardware Stack**: `ESP32_Core / moce:ai` + `ESP32_Shield_V1` + `Power_Management_V1`

### 1.1 主控確認規格 (Verified Silicon)

| 項目 | 確認值 (照片絲印鐵證) |
|---|---|
| 主控模組 | **ESPRESSIF ESP32-WROOM-32E**（原廠模組，非兼容版） |
| 運算 | 雙核 Xtensa LX6 @ 240MHz，無 NPU / 無 PSRAM |
| 無線 | Wi-Fi 802.11 b/g/n + 藍牙（BT Classic + BLE） |
| Flash / SRAM | **4MB Flash** / 約 520KB SRAM（可用 heap 約 250–300KB） |
| 燒錄/除錯 | Type-C（板上 USB 轉串口晶片）+ BOOT/RESET 按鍵 |
| 電源輸入 | 黃色 XT30 5V（來自 Power_Management_V1） |
| Core 底部出口 | `CAN_OUT` / `UART_A` / `I2C` 三個 JST 白座 |

> **韌體體積實測**：PlatformIO 6.2.0 編譯 = 289KB / 1.3MB（**22.1%**），RAM 6.6% — 部署空間綽綽有餘。

### 1.2 Shield_V1 接口全圖 (官方接線定案，模組插對插座即可)

| Shield 絲印 | 用途 | 掛載模組 |
|---|---|---|
| `I2C` | SDA/SCL 菊花鏈總線 | OLED(0x3C) / IMU(0x68) / ToF(0x29) / 溫濕度(0x38/0x44) |
| `UART_A` | 硬體串口 | TTS 語音模組、CH32 橋接板 |
| `CAN_OUT` ×3 (橘) | CAN 總線（ESP32 內建 TWAI） | 3 塊 CH32 節點板（⚠️ 每塊須先各自燒韌體） |
| `ADC1–ADC4` | 4 路類比輸入 (0–3.3V) | ⚠️ 5 件類比件（Mic/LDR/熱敏/水位/電位器）搶 4 位，取捨 1 件 |
| `MIC` / `SPK` | 麥克風入 / 喇叭出 | Microphone Module / TTS 喇叭 |
| `SERVO_OUT` / `MOTOR_OUT` | 各 2 路 PWM | Servo Controller (MG90S×2) / Motor Driver (TT 馬達×2) |
| 上下圓孔焊盤 | 各 10 孔 | 原型擴展（飛線/加感測器） |

### 1.3 硬體能力邊界 (Hard Limits — 不做幻想功能)

| 邊界 | 結論 |
|---|---|
| 「看到人」 | ✅ ToF 前向測距判有人靠近（< 80–100cm）；❌ 無鏡頭，**不做人臉識別** |
| 「聽懂回答」 | 簡單版 = 類比 Mic 判「有無聲音」；進階版 = I2S 錄音 → Wi-Fi 上雲端 ASR |
| ADC2 衝突 | 開 Wi-Fi 時 ADC2 失效 → 類比感測器全部走 ADC1 (GPIO32–39) |
| 本地 AI | 無 PSRAM/NPU → 不跑影像/神經網路，LLM 決策放主機端 Python |
- **Key Capabilities**: 
  1. **Locomotion**: 雙輪差速驅動底盤 (TT 馬達 + 橡膠輪)
  2. **Active Perception**: MG90S 雙軸雲台 (Pan/Tilt) + ToF 雷射測距 (VL53L0X) + IMU 姿態
  3. **Interaction**: TTS 語音即時合成播報 + 0.96 OLED 狀態螢幕 + Mic 環境音量感知
  4. **Brain / Software**: Python 雙向協議橋接 + 網頁即時儀表板 + LLM/邊緣決策 Agent

---

## 2. 核心功能規格 (MVP vs Phase 2)

| 模組 | MVP (P0) 交付規格 | Phase 2 (P1) 擴充 |
|---|---|---|
| **底盤動力** | 網頁 D-Pad 點擊/鍵盤控制前進、後退、左右轉與停止 | 閉環編碼器測速與定距巡航 |
| **雲台感知** | Pan/Tilt 舵機 0°~180° 滑桿即時聯動 | 自動 Pan 掃描建立前方距離雷達圖 |
| **主動防撞** | ToF 雷射測距 < 150mm 時自動觸發減速/急停 | 結合 IMU 檢測傾覆與劇烈撞擊 |
| **語音互動** | 網頁發送字串 $\rightarrow$ TTS 模組即時語音播報 | Mic 捕捉關鍵字喚醒語音問答 |
| **狀態可視化** | OLED 顯示機器人表情與 IP，網頁實時 Telemetry | 歷史數據折線圖與感測軌跡 |
| **開發解耦** | 全功能 Mock 模擬器，拔除實體板子時 UI 仍可完全操作 | 虛擬小車 2D Canvas 運動學模擬 |

---

## 3. 60 秒極速路演 Demo 腳本

```text
[00:00 - 00:15] 開場與硬體亮相
- 亮點：基於 moce:ai ESP32 核心與模組化 Shield，快速組裝具備感知、動力與語音的多模態邊緣實體。
- 動作：展示實體小車通電，OLED 顯示連線就緒，網頁儀表板同時上線。

[00:15 - 00:30] 即時控制與多模態回饋
- 動作：在電腦控制台點擊「前進」與「轉向」，小車即時運動；滑動雲台滑桿，MG90S 雲台靈敏轉動。
- 亮點：USB-UART JSON-Lines 協議低延遲雙向互通。

[00:30 - 00:45] 主動安全與環境感知
- 動作：手部靠近小車前方 ToF 雷射，網頁測距數字驟降並亮起紅色「⚠️ 前方障礙」警告。
- 語音聯動：系統自動觸發 TTS 模組播報：「前方檢測到障礙物，已自動減速避讓」。

[00:45 - 01:00] 總結與架構優勢
- 亮點：軟硬體完全解耦（Mock-First）、標準化通訊協議、兼具實體互動與 AI 決策延展性。
```

---

## 4. 驗收標準 (Definition of Done)

- [x] GitHub Private 倉庫已建置並推播 (`howardpen9/sep-19-SZ-hackthon`)
- [x] 硬體清單 (BOM) 與防呆安全檢查清單齊備
- [x] 完整引腳分配圖 (PINOUT) 對接 ESP32_Shield_V1
- [x] JSON-Lines 雙向控制協議 (`docs/PROTOCOL.md`) 規範完成
- [x] 免硬體 Mock 模擬器 (`scripts/mock_hardware.py`) 支援全套虛擬小車行為
- [x] 整合式網頁控制台 (`software/server.py`) 支援即時駕駛、舵機調整、語音與雷達數值
- [x] ESP32 固件框架 (`firmware/src/main.cpp`) **編譯驗證通過**（PlatformIO Core 6.2.0 @ macOS M2，Flash 22.1%）
