# Firmware vs. PINOUT 一致性審查報告

> **審查者**: Kimmy K. Lee（獨立觀察總結，未修改任何程式碼或文件）
> **日期**: 2026-09-19
> **範圍**: `firmware/src/main.cpp` vs `hardware/PINOUT.md`（輔以 `hardware/BOM.md`、`firmware/platformio.ini`）
> **目的**: 供其他 agent review / 決策用。本檔案僅記錄觀察結果與建議，**不代表已執行任何修改**。

---

## 1. 一致的部分（無需動作）

| 項目 | PINOUT.md | main.cpp | 狀態 |
|---|---|---|---|
| 馬達驅動 | L: PWM 18 / DIR 19；R: PWM 23 / DIR 5 | `PIN_MOTOR_L_PWM 18` 等，完全相同 | ✅ |
| 舵機 Pan/Tilt | GPIO 25 / 26 | `PIN_SERVO_PAN 25` / `PIN_SERVO_TILT 26` | ✅ |
| I2C 總線 | SDA 21 / SCL 22 | `Wire.begin(21, 22)` | ✅ |
| ADC（LDR/熱敏/旋鈕/水位） | 35 / 32 / 33 / 36 | `PIN_LDR 35` 等，完全相同 | ✅ |
| OLED 位址 | `0x3C` (SSD1306) | `oled.begin(SSD1306_SWITCHCAPVCC, 0x3C)` | ✅ |
| ToF 位址 | `0x29` | 一致，且實作了 L0X/L1X/L4CD 三型號 fallback 偵測 | ✅ |

---

## 2. 發現的問題（4 項）

### ⚠️ 問題 1：麥克風腳位文件與韌體矛盾
- **PINOUT.md** 寫：`Microphone Module` → `GPIO 34 (ADC1_CH6)`，且該文件明確要求「避開 WiFi 衝突的 ADC2」。
- **main.cpp:29** 實際使用：`#define PIN_MIC 12`（**GPIO12 = ADC2**）。
- main.cpp:26-28 的註解聲稱：mic 的 AO 走 UART_A，經硬體掃腳驗證在 GPIO12，並提醒「依賴 mic 輸入時需關閉 Wi-Fi」。
- **矛盾點**：文件與韌體各說各話；且若韌體為真，則違反了 PINOUT.md 自己定的 ADC2 規範。
- **建議**：先確認實機接線到底在哪支腳，再同步另一邊。若實機確為 GPIO12，PINOUT.md 需改寫並加註 ADC2/Wi-Fi 衝突警告。

### ⚠️ 問題 2：TTS UART TX/RX 定義顛倒
- **PINOUT.md §1.2** 寫：`TXD1 = GPIO16` → TTS RX；`RXD1 = GPIO17` ← TTS TX。
- **main.cpp:65**：`Serial2.begin(tts_baud, SERIAL_8N1, 16, 17)` —— Arduino API 參數序為 **(RX, TX)**，即韌體認定 RX=16、TX=17。
- main.cpp:182 註解更明確寫：「UART_A schematic: GPIO17 is TXD1 (to TTS RX), GPIO16 is RXD1」。
- **矛盾點**：兩份文件對 TX/RX 的腳位指派完全相反。韌體註解自稱依據 schematic，傾向韌體為準，但需有 schematic 或實測佐證。
- **建議**：核對 Shield_V1 / UART_A 原理圖後，修正錯誤的一方。

### ⚠️ 問題 3：遙測資料含假值（Placeholder）
- main.cpp:346-354：
  - `temp_c` = `25.0 + (analogRead(PIN_TEMP_ANALOG) % 50) / 10.0` —— 公式拼湊的假溫度，非真實換算。
  - `humidity_pct` 寫死 `60.0` —— 溫濕度感測器（I2C `0x38/0x44`）完全未讀取。
  - `imu` roll/pitch/yaw 全為 `0.0` —— IMU（MPU6050 等）未實作。
- **風險**：demo 時若評審或 agent 依賴這些欄位做決策，會拿到看似合理但無意義的數據。
- **相關阻塞**：BOM.md 中 IMU 晶片型號仍「⚠️ 半確認（待近拍晶片）」，選型未定前無法選 library。
- **建議**：在 PROTOCOL.md 或遙測 payload 中標記這些欄位為 placeholder；或儘快實作。

### 🔧 問題 4：小雜項
- **水位感測器未入遙測**：`PIN_WATER_LEVEL 36`（main.cpp:33）已定義，但 `sendTelemetry()` 從未 `analogRead` 它，遙測 JSON 無對應欄位。
- **過期註解**：main.cpp:150 註解寫「8-bit resolution」，但 `ledcSetup(2, 50, 10)`（main.cpp:173）實際為 **10-bit**。duty 映射 26~128 對 10-bit 才是正確的 500µs~2500µs，所以程式邏輯沒錯，純粹是註解過期會誤導後人。

---

## 3. 建議處理順序（供 review agent 參考）

1. **文件同步**（低風險，立即可做）：修正 PINOUT.md 的 mic 腳位與 TTS TX/RX —— 但須先確認實機/原理圖以決定改哪邊。
2. **補水位感測器遙測**（低風險）：一行 `analogRead` + 一個 JSON 欄位。
3. **修正過期註解**（零風險）。
4. **實作 IMU + 溫濕度讀取**（中風險）：受 BOM.md 中 IMU 型號未確認阻塞，建議先近拍晶片絲印定案。

---

## 4. 免責聲明

本報告由 Kimmy K. Lee 於 2026-09-19 獨立完成，僅基於靜態程式碼閱讀，未上電實測、未修改任何檔案。所有「建議」需經 review agent / 硬體負責人確認後方可執行。
