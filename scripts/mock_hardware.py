#!/usr/bin/env python3
"""
mock_hardware.py — Virtual Hardware / MCU Simulator for Moce:AI Robot
Simulates dual DC motors, pan-tilt servos, ToF laser ranging, IMU, OLED, TTS, and sensors.
"""

import sys
import json
import time
import math
import random
import threading

running = True
seq_num = 0

state = {
    "actuators": {
        "left_motor": 0,
        "right_motor": 0,
        "pan": 90,
        "tilt": 45
    },
    "oled": {
        "line1": "MOCE:AI READY",
        "line2": "MOCK SIMULATOR"
    },
    "last_spoken": ""
}

def telemetry_emitter():
    global seq_num, running
    start_time = time.time()
    
    while running:
        seq_num += 1
        elapsed = time.time() - start_time
        
        # Calculate dynamic mock physics
        # If moving forward, distance decreases; else hovers around 200-400mm
        fwd_speed = (state["actuators"]["left_motor"] + state["actuators"]["right_motor"]) / 2.0
        base_dist = max(50.0, 350.0 - fwd_speed * 1.5 + random.uniform(-5.0, 5.0))

        packet = {
            "type": "telemetry",
            "seq": seq_num,
            "timestamp_ms": int(elapsed * 1000),
            "data": {
                "tof_distance_mm": round(base_dist, 1),
                "imu": {
                    "roll": round(math.sin(elapsed * 0.5) * 2.0, 2),
                    "pitch": round(math.cos(elapsed * 0.5) * 1.5, 2),
                    "yaw": round((elapsed * 5.0) % 360, 1),
                    "ax": round(random.uniform(-0.02, 0.02), 3),
                    "ay": round(random.uniform(-0.02, 0.02), 3),
                    "az": 1.002
                },
                "environment": {
                    "temp_c": round(25.0 + math.sin(elapsed / 10.0) * 2.0, 1),
                    "humidity_pct": round(58.0 + math.cos(elapsed / 8.0) * 3.0, 1),
                    "light_level": int(400 + random.uniform(-20, 20)),
                    "potentiometer": 512,
                    "mic_level": int(random.uniform(20, 95))
                },
                "actuators": state["actuators"]
            }
        }
        sys.stdout.write(json.dumps(packet) + "\n")
        sys.stdout.flush()
        time.sleep(1.0)

def command_receiver():
    global running, state
    
    for line in sys.stdin:
        if not running:
            break
        line = line.strip()
        if not line:
            continue
        try:
            cmd_packet = json.loads(line)
            cmd_type = cmd_packet.get("type")
            msg_id = cmd_packet.get("msg_id", f"msg-{int(time.time()*1000)}")
            
            if cmd_type == "command":
                cmd = cmd_packet.get("cmd")
                params = cmd_packet.get("params", {})
                
                if cmd == "PING":
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": "PONG"}
                elif cmd == "SET_MOTOR":
                    left = params.get("left_speed", 0)
                    right = params.get("right_speed", 0)
                    state["actuators"]["left_motor"] = left
                    state["actuators"]["right_motor"] = right
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": f"Motors set to L:{left}, R:{right}"}
                elif cmd == "SET_SERVO":
                    pan = params.get("pan", state["actuators"]["pan"])
                    tilt = params.get("tilt", state["actuators"]["tilt"])
                    state["actuators"]["pan"] = pan
                    state["actuators"]["tilt"] = tilt
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": f"Servos set to Pan:{pan}°, Tilt:{tilt}°"}
                elif cmd == "SPEAK":
                    text = params.get("text", "")
                    state["last_spoken"] = text
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": f"TTS: '{text}'"}
                elif cmd == "DISPLAY_TEXT":
                    state["oled"]["line1"] = params.get("line1", "")
                    state["oled"]["line2"] = params.get("line2", "")
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": "OLED display updated"}
                elif cmd == "STOP" or cmd == "RESET":
                    state["actuators"]["left_motor"] = 0
                    state["actuators"]["right_motor"] = 0
                    state["actuators"]["pan"] = 90
                    state["actuators"]["tilt"] = 45
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": "Stopped & Reset"}
                else:
                    response = {"type": "error", "msg_id": msg_id, "code": "UNKNOWN_COMMAND", "message": f"Command '{cmd}' not recognized"}
            else:
                response = {"type": "error", "msg_id": msg_id, "code": "INVALID_TYPE", "message": "Expected 'command'"}
                
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            err = {"type": "error", "code": "JSON_PARSE_ERROR", "message": "Malformed JSON line"}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

def main():
    global running
    sys.stderr.write("[Mock Hardware] Moce:AI Robot Simulator started.\n")
    t = threading.Thread(target=telemetry_emitter, daemon=True)
    t.start()
    
    try:
        command_receiver()
    except KeyboardInterrupt:
        running = False
        sys.stderr.write("\n[Mock Hardware] Exiting simulator.\n")

if __name__ == "__main__":
    main()
