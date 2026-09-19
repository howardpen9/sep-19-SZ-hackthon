# Product Requirements Document (PRD)

## 1. Project Summary

- **Event**: Shenzhen Hackathon (2026-09-19)
- **Project Name**: Moce:AI Multimodal Edge Rover & Intelligent Control Station
- **Hardware Stack**: `ESP32_Core / moce:ai` + `ESP32_Shield_V1` + `Power_Management_V1`
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
- [x] ESP32 固件框架 (`firmware/src/main.cpp`) 完成編譯準備
