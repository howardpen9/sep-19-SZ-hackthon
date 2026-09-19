# Hardware-Software Communication Protocol

Version: `1.1.0`  
Standard Framing: Newline-delimited JSON (`\n` terminated UTF-8 strings).  
Baud Rate: `115200` bps (8-N-1).

---

## 1. Frame Types

All packets must contain a top-level `"type"` field:
- `telemetry`: MCU $\rightarrow$ Host (sensor measurements, state, health)
- `command`: Host $\rightarrow$ MCU (actuation, voice, display, movement)
- `ack`: MCU $\rightarrow$ Host (acknowledgment of received command)
- `event`: MCU $\rightarrow$ Host (asynchronous alerts e.g. obstacle trigger, sound peak)
- `error`: Bidirectional (malformed command, param out of range)

---

## 2. Command Packets (Host $\rightarrow$ MCU)

### 2.1 雙輪差速驅動 (`SET_MOTOR`)
控制左右輪動力與轉向：
```json
{
  "type": "command",
  "msg_id": "cmd-001",
  "cmd": "SET_MOTOR",
  "params": {
    "left_speed": 60,
    "right_speed": 60
  }
}
```
*數值範圍*：`-100` (全速後退) 到 `100` (全速前進)，`0` 為停止。

現場輪向校正模式：實體韌體將輸出限制為 ±50%；每次 SET_MOTOR 有效 500ms，未更新即停車。介面單擊為短脈衝，不是持續行駛。馬達 A：PWMA=25/AIN1=27/AIN2=14；B：PWMB=26/BIN1=12/BIN2=13。A/B 是否對應左右及正轉方向須架空驗證。GPIO32/33 為舵機；不再當類比感測讀取。此模式尚未提供已驗證的 ToF 防撞，禁止自主巡航。

### 2.2 雙軸雲台舵機 (`SET_SERVO`)
控制 MG90S 雲台角度：
```json
{
  "type": "command",
  "msg_id": "cmd-002",
  "cmd": "SET_SERVO",
  "params": {
    "pan": 90,
    "tilt": 45
  }
}
```
*數值範圍*：`pan` (水平) `0~180°`，`tilt` (俯仰) `0~180°`。

### 2.3 TTS 語音模組播報 (`SPEAK`)
觸發 Text_to_Speech 模組發音：
```json
{
  "type": "command",
  "msg_id": "cmd-003",
  "cmd": "SPEAK",
  "params": {
    "text": "檢測到前方向障礙物，已自動減速。",
    "volume": 80
  }
}
```

Host bridge 將 `text` 由 Unicode 嚴格轉為 GBK，新增 `params.gbk_hex`（十六進位字串，1–200 bytes）；不可編碼、空白或過長文字在發送前拒絕。直接 serial 呼叫若省略 `gbk_hex`，只接受 ASCII。`volume` 目前尚未套用。

TTS UART：9600 baud，RX GPIO16 / TX GPIO17。SYN6288 frame：`FD length_hi length_lo 01 01 <GBK bytes> XOR`；length＝文字 bytes＋3，XOR 為前面所有 bytes 的異或。ACK 僅表示已送出，不代表已發聲。

### 2.4 0.96 OLED 顯示內容 (`DISPLAY_TEXT`)
在 OLED 螢幕上顯示狀態或文字：
```json
{
  "type": "command",
  "msg_id": "cmd-004",
  "cmd": "DISPLAY_TEXT",
  "params": {
    "line1": "MOCE:AI ROBOT",
    "line2": "DIST: 124mm | OK"
  }
}
```

### 2.5 TTS UART 診斷 (`TTS_DIAGNOSTIC`)
僅供現場硬體排查。會切換 TTS UART baud rate，並送出含 XOR checksum 的 SYN6288-compatible ASCII `HELLO` frame；不控制馬達或其他裝置。

```json
{
  "type": "command",
  "msg_id": "cmd-tts-test-9600",
  "cmd": "TTS_DIAGNOSTIC",
  "params": { "baud": 9600 }
}
```

允許值：`9600`、`115200`。此測試驗證 SYN6288-compatible frame；無聲時再回頭確認 UART 實體 pin mapping 或晶片型號。

診斷 ACK 另含 `baud`、`rx_bytes`、`rx_hex`。`rx_bytes: 0` 表示 500 ms 內沒有收到模組回傳，不代表 ESP32 TX 一定未送出。

### 2.6 急停與復位 (`STOP` / `RESET`)
```json
{ "type": "command", "msg_id": "cmd-005", "cmd": "STOP" }
```

---

## 3. Telemetry Packets (MCU $\rightarrow$ Host)

發送頻率：預設 10Hz (100ms) 或數值變化時推送。

```json
{
  "type": "telemetry",
  "seq": 1420,
  "timestamp_ms": 154030,
  "data": {
    "tof_distance_mm": 185,
    "i2c_addresses": [41, 60],
    "tof_probe": { "l0x_model_id": 238, "l1x_model_id": -1 },
    "imu": {
      "roll": 1.2,
      "pitch": -0.8,
      "yaw": 120.4,
      "ax": 0.02,
      "ay": -0.01,
      "az": 0.99
    },
    "environment": {
      "temp_c": 26.5,
      "humidity_pct": 62.0,
      "light_level": 420,
      "potentiometer": 512,
      "mic_level": 85
    },
    "actuators": {
      "left_motor": 0,
      "right_motor": 0,
      "pan": 90,
      "tilt": 45
    }
  }
}
```

---

## 4. Acknowledgment (`ack`)
```json
{
  "type": "ack",
  "msg_id": "cmd-001",
  "status": "ok",
  "message": "Motors set to (60, 60)"
}
```
