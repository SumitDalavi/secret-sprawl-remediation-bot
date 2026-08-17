#!/bin/bash

echo "================================================="
echo "   Secret Sprawl Remediation Bot Demo"
echo "================================================="

echo "[1] Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "[2] Starting Mock Identity Provider API (background)..."
python mock_api/server.py &
API_PID=$!

# Wait a moment for the server to start
sleep 2

echo ""
echo "[3] Running Remediation Bot against Gitleaks report..."
echo "-------------------------------------------------"
python bot.py data/mock_gitleaks_report.json

echo ""
echo "[4] Cleaning up..."
kill $API_PID
echo "✅ Demo complete."
