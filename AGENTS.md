# AGENTS.md — Hardware-Software Integration Runbook

Read the **smallest** set of files for the job. Do not dump the entire tree into context.

## Routing Table

| Job | Read only |
| --- | --- |
| Hardware pinout & wiring | `hardware/PINOUT.md` + `hardware/BOM.md` |
| Firmware & MCU code | `firmware/` (PlatformIO / Arduino / MicroPython) |
| Hardware-Software protocol | `docs/PROTOCOL.md` + `ARCHITECTURE.md` |
| Software host / API / agent | `software/` |
| Mock hardware / simulator | `scripts/mock_hardware.py` |
| Product requirements & demo flow | `PRD.md` |

## Commands

```bash
# Setup environment
cp .env.example .env

# Run hardware mock simulator (for testing software without physical board)
python3 scripts/mock_hardware.py

# Run host backend / control service
python3 -m software.server    # or bash scripts/dev.sh

# Flash firmware (PlatformIO / esptool / Arduino CLI)
bash scripts/flash_firmware.sh
```

## Hard Rules

1. **One source of truth per protocol.** Packet frames and command codes are defined in `docs/PROTOCOL.md`. Neither firmware nor software may invent ad-hoc packets outside this spec.
2. **Mock-first hardware development.** Software and AI agent logic must always run with `SIMULATE_HARDWARE=true` via `scripts/mock_hardware.py` without requiring physical MCU plugged in.
3. **Never commit `.env` or raw credentials.** Keep API keys, WiFi passwords, and serial device paths in `.env.example` as placeholders only.
4. **Lean hackathon docs.** Prefer structured tables, Mermaid diagrams, and short bullet points. Do not write essays.
5. **No conflicting writers.** Only one active coding agent writes to the codebase at a time per Orca OS rules.
6. **Demo-ready gate.** Every feature must map directly to the demo flow specified in `PRD.md`.

## Agent Roles

| Role | Owns | Does not |
| --- | --- | --- |
| **Coordinator** | Architecture, task DAG, PRD alignment, demo verification | Direct unreviewed bulk refactors |
| **Firmware Agent** | MCU code, GPIO/I2C/SPI control, serial driver | Host UI/web logic |
| **Software Agent** | Host API, Serial/WebSocket bridge, data parser, frontend | Low-level register twiddling |
| **AI/Agentic Layer** | Multimodal reasoning, tool-calling dispatch, intent parsing | Direct hardware I/O bypass |

## Done Definition (Hackathon MVP)

- [ ] Firmware compiles cleanly and communicates over Serial / Protocol
- [ ] Mock simulator passes parity tests with physical protocol
- [ ] Host software receives telemetry and dispatches actuation commands
- [ ] End-to-end hardware-in-the-loop (or simulator) demo runnable within 60 seconds
- [ ] README contains 3-step setup and live demo verification steps
