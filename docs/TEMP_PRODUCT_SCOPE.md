# TEMP — Moce:AI Booth Rover Product Scope

> Temporary convergence note. Promote only confirmed decisions into `PRD.md`.

## Product question

How can a physical rover help a retail/event booth convert a passerby into a
consenting free-sample or free-membership claim safely and measurably?

## Locked direction

- **Scenario:** retail pop-up or event booth solicitation.
- **Problem:** limited staff cannot proactively engage every visitor; static QR/NFC
  signage is missed; the booth cannot see offer-to-claim conversion.
- **Product:** a consent-first rover that detects a nearby visitor, presents an
  approved offer, opens a phone flow via NFC/QR, and records the outcome.
- **First offer:** free sample or free membership; only one is used in the demo.
- **Safety boundary:** ESP32 owns motor safety and local emergency stop. Jev/cloud
  may choose approved copy/content but never motor, safety, payment, or claim truth.
- **Interaction boundary:** passive NTAG213 sticker + QR fallback opens a PWA;
  backend is the source of truth for a claim. No PN532 is required for P0.
- **Hardware UI:** OLED shows `PERCEIVE`, `DECIDE`, `ACT`, and `ERROR`; onboard LED
  is only a supplemental indicator.
- **Demo movement:** a stationary interaction point or a taped 1–2 m controlled
  lane; no free roaming in public space.

## Demo loop

```text
PERCEIVE: ToF sees a visitor in the interaction zone
  -> DECIDE: choose approved offer + reason code
  -> ACT: stop, display TAP, speak invitation
  -> phone taps NFC sticker / scans QR
  -> visitor explicitly presses Claim
  -> backend records success
  -> OLED/TTS confirms CLAIMED
  -> return to PERCEIVE
```

## Metrics

- Offer-to-claim interaction time
- Claim success rate
- ToF trigger with no claim (false-positive proxy)
- Negative events: duplicate prompt, tap timeout, invalid ToF, emergency stop,
  TTS failure, employee escalation
- Five consecutive complete demo runs

## Explicitly out of scope

- Production payment / Alipay integration
- Face recognition, camera identification, SLAM, local LLM, open-ended dialogue
- Cloud-controlled movement or emergency stopping

## Open decision

Choose the demo's first offer:

1. **Free sample** — lower friction; recommended for the first demo.
2. **Free membership** — stronger lead capture but requires a clearer privacy/consent flow.
