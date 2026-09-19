"""
server.py — Lightweight Host Server & Web Controller Dashboard
Zero-dependency HTTP server with live telemetry polling and actuation commands.
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from software.bridge import HardwareBridge

latest_telemetry = {"status": "waiting_for_data"}
bridge = None

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SZ Hackathon — Hardware Controller</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }
    .container { max-width: 800px; margin: 0 auto; }
    .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #334155; }
    h1 { margin-top: 0; color: #38bdf8; font-size: 24px; }
    h2 { font-size: 18px; color: #94a3b8; margin-top: 0; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .metric { background: #0f172a; padding: 16px; border-radius: 8px; border: 1px solid #334155; }
    .metric-val { font-size: 32px; font-weight: bold; color: #38bdf8; }
    .btn { background: #2563eb; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500; margin-right: 8px; }
    .btn:hover { background: #1d4ed8; }
    .btn-secondary { background: #475569; }
    .btn-secondary:hover { background: #334155; }
    pre { background: #090d16; padding: 12px; border-radius: 6px; overflow-x: auto; color: #a5f3fc; font-size: 13px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <h1>SZ Hackathon — Hardware Controller</h1>
      <p style="color: #94a3b8; margin: 0;">Live edge hardware telemetry and bidirectional actuation control.</p>
    </div>

    <div class="card">
      <h2>Real-time Telemetry</h2>
      <div class="grid">
        <div class="metric">
          <div style="color: #94a3b8; font-size: 12px;">TEMPERATURE</div>
          <div class="metric-val" id="val-temp">-- °C</div>
        </div>
        <div class="metric">
          <div style="color: #94a3b8; font-size: 12px;">DISTANCE</div>
          <div class="metric-val" id="val-dist">-- cm</div>
        </div>
      </div>
      <div style="margin-top: 16px;">
        <h3 style="font-size: 13px; color: #64748b;">RAW PACKET</h3>
        <pre id="raw-json">Listening...</pre>
      </div>
    </div>

    <div class="card">
      <h2>Actuation Controls</h2>
      <button class="btn" onclick="sendCommand('SET_ACTUATOR', {actuator: 'servo_pan', value: 0})">Servo 0°</button>
      <button class="btn" onclick="sendCommand('SET_ACTUATOR', {actuator: 'servo_pan', value: 90})">Servo 90° (Center)</button>
      <button class="btn" onclick="sendCommand('SET_ACTUATOR', {actuator: 'servo_pan', value: 180})">Servo 180°</button>
      <button class="btn btn-secondary" onclick="sendCommand('RESET')">Reset State</button>
    </div>
  </div>

  <script>
    async function fetchTelemetry() {
      try {
        const res = await fetch('/api/telemetry');
        const data = await res.json();
        document.getElementById('raw-json').textContent = JSON.stringify(data, null, 2);
        if (data.data) {
          if (data.data.temperature !== undefined) {
            document.getElementById('val-temp').textContent = data.data.temperature + ' °C';
          }
          if (data.data.distance_cm !== undefined) {
            document.getElementById('val-dist').textContent = data.data.distance_cm + ' cm';
          }
        }
      } catch (err) {}
    }

    async function sendCommand(cmd, params = {}) {
      await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd, params })
      });
    }

    setInterval(fetchTelemetry, 1000);
    fetchTelemetry();
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
            self.wfile.write(json.dumps({"status": "healthy", "simulate": bridge.simulate}).encode("utf-8"))
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
                self.wfile.write(json.dumps({"status": "command_dispatched"}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence routine access logs
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
