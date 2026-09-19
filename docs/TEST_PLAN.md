# Test Plan — Moce:AI Edge Rover

Version: `1.0.0` · Updated: 2026-09-19 (Shenzhen Hackathon)

> Lean, mock-first test plan. Every test maps to either a **protocol guarantee**, a **demo-flow step** (PRD §3), or a **known defect** found during codebase review. No physical hardware required for T1–T9; T10+ are hardware-in-the-loop gates.

---

## 0. Test Tiers & Environment

| Tier | Name | Needs Hardware? | Runner |
|---|---|---|---|
| T1–T3 | Protocol & framing | ❌ Mock only | `pytest` (to add) |
| T4–T5 | Bridge layer | ❌ Mock subprocess | `pytest` |
| T6–T7 | Host server / API | ❌ Mock only | `pytest` + `httpx` |
| T8–T9 | Mock↔Firmware parity | ❌ Mock + firmware build | `pytest` + `pio` |
| T10–T12 | Hardware-in-the-loop | ✅ ESP32 board | manual / scripted |

**Shared fixtures:** launch `scripts/mock_hardware.py` as a subprocess (same path `bridge.py` uses), pump JSON-Lines over stdin/stdout. No real serial port needed until T10.

---

## 1. Protocol & Framing Tests (T1–T3)

Source of truth: `docs/PROTOCOL.md` v1.1.0.

### T1 — JSON-Lines framing round-trip
| | |
|---|---|
| **Covers** | PROTOCOL §1 (newline-delimited UTF-8 JSON) |
| **Steps** | 1. Spawn mock. 2. Send `{"type":"command","msg_id":"t1","cmd":"PING"}` + `\n`. 3. Read one stdout line. |
| **Pass** | Response is valid JSON, ends with `\n`, contains `"type":"ack"` and `"msg_id":"t1"`. |
| **Fail signatures** | No `\n` (framing break) · non-JSON line · missing `type` field. |

### T2 — Command set conformance
| | |
|---|---|
| **Covers** | PROTOCOL §2.1–2.5 (SET_MOTOR / SET_SERVO / SPEAK / DISPLAY_TEXT / STOP) |
| **Steps** | For each command, send a well-formed packet; assert the mock returns `{"status":"ok"}` and mutates internal state. |
| **Pass** | All 5 commands ack `ok`; `SET_MOTOR` updates `actuators.left/right_motor`; `SET_SERVO` updates `pan/tilt`; `STOP` zeroes motors + resets servos to 90/45. |
| **Edge cases** | `left_speed` negative (reverse) · `pan` out of 0–180 (should clamp) · empty `text` for SPEAK. |

### T3 — Malformed input handling
| | |
|---|---|
| **Covers** | PROTOCOL §1 + ARCHITECTURE §4 (corrupt frame → discard, no crash) |
| **Steps** | Send: (a) garbage string, (b) truncated JSON `{`, (c) valid JSON with wrong `type`. |
| **Pass** | Mock emits `{"type":"error","code":"JSON_PARSE_ERROR"}` or `INVALID_TYPE` and **keeps running**; next valid command still works. |
| **Defect link** | Verifies the firmware `main.cpp:104-112` error path has mock parity. |

---

## 2. Bridge Layer Tests (T4–T5)

Source: `software/bridge.py`.

### T4 — Mock subprocess lifecycle & command dispatch
| | |
|---|---|
| **Covers** | AGENTS.md Done Definition (host dispatches actuation commands) |
| **Steps** | 1. `HardwareBridge(simulate=True).start()`. 2. `send_command("SET_MOTOR", {"left_speed":60,"right_speed":60})`. 3. Read next telemetry line. |
| **Pass** | Subprocess spawns, command is written to stdin, telemetry `actuators.left_motor==60` appears within 1.5 s. |
| **Defect link** | Exposes **D (ack pollution)** — see T5. |

### T5 — Telemetry vs ack routing  ⚠️ **REGRESSION FOR KNOWN BUG**
| | |
|---|---|
| **Covers** | `bridge.py:83-94` `_handle_raw_line` + `server.py:383-385` `on_data_received` |
| **Steps** | 1. Start bridge with `on_telemetry` callback recording last payload. 2. Send a command (triggers an `ack`). 3. Inspect what the callback received. |
| **Expected (current buggy behavior)** | Callback fires for **every** line incl. `ack` → `latest_telemetry` gets overwritten by an ack (no `data` field). |
| **Desired behavior** | Callback should only fire for `type=="telemetry"`; `ack`/`error`/`event` routed separately. |
| **Pass (after fix)** | After a command, `latest_telemetry` still holds the last real telemetry `data` block, not the ack. |
| **Why it matters** | Demo [00:15–00:30] frequent button presses freeze the sensor panel for up to 1 s. |

---

## 3. Host Server / API Tests (T6–T7)

Source: `software/server.py`.

### T6 — HTTP endpoints
| | |
|---|---|
| **Covers** | `server.py` GET `/`, `/api/telemetry`, `/health`; POST `/api/command` |
| **Steps** | Hit each endpoint with `httpx`; assert status codes + content-type. |
| **Pass** | `/` → 200 `text/html`; `/api/telemetry` → 200 `application/json` with `data.tof_distance_mm`; `/health` → 200 with `simulate` flag; POST `/api/command` → 200 `{"status":"ok","dispatched":...}`. |
| **Edge** | POST with malformed JSON body → 400. |

### T7 — Telemetry freshness under load  ⚠️ **REGRESSION FOR KNOWN BUG**
| | |
|---|---|
| **Covers** | Defect **D** (ack pollution) + Defect **E** (frequency mismatch) |
| **Steps** | 1. Start server in sim mode. 2. Poll `/api/telemetry` every 200 ms for 10 s while firing 1 command/s. 3. Count responses where `data` field is missing. |
| **Pass (current)** | Will FAIL — expect ~10 polluted responses (acks without `data`). |
| **Pass (after fix)** | 0 polluted responses; every `/api/telemetry` returns a `data` block. |

---

## 4. Mock ↔ Firmware Parity Tests (T8–T9)

AGENTS.md Done Definition: *"Mock simulator passes parity tests with physical protocol."*

### T8 — Telemetry schema parity
| | |
|---|---|
| **Covers** | `main.cpp:165-200` vs `mock_hardware.py:44-67` vs `PROTOCOL.md §3` |
| **Steps** | Collect 5 telemetry packets from mock; collect 5 from firmware (via serial log capture or build-time stub). Diff the key set. |
| **Known drift** | Mock emits `imu.ax/ay/az`; firmware **omits** `ax/ay/az` (Defect **M**). Firmware `tof_distance_mm` hardcoded `320`; mock computes dynamically. |
| **Pass** | Both sides emit the **intersection** required by the dashboard: `tof_distance_mm`, `imu.{roll,pitch,yaw}`, `environment.{temp_c,humidity_pct,light_level,potentiometer,mic_level}`, `actuators.*`. |
| **Action** | Either add `ax/ay/az` to firmware or drop from PROTOCOL spec — pick one source of truth. |

### T9 — Telemetry frequency parity  ⚠️ **REGRESSION FOR KNOWN BUG**
| | |
|---|---|
| **Covers** | Defect **E** (three different rates) |
| **Steps** | Measure inter-packet interval for: firmware (`main.cpp:31` → 200 ms / 5 Hz), mock (`mock_hardware.py:70` → 1000 ms / 1 Hz), spec (`PROTOCOL.md:89` → 100 ms / 10 Hz). |
| **Pass (current)** | FAIL — three different values. |
| **Pass (after fix)** | All three agree on a single rate (recommend 200 ms / 5 Hz to match UI poll). |

---

## 5. Hardware-in-the-Loop Gates (T10–T12)

Require flashed ESP32 + `SIMULATE_HARDWARE=false`.

### T10 — Firmware compiles & flashes
| | |
|---|---|
| **Covers** | AGENTS.md Done Definition line 1 |
| **Steps** | `pio run -d firmware` (compile) → `pio run -t upload -d firmware` (flash). |
| **Pass** | Exit 0; `firmware.bin` produced; board resets and emits telemetry within 3 s. |
| **Note** | LEDC legacy API (`ledcSetup/ledcAttachPin/ledcWrite`) verified present in installed framework — compiles today. |

### T11 — Real serial round-trip
| | |
|---|---|
| **Covers** | ARCHITECTURE §2 (Serial JSON-Lines @ 115200) |
| **Steps** | Start server with real serial; send PING; read telemetry. |
| **Pass** | Ack received < 100 ms; telemetry at ~5 Hz. |
| **Defect link** | Exposes **F** — `Serial.readStringUntil('\n')` 1 s blocking timeout if host sends no newline. |

### T12 — 60-second demo flow  ⚠️ **END-TO-END GATE**
| | |
|---|---|
| **Covers** | PRD §3 (the actual demo script) |
| **Steps** | Run the 4 demo phases against hardware (or mock if board absent): |

| Time | Demo action | Test assertion | Current status |
|---|---|---|---|
| 00:00–00:15 | Power on, OLED shows ready, dashboard online | OLED displays text; `/health` 200 | ❌ OLED is a stub (Defect **B**) |
| 00:15–00:30 | Click Forward/Turn; move servo sliders | Motors move; servos respond; ack ok | ✅ Works in mock |
| 00:30–00:45 | Hand near ToF → distance drops → red warning + TTS | `tof<150` → UI red **and** auto-STOP **and** SPEAK | ❌ No auto-stop logic (Defect **A**); ToF hardcoded 320 (Defect **C**) |
| 00:45–01:00 | Architecture recap | n/a | ✅ |

---

## 6. Defect → Test Traceability

| Defect | Severity | Test that catches it | Fix location |
|---|---|---|---|
| **A** No active collision-avoidance / auto-stop | 🔴 | T12 [00:30–00:45] | `server.py` `on_data_received` + `main.cpp` |
| **B** OLED is a stub (no `Wire.begin`, no SSD1306) | 🔴 | T12 [00:00–00:15] | `main.cpp` setup + DISPLAY_TEXT handler |
| **C** I2C sensors uninit'd (ToF/IMU/temp-humidity) | 🔴 | T8, T12 | `main.cpp` setup + telemetry |
| **D** Ack packets pollute `latest_telemetry` | 🟠 | T5, T7 | `bridge.py:88-90` filter by `type` |
| **E** Telemetry rate 3-way mismatch | 🟠 | T9 | align `main.cpp:31`, `mock:70`, `PROTOCOL:89` |
| **F** `readStringUntil('\n')` 1 s blocking | 🟠 | T11 | `main.cpp:205` set timeout / non-blocking |
| **G** SPEAK `volume` param ignored | 🟠 | T2 edge | `main.cpp:140-144` |
| **H** No `requirements.txt` | 🟡 | setup gate | add manifest (pyserial) |
| **I** No tests exist | 🟡 | this doc | add `tests/` |
| **J** Mock subprocess crash = silent | 🟡 | T4 | `bridge.py:51-56` add restart/backoff |
| **K** `.env` shell load unsafe with spaces | 🟡 | — | `scripts/*.sh` use `set -a; . .env` |
| **L** Single-threaded HTTP server | 🟡 | T6 under load | `server.py:397` (acceptable for hackathon) |
| **M** Telemetry schema drift (`ax/ay/az`) | 🟡 | T8 | align firmware ↔ spec |
| **N** `StaticJsonDocument` deprecated | 🟡 | T10 compile warning | `main.cpp` → `JsonDocument` |

---

## 7. Recommended Sprint Order (CP-value)

1. **Write T1–T3 + T5 + T7** as `pytest` cases — these catch Defects D, E, M with zero hardware. ~30 min.
2. **Fix D** (one-line filter in `bridge.py`) → T5/T7 go green. ~5 min.
3. **Add host-side auto-stop** (Defect A) → T12 [00:30–00:45] passes in mock. ~15 min.
4. **Align telemetry rate** (Defect E) → T9 green. ~5 min.
5. **OLED + I2C init** (Defects B, C) → T12 [00:00–00:15] passes on real board. ~30 min + wiring.

---

## 8. Open Questions (need user decision)

- [ ] Target telemetry rate: **5 Hz** (firmware current) or **10 Hz** (spec)? Affects T9 fix direction.
- [ ] Auto-stop: host-side (`server.py`) quick fix, or firmware-side (`main.cpp`) for real safety? Affects T12.
- [ ] OLED library: Adafruit_SSD1306 + `Wire`, or keep stubbed for hackathon? Affects T10/T12.

---

## 9. Authorship & Model Attribution

| Field | Value |
|---|---|
| **Produced by** | Claude |
| **Model provider** | Anthropic |
| **Model** | Claude (running in a Claude Code session) |
| **Date** | 2026-09-19 (Shenzhen Hackathon) |
| **Task** | Codebase review + test plan authoring — **analysis only, no source code modified** |
| **Scope** | Read all 17 tracked files + verified toolchain (PlatformIO 6.2.0, arduino-esp32 framework) + cross-checked LEDC legacy API against installed framework headers + git status audit |
| **Method** | Cross-referenced `main.cpp`, `bridge.py`, `server.py`, `mock_hardware.py` against `PROTOCOL.md` v1.1.0, `PRD.md` §3 demo script, and `AGENTS.md` Done Definition. Verified critical claims (LEDC API presence, build artifacts, git hygiene) via shell inspection rather than assumption. |
| **Limitations** | Static analysis only — no firmware executed on real hardware. Defects A–N are source-level findings; T10–T12 require a physical ESP32 to confirm. T1–T9 are test *specifications*, not yet implemented as `pytest` code. |

> This document is a static analysis artifact. Defects A–N were identified by reading source, not by running tests. Re-verify line numbers after any code change before relying on the "Fix location" column in §6.
