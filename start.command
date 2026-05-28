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

# Clear stale processes on required ports
for PORT in 8001 3001; do
    PIDS=$(lsof -Pi :$PORT -sTCP:LISTEN -t 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "--> Clearing stale process(es) on port $PORT (PIDs: $PIDS)..."
        kill $PIDS 2>/dev/null
        sleep 1
    fi
done

# Start Backend
echo "--> Starting Backend (Port 8001)..."
cd backend
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Warning: No .venv found in backend. Using system python."
fi

# Verify MLX runtime is available before the first archive request starts the local server.
if ! python -c "import mlx_vlm" &> /dev/null; then
    echo "Warning: mlx-vlm not found in the backend environment. Run: pip install -r requirements.txt"
    echo "Archive generation will fail until mlx-vlm is installed."
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Start Frontend
echo "--> Starting Frontend (Port 3001)..."
cd ../frontend
npm run dev -- -H 0.0.0.0 --port 3001 &
FRONTEND_PID=$!

echo "============================================"
echo "   App is Running!"
echo "   Open: http://localhost:3001"
echo "============================================"
echo "   (Close this window to stop the app)"
echo "============================================"

# Auto-launch browser in a private session so app state starts cleanly.
sleep 3
APP_URL="http://localhost:3001"
if [ -d "/Applications/Google Chrome.app" ]; then
    open -na "Google Chrome" --args --incognito "$APP_URL"
elif [ -d "/Applications/Chromium.app" ]; then
    open -na "Chromium" --args --incognito "$APP_URL"
elif [ -d "/Applications/Brave Browser.app" ]; then
    open -na "Brave Browser" --args --incognito "$APP_URL"
else
    echo "Warning: Chrome/Chromium/Brave not found. Opening the app in the default browser instead."
    echo "For a private session, open this URL in an incognito/private window: $APP_URL"
    open "$APP_URL"
fi

# Wait for both processes
wait
