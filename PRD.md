# Product Requirements Document (PRD)

## 1. Project Summary

- **Event**: Shenzhen Hackathon (2026-09-19)
- **Domain**: Hardware-Software Integration & Intelligent Edge Agent
- **Core Value**: Seamless physical-world interaction driven by software intelligence.

---

## 2. Problem Statement & Target Persona

- **Problem**: Hardware prototypes are often difficult to demo cleanly, lack real-time responsive software/AI feedback loops, and suffer from brittle serial connections.
- **Solution**: A robust hardware-software system pairing microcontroller edge sensing/actuation with an intuitive real-time dashboard and AI decision-making.

---

## 3. Hackathon Scope & Milestones

### Phase 1: Foundation (Hours 0 - 4)
- [x] Workspace repository scaffolded per Orca OS conventions
- [x] Protocol specification and framing rules defined
- [x] Virtual mock simulator operational for unblocked software development

### Phase 2: Core Hardware & Host Driver (Hours 4 - 10)
- [ ] MCU firmware reading sensors and sending valid telemetry packets
- [ ] Host bridge connected via Serial/UART with auto-reconnect
- [ ] Host API routing real-time telemetry to state engine

### Phase 3: Actuation & Intelligence (Hours 10 - 18)
- [ ] Bidirectional command dispatch (Host -> MCU -> Actuators)
- [ ] AI agent / reasoning loop evaluating sensor inputs and triggering actions
- [ ] Real-time UI dashboard showing live state and control toggles

### Phase 4: Polish & Demo Rehearsal (Hours 18 - 24)
- [ ] 60-second bulletproof demo script locked
- [ ] Fallback simulator hotkey configured in case of physical cable glitches during stage demo
- [ ] Visual asset / slide deck aligned with live system

---

## 4. Feature Matrix (MVP vs Scope-Cut)

| Feature | Tier | Status | Notes |
| --- | --- | --- | --- |
| Bidirectional Serial / JSON-Lines protocol | MVP (P0) | Defined | Foundation for all data exchange |
| Hardware Mock Simulator | MVP (P0) | Ready | Software dev unblocked from breadboard |
| Real-time Telemetry Web Dashboard | MVP (P0) | Planned | Clear visual feedback for judges |
| AI Decision / Agent Control Loop | MVP (P0) | Planned | Differentiator for intelligence |
| Bluetooth LE / Wireless OTA | Scope-Cut (P2) | Optional | Fall back to reliable wired USB-UART |
| Multi-device mesh networking | Scope-Cut (P3) | Dormant | Out of scope for hackathon demo |

---

## 5. 60-Second Stage Demo Script

1. **0:00 - 0:15 (The Hook)**: Introduce the physical device and the real-world problem it solves.
2. **0:15 - 0:35 (The Action)**: Trigger physical sensor input; show instantaneous telemetry visualization on screen.
3. **0:35 - 0:50 (The Intelligence)**: AI agent analyzes data, determines optimal intervention, and fires physical actuation command.
4. **0:50 - 1:00 (The Impact & Wrap)**: Physical actuator responds immediately; wrap with scalability and future roadmap.
