#!/bin/bash
# Automated Ping-Pong Game Starter (Bash version)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[MASTER] Starting Ping-Pong game..."

# Trap Ctrl+C to clean up
cleanup() {
    echo ""
    echo "[MASTER] Stopping all clients..."
    kill $PONG_PID $PING_PID 2>/dev/null
    wait
    echo "[MASTER] All clients stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start pong client in background
echo "[MASTER] Starting pong client..."
python "$SCRIPT_DIR/pingpong_client.py" pong &
PONG_PID=$!

# Wait a bit for pong to connect
sleep 1

# Start ping client with initial message
echo "[MASTER] Starting ping client (with initial message)..."
python "$SCRIPT_DIR/pingpong_client.py" ping --initial &
PING_PID=$!

echo "[MASTER] Both clients started. Press Ctrl+C to stop."
echo "--------------------------------------------------"

# Wait for both processes
wait


