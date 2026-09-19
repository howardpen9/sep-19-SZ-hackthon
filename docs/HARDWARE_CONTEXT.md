# Long-term Hardware Context

Updated: 2026-09-19 (Asia/Shanghai)

Use this file as the first hardware handoff. It separates schematic facts from live-test evidence and experimental assumptions.

## 1. Board identity and live host

| Item | Confirmed value |
| --- | --- |
| Core | moce:ai `ESP32_Core`, ESP32-WROOM-32E, 4 MB flash, no PSRAM |
| Expansion | `ESP32_Shield_V1` |
| USB serial | `/dev/cu.usbserial-10` at 115200 |
| Host UI | `http://localhost:8000/` |
| Real hardware launch | `SIMULATE_HARDWARE=false SERIAL_PORT=/dev/cu.usbserial-10 HOST_API_PORT=8000 .venv/bin/python -m software.server` |
| Firmware upload | `pio run -d firmware --target upload --upload-port /dev/cu.usbserial-10` |

## 2. Schematic-confirmed ESP32 nets

These mappings were transcribed from the supplied mainboard schematics. They take priority over older guessed pinouts.

| Function | ESP32 GPIO / net |
| --- | --- |
| USB serial | TXD0 GPIO1, RXD0 GPIO3 |
| I2C | SCL GPIO22, SDA GPIO21 |
| UART_A | TXD1 GPIO17, RXD1 GPIO16 |
| CAN controller | CAN_TX GPIO5, CAN_RX GPIO4 |
| Status LED | GPIO23 |
| I2S | WS GPIO19, SCK GPIO18, SD GPIO2 (direction still to verify) |
| Analog | SENSOR_VP GPIO36, SENSOR_VN GPIO39, ADC3 GPIO34, ADC4 GPIO35 |
| Motor/control nets | PWM1 GPIO32, PWM2 GPIO33, PWMA GPIO25, PWMB GPIO26, AIN1 GPIO27, AIN2 GPIO14, BIN1 GPIO12, BIN2 GPIO13 |

### External connector order

| Connector | Pin 1 | Pin 2 | Pin 3 | Pin 4 |
| --- | --- | --- | --- | --- |
| I2C | VDD | SCL | SDA | GND |
| UART_A | VDD | TXD1 | RXD1 | GND |
| CAN | 3V3 | CANL | CANH | GND |

The separate schematic connectors labelled microphone and speaker use `3V3 / I2S_WS / I2S_SCK / I2S_SD / GND`. They are distinct from the UART Text-to-Speech module.

## 3. Hardware verified on the bench

| Component | Result | Evidence / driver |
| --- | --- | --- |
| USB host bridge | PASS | Real JSON-Lines telemetry increments continuously |
| LaserRange | PASS | I2C `0x29`; ID probe `0xEB`; VL53L4CD driver produced changing millimetre values |
| OLED direct to ESP32 I2C | PASS | SSD1306 `0x3C` displayed test text when directly attached |
| OLED through CAN + CH32 | NOT IMPLEMENTED | No ESP32 CAN driver, CAN message contract, or CH32 bridge firmware exists in this repo |
| TTS module power | PASS | Module blue LED lights |
| TTS UART/protocol | PASS | UART_A RX GPIO16/TX GPIO17 at 9600; checksum-correct SYN6288 frame returned `0x41` (accepted) |
| TTS speech | PASS with replacement module | Replacement speaker spoke `HELLO`; original speaker module is faulty |
| Microphone | UNRESOLVED | Earlier GPIO12 reading conflicts with schematic: GPIO12 is `BIN1`; dedicated microphone connector is I2S |

## 3a. CH32 module identification (photo record)

The supplied close-up shows a CH32 bridge board with:

- top debug header labelled `3V3 / GND / DIO / CLK`;
- lower connectors labelled `CAN IN` and `UART_A`;
- separate connectors labelled `SPI` and `I2C`;
- a WCH `CH32` MCU marking that appears to read `CH32V203` in the available photo, but this part number is **not yet optically confirmed**.

This board has no USB connector. Programming therefore requires a compatible WCH-Link/debug probe on the four-pin header. `CAN IN` is a runtime data connector, not a programming port. The I2C OLED can only be remote-controlled after CH32 firmware and an ESP32 CAN frame contract are available.

## 4. Critical current-code warnings

Do not treat all constants in `firmware/src/main.cpp` as proven hardware mappings.

| Area | Current issue |
| --- | --- |
| Motors | Firmware now uses PWMA25/AIN1 27/AIN2 14 and PWMB26/BIN1 12/BIN2 13; servos32/33, LED23. Manual calibration caps duty at 50% and expires motor commands after ~500ms. Original board wheel directions were confirmed by user; replacement board motion remains unresolved. Test wheels raised. Autonomous start is disabled. |
| Microphone | Telemetry is null until I2S capture exists; GPIO12 is BIN1 and must not be read as a microphone ADC. |
| OLED ACK | `OLED text updated` only means the SSD1306 write function ran. It does not prove a display ACK, especially through CH32/CAN. |
| CAN/CH32 | No TWAI/CAN implementation or CAN-to-I2C packet definition is present. Never claim the bridge works from an HTTP ACK. |
| TTS | Correct Arduino UART call is `Serial2.begin(baud, SERIAL_8N1, 16, 17)` because arguments are `(RX, TX)`. `SPEAK` now uses host GBK encoding (`gbk_hex`) and checksummed SYN6288 framing at 9600 baud. Chinese playback still requires listening confirmation; ACK means frame sent only. |

## 5. Proven interface topology

```text
Browser :8000
  -> Python host
  -> USB serial JSON-Lines @ 115200
  -> ESP32
       -> I2C GPIO21/22 -> VL53L4CD or direct OLED
       -> UART_A TX GPIO17 / RX GPIO16 -> TTS module (protocol unresolved)
       -> CAN TX GPIO5 / RX GPIO4 -> CH32 bridge (software missing)
```

I2C can electrically share OLED `0x3C` and LaserRange `0x29`, but the current hardware has only one convenient socket. Use a verified parallel splitter for both; do not assume CAN creates a transparent I2C extension.

## 6. Next safe work order

1. Obtain the exact CH32 chip model/toolchain, then write the CAN-to-I2C firmware and define its frames in `docs/PROTOCOL.md`.
2. Reconcile motor and microphone pins against the schematic before energizing motors.
3. Convert production `SPEAK` content to the confirmed checksummed SYN6288 framing and supported text encoding.

## 7. Source-of-truth rules

- Host protocol: `docs/PROTOCOL.md`.
- Wiring target: this file plus `hardware/PINOUT.md`; unresolved conflicts stay marked, not guessed.
- Physical success requires observed hardware behavior, not only an ESP32 ACK.
- Power-cycle before moving VDD/GND connectors. Never feed the 11.1 V battery directly to logic modules.
