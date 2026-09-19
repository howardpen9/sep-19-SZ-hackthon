# Hardware-Software Communication Protocol

Version: `1.0.0`  
Standard Framing: Newline-delimited JSON (`\n` terminated UTF-8 strings).

---

## 1. Frame Types

All packets must contain a top-level `"type"` field with one of:
- `telemetry` (MCU -> Host)
- `command` (Host -> MCU)
- `ack` (MCU -> Host)
- `event` (MCU -> Host)
- `error` (Bidirectional)

---

## 2. Packet Schemas

### 2.1 Telemetry (`telemetry`)
Sent periodically by the MCU (e.g., at 10Hz or on change).

```json
{
  "type": "telemetry",
  "seq": 42,
  "timestamp_ms": 104230,
  "data": {
    "temperature": 26.4,
    "distance_cm": 18.2,
    "button_pressed": false,
    "battery_pct": 98
  }
}
```

### 2.2 Command (`command`)
Sent by host to trigger hardware actuation or configuration.

```json
{
  "type": "command",
  "msg_id": "cmd-101",
  "cmd": "SET_ACTUATOR",
  "params": {
    "actuator": "servo_pan",
    "value": 90
  }
}
```

Standard Command Codes:
- `PING`: Connectivity check
- `SET_ACTUATOR`: Drive motor / servo / output pin
- `SET_LED`: Set status RGB LED color / pattern
- `RESET`: Reboot MCU state machine
- `CALIBRATE`: Run sensor zeroing calibration

### 2.3 Acknowledgment (`ack`)
Sent by MCU upon receiving and parsing a command.

```json
{
  "type": "ack",
  "msg_id": "cmd-101",
  "status": "ok",
  "message": "Actuator updated to 90"
}
```

### 2.4 Asynchronous Event (`event`)
Sent immediately when an interrupt or threshold trigger occurs.

```json
{
  "type": "event",
  "event_name": "THRESHOLD_EXCEEDED",
  "details": {
    "sensor": "vibration",
    "val": 890,
    "limit": 500
  }
}
```

### 2.5 Error (`error`)

```json
{
  "type": "error",
  "code": "INVALID_PARAM",
  "message": "Servo angle must be between 0 and 180"
}
```
