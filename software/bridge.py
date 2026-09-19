"""
bridge.py — Hardware-Software Transport Bridge
Handles bidirectional serial communication with real or mock hardware.
"""

import os
import sys
import json
import time
import subprocess
import threading
from typing import Callable, Optional

class HardwareBridge:
    def __init__(
        self,
        port: str = "/dev/cu.usbserial-0001",
        baud: int = 115200,
        simulate: bool = True,
        on_telemetry: Optional[Callable[[dict], None]] = None,
    ):
        self.port = port
        self.baud = baud
        self.simulate = simulate
        self.on_telemetry = on_telemetry
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._proc: Optional[subprocess.Popen] = None
        self._serial = None
        self._command_lock = threading.Lock()

    def start(self):
        self.running = True
        if self.simulate:
            self._start_mock()
        else:
            self._start_serial()

    def _start_mock(self):
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "mock_hardware.py")
        self._proc = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._thread = threading.Thread(target=self._read_mock_loop, daemon=True)
        self._thread.start()

    def _read_mock_loop(self):
        while self.running and self._proc and self._proc.stdout:
            line = self._proc.stdout.readline()
            if not line:
                break
            self._handle_raw_line(line)

    def _start_serial(self):
        try:
            import serial
            self._serial = serial.Serial(self.port, self.baud, timeout=1.0)
            # Keep GPIO0 and EN released. A reset pulse here can leave this
            # USB-UART board in DOWNLOAD_BOOT instead of normal firmware mode.
            self._serial.dtr = False
            self._serial.rts = False
            self._thread = threading.Thread(target=self._read_serial_loop, daemon=True)
            self._thread.start()
        except ImportError:
            sys.stderr.write("[Bridge] Error: pyserial not installed. Falling back to simulation.\n")
            self.simulate = True
            self._start_mock()
        except Exception as e:
            sys.stderr.write(f"[Bridge] Serial connection error: {e}. Falling back to simulation.\n")
            self.simulate = True
            self._start_mock()

    def _read_serial_loop(self):
        while self.running and self._serial:
            try:
                line = self._serial.readline().decode("utf-8", errors="ignore")
                if line:
                    self._handle_raw_line(line)
            except Exception as e:
                if self.running:
                    sys.stderr.write(f"[Bridge] Read error: {e}\n")
                time.sleep(1.0)

    def _handle_raw_line(self, line: str):
        line = line.strip()
        if not line:
            return
        try:
            payload = json.loads(line)
            if self.on_telemetry:
                self.on_telemetry(payload)
            else:
                print(f"[Telemetry] {payload}")
        except json.JSONDecodeError:
            pass

    def send_command(self, cmd: str, params: Optional[dict] = None) -> None:
        params = dict(params or {})
        if cmd == "SPEAK":
            text = params.get("text", "")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("SPEAK requires non-empty text")
            encoded_text = text.encode("gbk")
            if len(encoded_text) > 200:
                raise ValueError("SPEAK supports at most 200 GBK bytes")
            params["gbk_hex"] = encoded_text.hex()
        packet = {
            "type": "command",
            "msg_id": f"cmd-{int(time.time() * 1000)}",
            "cmd": cmd,
            "params": params,
        }
        encoded = json.dumps(packet) + "\n"
        with self._command_lock:
            if self.simulate and self._proc and self._proc.stdin:
                self._proc.stdin.write(encoded)
                self._proc.stdin.flush()
            elif self._serial and self._serial.is_open:
                self._serial.write(encoded.encode("utf-8"))

    def stop(self):
        self.running = False
        if self._proc:
            self._proc.terminate()
        if self._serial:
            self._serial.close()
