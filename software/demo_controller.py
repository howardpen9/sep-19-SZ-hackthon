"""Deterministic coupon-rover demo state machine.

The controller is deliberately host-side: it only emits commands already
defined by docs/PROTOCOL.md, so the firmware protocol stays unchanged.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional


class CouponDemoController:
    DETECT_MM = 600
    OFFER_MM = 350
    EMERGENCY_STOP_MM = 150

    def __init__(self, send_command: Callable[[str, dict], None]):
        self._send_command = send_command
        self._lock = threading.RLock()
        self._state = "IDLE"
        self._running = False
        self._entered_at = time.monotonic()
        self._last_patrol_command = 0.0
        self._last_distance_mm: Optional[float] = None

    def status(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "state": self._state,
                "distance_mm": self._last_distance_mm,
                "thresholds_mm": {
                    "detect": self.DETECT_MM,
                    "offer": self.OFFER_MM,
                    "emergency_stop": self.EMERGENCY_STOP_MM,
                },
            }

    def start(self) -> None:
        with self._lock:
            self._running = True
            self._transition("PATROL")

    def stop(self) -> None:
        with self._lock:
            self._running = False
            self._transition("IDLE")

    def redeem_nfc(self) -> bool:
        """Accept a demo NFC tap only while the rover is offering a coupon."""
        with self._lock:
            if not self._running or self._state != "OFFER":
                return False
            self._transition("THANK_YOU")
            return True

    def on_telemetry(self, packet: dict) -> None:
        data = packet.get("data", {})
        distance = data.get("tof_distance_mm")
        if not isinstance(distance, (int, float)) or distance < 0:
            return

        with self._lock:
            self._last_distance_mm = distance
            if not self._running:
                return

            now = time.monotonic()
            if distance < self.EMERGENCY_STOP_MM:
                self._transition("SAFETY_STOP")
            elif self._state == "PATROL":
                if distance < self.DETECT_MM:
                    self._transition("APPROACH")
                elif now - self._last_patrol_command >= 1.0:
                    self._send_command("SET_MOTOR", {"left_speed": 30, "right_speed": 30})
                    self._last_patrol_command = now
            elif self._state == "APPROACH" and distance < self.OFFER_MM:
                self._transition("OFFER")
            elif self._state == "THANK_YOU" and now - self._entered_at >= 3.0:
                self._transition("RETREAT")
            elif self._state == "RETREAT" and now - self._entered_at >= 4.0:
                self._transition("PATROL")

    def _transition(self, state: str) -> None:
        self._state = state
        self._entered_at = time.monotonic()

        if state == "IDLE":
            self._send_command("STOP", {})
            self._send_command("DISPLAY_TEXT", {"line1": "MOCE:AI READY", "line2": "DEMO IDLE"})
        elif state == "PATROL":
            self._send_command("DISPLAY_TEXT", {"line1": "COUPON ROVER", "line2": "PATROLLING"})
            self._send_command("SET_MOTOR", {"left_speed": 30, "right_speed": 30})
            self._last_patrol_command = time.monotonic()
        elif state == "APPROACH":
            self._send_command("DISPLAY_TEXT", {"line1": "VISITOR NEAR", "line2": "APPROACHING"})
            self._send_command("SET_MOTOR", {"left_speed": 20, "right_speed": 20})
        elif state == "OFFER":
            self._send_command("STOP", {})
            self._send_command("DISPLAY_TEXT", {"line1": "TAP FOR COUPON", "line2": "NFC READY"})
            self._send_command("SPEAK", {"text": "您好，要不要拿優惠券？請碰一下 NFC。", "volume": 80})
        elif state == "THANK_YOU":
            self._send_command("STOP", {})
            self._send_command("DISPLAY_TEXT", {"line1": "COUPON CLAIMED", "line2": "THANK YOU"})
            self._send_command("SPEAK", {"text": "優惠券已領取，謝謝您。", "volume": 80})
        elif state == "RETREAT":
            self._send_command("DISPLAY_TEXT", {"line1": "THANK YOU", "line2": "RESUMING ROUTE"})
            self._send_command("SET_MOTOR", {"left_speed": -50, "right_speed": -50})
        elif state == "SAFETY_STOP":
            self._send_command("STOP", {})
            self._send_command("DISPLAY_TEXT", {"line1": "SAFETY STOP", "line2": "OBJECT TOO CLOSE"})
