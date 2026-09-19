"""
server.py — Host Server & Web Controller for Moce:AI Robot
Real-time web dashboard with D-Pad motor drive, Pan/Tilt servos, ToF radar, TTS speech, and OLED controller.
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from software.bridge import HardwareBridge

latest_telemetry = {
    "type": "telemetry",
    "data": {
        "tof_distance_mm": 300,
        "imu": {"roll": 0, "pitch": 0, "yaw": 0},
        "environment": {"temp_c": 25.0, "humidity_pct": 60.0, "light_level": 400, "mic_level": 30},
        "actuators": {"left_motor": 0, "right_motor": 0, "pan": 90, "tilt": 45}
    }
}
bridge = None

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>SZ Hackathon — Moce:AI Edge Robot Controller</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #151d30;
      --card-border: #23314e;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.2);
      --danger: #ef4444;
      --success: #10b981;
      --warning: #f59e0b;
    }
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 24px;
    }
    .container { max-width: 1000px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--card-border);
    }
    h1 { margin: 0; font-size: 22px; color: var(--accent); }
    .status-badge {
      font-size: 12px;
      padding: 4px 10px;
      border-radius: 9999px;
      background: #064e3b;
      color: #6ee7b7;
      border: 1px solid #059669;
    }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    @media (max-width: 768px) {
      .grid-2, .grid-4 { grid-template-columns: 1fr; }
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .card h2 {
      font-size: 16px;
      color: var(--text-muted);
      margin-top: 0;
      margin-bottom: 16px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .metric-box {
      background: #0c1220;
      padding: 12px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      text-align: center;
    }
    .metric-label { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
    .metric-val { font-size: 20px; font-weight: bold; color: var(--accent); }
    .tof-radar {
      background: #0c1220;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
      margin-bottom: 12px;
    }
    .tof-dist { font-size: 38px; font-weight: 800; color: #38bdf8; }
    .tof-status { font-size: 13px; font-weight: bold; color: var(--success); }
    .tof-warning { color: var(--danger) !important; }
    
    /* D-Pad Controller */
    .dpad {
      display: grid;
      grid-template-columns: 80px 80px 80px;
      grid-template-rows: 60px 60px 60px;
      gap: 10px;
      justify-content: center;
      margin: 16px auto;
    }
    .btn-ctrl {
      background: #1e293b;
      color: var(--text);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.1s;
    }
    .btn-ctrl:hover { background: #334155; border-color: var(--accent); }
    .btn-ctrl:active { transform: scale(0.95); background: var(--accent); color: #000; }
    .btn-stop { background: #7f1d1d; color: #fca5a5; border-color: #991b1b; }
    .btn-stop:hover { background: #991b1b; }
    
    /* Sliders & Inputs */
    .slider-group { margin-bottom: 14px; }
    .slider-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }
    input[type="range"] { width: 100%; accent-color: var(--accent); }
    .input-row { display: flex; gap: 8px; margin-bottom: 12px; }
    input[type="text"] {
      flex: 1;
      background: #0c1220;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px 14px;
      color: white;
      font-size: 14px;
    }
    .btn-action {
      background: #0284c7;
      color: white;
      border: none;
      border-radius: 6px;
      padding: 10px 18px;
      font-weight: bold;
      cursor: pointer;
    }
    .btn-action:hover { background: #0369a1; }
    pre {
      background: #090d16;
      padding: 12px;
      border-radius: 6px;
      color: #7dd3fc;
      font-size: 12px;
      overflow-x: auto;
      max-height: 120px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>Moce:AI 邊緣小車控制台</h1>
        <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">ESP32_Core + Shield V1 軟硬體整合架構</div>
      </div>
      <div id="conn-badge" class="status-badge">模擬器連線中 (SIM)</div>
    </header>

    <!-- Top Sensors -->
    <div class="card" style="margin-bottom: 20px;">
      <h2>即時感測指標 (Sensory Suite)</h2>
      <div class="grid-4">
        <div class="tof-radar" style="grid-column: span 2; margin-bottom: 0;">
          <div class="metric-label">ToF 雷射測距 (VL53L0X)</div>
          <div class="tof-dist" id="tof-val">320 mm</div>
          <div class="tof-status" id="tof-alert">安全前方無障礙</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">姿態 (IMU PITCH/ROLL)</div>
          <div class="metric-val" id="imu-val">P: 0° / R: 0°</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">環境溫濕度 (TEMP/HUM)</div>
          <div class="metric-val" id="env-val">25.0°C / 60%</div>
        </div>
      </div>
    </div>

    <!-- Middle Controls -->
    <div class="grid-2" style="margin-bottom: 20px;">
      <!-- Left: Locomotion -->
      <div class="card">
        <h2>雙直流馬達底盤 (TT Motors)</h2>
        <div class="dpad">
          <div></div>
          <button class="btn-ctrl" onclick="sendDrive(70, 70)">▲ 前進</button>
          <div></div>
          <button class="btn-ctrl" onclick="sendDrive(-50, 50)">◀ 左轉</button>
          <button class="btn-ctrl btn-stop" onclick="sendDrive(0, 0)">■ 停止</button>
          <button class="btn-ctrl" onclick="sendDrive(50, -50)">右轉 ▶</button>
          <div></div>
          <button class="btn-ctrl" onclick="sendDrive(-70, -70)">▼ 後退</button>
          <div></div>
        </div>
        <div style="text-align: center; font-size: 12px; color: var(--text-muted);">
          速度設定：左右輪差速驅動 · 支援負數倒退
        </div>
      </div>

      <!-- Right: Servos & Display -->
      <div class="card">
        <h2>MG90S 雙軸雲台舵機 (Pan / Tilt)</h2>
        <div class="slider-group">
          <div class="slider-header">
            <span>水平舵機 (Pan A1)</span>
            <span id="pan-label">90°</span>
          </div>
          <input type="range" min="0" max="180" value="90" id="pan-slider" oninput="onServoChange()">
        </div>
        <div class="slider-group">
          <div class="slider-header">
            <span>俯仰舵機 (Tilt A2)</span>
            <span id="tilt-label">45°</span>
          </div>
          <input type="range" min="0" max="180" value="45" id="tilt-slider" oninput="onServoChange()">
        </div>

        <h2 style="margin-top: 20px;">TTS 語音播報 & 0.96 OLED</h2>
        <div class="input-row">
          <input type="text" id="tts-input" placeholder="輸入要播報的語音 (Text_to_Speech)..." value="深圳黑客松硬體已就緒">
          <button class="btn-action" onclick="sendTTS()">語音發音</button>
        </div>
        <div class="input-row">
          <input type="text" id="oled-input" placeholder="輸入 OLED 第1行文字..." value="HELLO SHENZHEN">
          <button class="btn-action" style="background: #475569;" onclick="sendOLED()">更新螢幕</button>
        </div>
      </div>
    </div>

    <!-- Bottom: Raw Telemetry -->
    <div class="card">
      <h2>通訊封包檢視器 (Raw JSON-Lines Frame)</h2>
      <pre id="raw-frame">Listening for telemetry...</pre>
    </div>
  </div>

  <script>
    async function sendCommand(cmd, params = {}) {
      try {
        await fetch('/api/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cmd, params })
        });
      } catch (err) {
        console.error("Command error:", err);
      }
    }

    function sendDrive(left, right) {
      sendCommand('SET_MOTOR', { left_speed: left, right_speed: right });
    }

    function onServoChange() {
      const pan = parseInt(document.getElementById('pan-slider').value);
      const tilt = parseInt(document.getElementById('tilt-slider').value);
      document.getElementById('pan-label').textContent = pan + '°';
      document.getElementById('tilt-label').textContent = tilt + '°';
      sendCommand('SET_SERVO', { pan, tilt });
    }

    function sendTTS() {
      const text = document.getElementById('tts-input').value;
      if (text) {
        sendCommand('SPEAK', { text });
      }
    }

    function sendOLED() {
      const line1 = document.getElementById('oled-input').value;
      sendCommand('DISPLAY_TEXT', { line1, line2: "STATUS: OK" });
    }

    async function pollTelemetry() {
      try {
        const res = await fetch('/api/telemetry');
        const data = await res.json();
        document.getElementById('raw-frame').textContent = JSON.stringify(data, null, 2);

        if (data && data.data) {
          const d = data.data;
          // ToF Radar
          if (d.tof_distance_mm !== undefined) {
            const dist = d.tof_distance_mm;
            document.getElementById('tof-val').textContent = dist + ' mm';
            const alertEl = document.getElementById('tof-alert');
            if (dist < 150) {
              alertEl.textContent = '⚠️ 前方障礙危險！';
              alertEl.className = 'tof-status tof-warning';
            } else {
              alertEl.textContent = '安全前方無障礙';
              alertEl.className = 'tof-status';
            }
          }

          // IMU
          if (d.imu) {
            document.getElementById('imu-val').textContent = `P: ${d.imu.pitch}° / R: ${d.imu.roll}°`;
          }

          // Environment
          if (d.environment) {
            document.getElementById('env-val').textContent = `${d.environment.temp_c}°C / ${d.environment.humidity_pct}%`;
          }
        }
      } catch (err) {}
    }

    setInterval(pollTelemetry, 1000);
    pollTelemetry();
  </script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif self.path == "/api/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(latest_telemetry).encode("utf-8"))
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "simulate": bridge.simulate if bridge else True}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/command":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                cmd = payload.get("cmd")
                params = payload.get("params", {})
                if bridge:
                    bridge.send_command(cmd, params)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "dispatched": cmd}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

def on_data_received(data):
    global latest_telemetry
    latest_telemetry = data

def main():
    global bridge
    port = int(os.environ.get("HOST_API_PORT", 8000))
    simulate = os.environ.get("SIMULATE_HARDWARE", "true").lower() in ("true", "1", "yes")
    serial_port = os.environ.get("SERIAL_PORT", "/dev/cu.usbserial-0001")
    baud = int(os.environ.get("SERIAL_BAUD_RATE", 115200))

    bridge = HardwareBridge(port=serial_port, baud=baud, simulate=simulate, on_telemetry=on_data_received)
    bridge.start()

    server = HTTPServer(("0.0.0.0", port), RequestHandler)
    print(f"[Server] Hardware Host Server listening on http://localhost:{port}")
    print(f"[Server] Mode: {'Simulation (Virtual Mock)' if simulate else f'Real Serial ({serial_port})'}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")
    finally:
        bridge.stop()
        server.server_close()

if __name__ == "__main__":
    main()
