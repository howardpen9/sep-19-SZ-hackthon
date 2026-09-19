#!/usr/bin/env bash
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

PORT="${SERIAL_PORT:-/dev/cu.usbserial-0001}"
BAUD="${SERIAL_BAUD_RATE:-115200}"

echo "=== Firmware Flashing Script ==="
echo "Target port: $PORT @ $BAUD baud"

if command -v pio &> /dev/null; then
    echo "PlatformIO detected. Uploading firmware..."
    pio run -d firmware --target upload --upload-port "$PORT"
elif command -v arduino-cli &> /dev/null; then
    echo "Arduino CLI detected. Compiling and uploading..."
    arduino-cli compile --fqbn esp32:esp32:esp32 firmware/
    arduino-cli upload -p "$PORT" --fqbn esp32:esp32:esp32 firmware/
else
    echo "[!] Neither 'pio' nor 'arduino-cli' found in PATH."
    echo "Please flash manually or install PlatformIO Core / Arduino CLI."
fi
