#!/usr/bin/env bash
set -e

# Load environment if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "=== Starting Development Environment ==="
echo "SIMULATE_HARDWARE: ${SIMULATE_HARDWARE:-true}"
echo "SERIAL_PORT: ${SERIAL_PORT:-/dev/cu.usbserial-0001}"

python3 -m software.server
