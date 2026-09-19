#!/usr/bin/env python3
"""
mock_hardware.py — Virtual Hardware / MCU Simulator
Generates synthetic telemetry and responds to protocol commands without physical hardware.
"""

import sys
import json
import time
import math
import random
import threading

running = True
seq_num = 0
actuator_state = {"servo_pan": 90, "led_status": 0}

def telemetry_emitter():
    global seq_num, running
    start_time = time.time()
    
    while running:
        seq_num += 1
        elapsed = time.time() - start_time
        
        # Synthetic sensor values (sine wave temperature, jittered distance)
        packet = {
            "type": "telemetry",
            "seq": seq_num,
            "timestamp_ms": int(elapsed * 1000),
            "data": {
                "temperature": round(24.0 + 2.5 * math.sin(elapsed / 5.0), 2),
                "distance_cm": round(20.0 + random.uniform(-1.0, 1.0), 1),
                "button_pressed": False,
                "actuators": actuator_state
            }
        }
        sys.stdout.write(json.dumps(packet) + "\n")
        sys.stdout.flush()
        time.sleep(1.0)

def command_receiver():
    global running, actuator_state
    
    for line in sys.stdin:
        if not running:
            break
        line = line.strip()
        if not line:
            continue
        try:
            cmd_packet = json.loads(line)
            cmd_type = cmd_packet.get("type")
            msg_id = cmd_packet.get("msg_id", "unknown")
            
            if cmd_type == "command":
                cmd = cmd_packet.get("cmd")
                params = cmd_packet.get("params", {})
                
                if cmd == "PING":
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": "PONG"}
                elif cmd == "SET_ACTUATOR":
                    target = params.get("actuator", "servo_pan")
                    val = params.get("value", 90)
                    actuator_state[target] = val
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": f"{target} set to {val}"}
                elif cmd == "RESET":
                    actuator_state = {"servo_pan": 90, "led_status": 0}
                    response = {"type": "ack", "msg_id": msg_id, "status": "ok", "message": "State reset"}
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
    sys.stderr.write("[Mock Hardware] Simulator started. Streaming telemetry at 1Hz...\n")
    t = threading.Thread(target=telemetry_emitter, daemon=True)
    t.start()
    
    try:
        command_receiver()
    except KeyboardInterrupt:
        running = False
        sys.stderr.write("\n[Mock Hardware] Exiting simulator.\n")

if __name__ == "__main__":
    main()
