# Shenzhen Hackathon — Hardware-Software Integration Project

> **SZ Hackathon 2026-09-19** · High-velocity hardware-software integrated prototype.

---

## 1. Quick Start

### Step 1: Clone & Configure
```bash
cp .env.example .env
# Edit .env for your SERIAL_PORT (or leave SIMULATE_HARDWARE=true for local simulation)
```

### Step 2: Run Software with Mock Simulator
```bash
# Terminal 1: Run virtual hardware simulator
python3 scripts/mock_hardware.py

# Terminal 2: Run software host service / UI
bash scripts/dev.sh
```

### Step 3: Flash MCU (When ready for physical hardware)
```bash
bash scripts/flash_firmware.sh
```

### Manual rover demo (60 seconds)
1. Open `http://localhost:8000`. For physical hardware, start with `SIMULATE_HARDWARE=false SERIAL_PORT=<your-serial-port> .venv/bin/python -m software.server` and verify `/api/diagnostics` reports `hardware_mode: true` with advancing telemetry.
2. Verify wheel direction with wheels raised, then use the direction buttons in a clear demo lane. Each click requests a short pulse capped at 50% duty; the firmware stops after approximately 500 ms without another motor command. Autonomous demo start is disabled.
3. Stop, display an invitation on the OLED, and use the 9600 HELLO diagnostic or SPEAK button for audio. Chinese SPEAK uses GBK and still needs audible verification. A real NFC/QR phone claim flow is not implemented; describe any acted-out tap as a simulation.

USB-C carries host control; the motor board requires its own verified 5V supply. After unplugging USB, restart the host service to reconnect. See `docs/HARDWARE_CONTEXT.md` for hardware evidence and remaining limitations.

---

## 2. Architecture Overview

```mermaid
flowchart LR
    subgraph Hardware [Physical / Mock Hardware]
        Sensors[Sensors / Input] --> MCU[Microcontroller / ESP32 / Arduino]
        MCU --> Actuators[Actuators / Motors / Screen]
    end

    subgraph Interface [Transport Layer]
        MCU <--> |Serial / BLE / WiFi| Bridge[Transport Bridge / Driver]
    end

    subgraph Software [Host Software & AI Agent]
        Bridge <--> HostAPI[Host Backend / Server]
        HostAPI <--> AIAgent[AI / Multimodal Reasoning]
        HostAPI <--> WebUI[Web UI / Dashboard / Controller]
    end
```

See [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/PROTOCOL.md](docs/PROTOCOL.md) for frame specifications.

---

## 3. Directory Layout

```text
├── AGENTS.md            # Agent routing, commands, and rules
├── ARCHITECTURE.md      # System design, data flow, state machine
├── PRD.md               # Hackathon product definition & demo script
├── .env.example         # Parameter templates & hardware configs
├── hardware/            # Schematics, pinouts, BOM
│   ├── PINOUT.md
│   └── BOM.md
├── firmware/            # Embedded code (ESP32 / Arduino / PlatformIO)
├── software/            # Host service, protocol bridge, API, UI
├── docs/                # Protocol specs, API documentation
│   └── PROTOCOL.md
└── scripts/             # Dev, flash, simulator, and test scripts
    ├── mock_hardware.py
    ├── dev.sh
    └── flash_firmware.sh
```

---

## 4. Hardware Specifications

- **MCU**: ESP32 / STM32 / Arduino compatible
- **Baud Rate**: `115200`
- **Transport**: USB-UART Serial / WiFi / BLE
- Details in [hardware/PINOUT.md](hardware/PINOUT.md) and [hardware/BOM.md](hardware/BOM.md).
