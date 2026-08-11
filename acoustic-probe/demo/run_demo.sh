#!/usr/bin/env bash
# run_demo.sh — Starts the FV Eileen Acoustic Probe Demo
#
# This launches:
#   1. A Python HTTP server for the visual dashboard
#   2. The telemetry simulator (5-minute fishing trip)
#   3. The musical output converter (telemetry → music parameters)
#
# Usage:
#   ./run_demo.sh              # Full demo, 5-minute trip
#   ./run_demo.sh --speed 2    # 2x speed (2.5 minute trip)
#   ./run_demo.sh --duration 600  # 10-minute trip
#
# Then open http://localhost:8777 in a browser.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=8777
PYTHON="${PYTHON:-python3}"

echo "═══════════════════════════════════════════════════════"
echo "  FV EILEEN — ACOUSTIC PROBE DEMO"
echo "  The ship becomes a musical instrument."
echo "═══════════════════════════════════════════════════════"
echo ""

# Pass through arguments to simulator
SIM_ARGS=("$@")

# ─── Start HTTP Server ────────────────────────────────────────
echo "▶  Starting dashboard server on port $PORT..."
$PYTHON -m http.server $PORT \
    --bind 127.0.0.1 \
    > /dev/null 2>&1 &
HTTP_PID=$!
echo "  Dashboard: http://localhost:$PORT/demo.html"
echo "  PID: $HTTP_PID"

# Cleanup on exit
cleanup() {
    echo ""
    echo "■  Stopping demo..."
    kill $HTTP_PID 2>/dev/null || true
    # Kill any simulator or musical_output processes we started
    for pid in ${SIM_PID:-} ${MUSIC_PID:-}; do
        kill $pid 2>/dev/null || true
    done
    echo "■  Demo stopped."
}
trap cleanup EXIT INT TERM

# ─── Start Musical Output Converter ───────────────────────────
echo "▶  Starting musical output converter..."
$PYTHON musical_output.py --interval 3 &
MUSIC_PID=$!
echo "  PID: $MUSIC_PID"

sleep 1

# ─── Start Simulator ──────────────────────────────────────────
echo "▶  Starting telemetry simulator..."
echo "  Args: ${SIM_ARGS[*]:-(default 5-minute trip)}"
echo ""
echo "────────────────────────────────────────────────────────"
echo "  Open your browser: http://localhost:$PORT/demo.html"
echo "  The dashboard updates automatically every 2 seconds."
echo "  Press Ctrl+C to stop."
echo "────────────────────────────────────────────────────────"
echo ""

$PYTHON simulator.py "${SIM_ARGS[@]}" &
SIM_PID=$!

# Wait for simulator to finish
wait $SIM_PID 2>/dev/null || true
SIM_PID=""

echo ""
echo "✓  Trip complete! Dashboard remains available."
echo "  Press Ctrl+C to exit."

# Keep the dashboard alive after the trip ends
wait $HTTP_PID 2>/dev/null || true
