#!/bin/bash

# Navigate to the directory where this script resides
cd "$(dirname "$0")"

# Function to kill background processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
}
trap cleanup EXIT

echo "============================================"
echo "   Starting Smart YouTube Reader..."
echo "============================================"

# Check requirements
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install it (e.g., brew install ffmpeg)."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if ports are in use
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "Error: Port 8001 is already in use. Please stop the existing backend process."
    read -p "Press Enter to exit..."
    exit 1
fi

if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null ; then
    echo "Error: Port 3001 is already in use. Please stop the existing frontend process."
    read -p "Press Enter to exit..."
    exit 1
fi

# Start Backend
echo "--> Starting Backend (Port 8001)..."
cd backend
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Warning: No .venv found in backend. Using system python."
fi
uvicorn app.main:app --reload --port 8001 &
BACKEND_PID=$!

# Start Frontend
echo "--> Starting Frontend (Port 3001)..."
cd ../frontend
npm run dev -- --port 3001 &
FRONTEND_PID=$!

echo "============================================"
echo "   App is Running!"
echo "   Open: http://localhost:3001"
echo "============================================"
echo "   (Close this window to stop the app)"
echo "============================================"

# Auto-launch browser
sleep 3
open "http://localhost:3001"

# Wait for both processes
wait
