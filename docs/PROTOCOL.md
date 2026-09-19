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

### 2.5 急停與復位 (`STOP` / `RESET`)
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
