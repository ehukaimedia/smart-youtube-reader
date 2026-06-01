#!/bin/bash

# Navigate to the directory where this script resides
cd "$(dirname "$0")"

detect_tailscale_ip() {
    if command -v tailscale &> /dev/null; then
        TAILSCALE_CLI_IP="$(tailscale ip -4 2>/dev/null | head -n 1)"
        if [ -n "$TAILSCALE_CLI_IP" ]; then
            echo "$TAILSCALE_CLI_IP"
            return
        fi
    fi

    if command -v ifconfig &> /dev/null; then
        ifconfig 2>/dev/null | awk '/inet 100\\./ { print $2; exit }'
    fi
}

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

# Local-first by default: bind loopback only. Opt in to network/tailnet sharing
# with SYR_SHARE=1, which binds all interfaces (so your tailnet IP is reachable).
BIND_HOST="127.0.0.1"
if [ "${SYR_SHARE:-0}" = "1" ]; then
    BIND_HOST="0.0.0.0"
    echo "--> SYR_SHARE=1: binding to all interfaces (0.0.0.0)."
    echo "    The app will be reachable by other devices on your network/tailnet."
    echo "    Press Ctrl+C now if that is not what you intended."
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
if [ ! -d ".venv" ]; then
    echo "--> No backend virtualenv found. Creating one and installing dependencies (first run only)..."
    if ! python3 -m venv .venv; then
        echo "Error: could not create the Python virtualenv. Install Python 3.11+ and re-run ./start.command"
        read -p "Press Enter to exit..."
        exit 1
    fi
    source .venv/bin/activate
    if ! pip install -r requirements.txt; then
        echo "Error: backend dependency install failed. Fix the error above, then re-run ./start.command"
        deactivate 2>/dev/null
        rm -rf .venv   # don't leave a half-built venv that the next run would treat as ready
        read -p "Press Enter to exit..."
        exit 1
    fi
else
    source .venv/bin/activate
fi

# Verify MLX runtime is available before the first archive request starts the local server.
if ! python -c "import mlx_vlm" &> /dev/null; then
    echo "Note: mlx-vlm is not installed (expected on non-Apple-Silicon systems)."
    echo "      Download, transcript, frames, slicing, and the UI all work; local archive"
    echo "      chaptering requires Apple Silicon. On Apple Silicon, run: pip install -r requirements.txt"
fi

uvicorn app.main:app --reload --host "$BIND_HOST" --port 8001 &
BACKEND_PID=$!

# Start Frontend
echo "--> Starting Frontend (Port 3001)..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "--> Installing frontend dependencies (first run only)..."
    if [ -f "package-lock.json" ]; then
        FRONTEND_INSTALL="npm ci"
    else
        FRONTEND_INSTALL="npm install"
    fi
    if ! $FRONTEND_INSTALL; then
        echo "Error: frontend dependency install failed. Run 'npm install' in ./frontend, then re-run ./start.command"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi
npm run dev -- -H "$BIND_HOST" --port 3001 &
FRONTEND_PID=$!

if [ "$BIND_HOST" = "0.0.0.0" ]; then
    TAILSCALE_IP="$(detect_tailscale_ip)"
    if [ -n "$TAILSCALE_IP" ]; then
        APP_URL="http://${TAILSCALE_IP}:3001/dashboard"
    else
        APP_URL="http://localhost:3001/dashboard"
    fi
else
    APP_URL="http://localhost:3001/dashboard"
fi

echo "============================================"
echo "   App is Running!"
echo "   Open: $APP_URL"
echo "============================================"
echo "   (Close this window to stop the app)"
echo "============================================"

# Auto-launch browser in a private session so app state starts cleanly.
sleep 3
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
