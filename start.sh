#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
}
trap cleanup EXIT

echo "Starting Smart YouTube Reader..."

# Check requirements
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed."
    exit 1
fi

# Start Backend
echo "Starting Backend on port 8001..."
cd backend
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Warning: No .venv found in backend. running without activation."
fi
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend on port 3001..."
cd ../frontend
npm run dev -- -H 0.0.0.0 --port 3001 &
FRONTEND_PID=$!

echo "App running!"
echo "Backend: http://localhost:8001"
echo "Frontend: http://localhost:3001"
echo "Press Ctrl+C to stop."

wait
