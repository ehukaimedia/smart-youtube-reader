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

if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama is not installed. Install it from https://ollama.com/download"
    exit 1
fi

SMART_READER_MODEL="${SMART_READER_MODEL:-gemma4:12b}"
if ! ollama list &> /dev/null; then
    echo "Error: Ollama is not running. Start Ollama, then re-run ./start.sh"
    exit 1
fi
if ! ollama list | awk 'NR > 1 { print $1 }' | grep -Fxq "$SMART_READER_MODEL"; then
    echo "Pulling local model $SMART_READER_MODEL with Ollama..."
    if ! ollama pull "$SMART_READER_MODEL"; then
        echo "Error: could not pull $SMART_READER_MODEL"
        exit 1
    fi
fi
export SMART_READER_MODEL

# Local-first by default: bind loopback only. Opt in to network/tailnet sharing
# with SYR_SHARE=1, which binds all interfaces.
BIND_HOST="127.0.0.1"
if [ "${SYR_SHARE:-0}" = "1" ]; then
    BIND_HOST="0.0.0.0"
    echo "SYR_SHARE=1: binding to all interfaces (0.0.0.0); reachable by other devices on your network."
fi

# Start Backend
echo "Starting Backend on port 8001..."
cd backend
if [ ! -d ".venv" ]; then
    echo "No backend virtualenv found. Creating one and installing dependencies (first run only)..."
    if ! python3 -m venv .venv; then
        echo "Error: could not create the Python virtualenv. Install Python 3.11+ and re-run ./start.sh"
        exit 1
    fi
    source .venv/bin/activate
    if ! pip install -r requirements.txt; then
        echo "Error: backend dependency install failed. Fix the error above, then re-run ./start.sh"
        deactivate 2>/dev/null
        rm -rf .venv   # don't leave a half-built venv that the next run would treat as ready
        exit 1
    fi
else
    source .venv/bin/activate
fi

uvicorn app.main:app --reload --host "$BIND_HOST" --port 8001 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend on port 3001..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (first run only)..."
    if [ -f "package-lock.json" ]; then
        FRONTEND_INSTALL="npm ci"
    else
        FRONTEND_INSTALL="npm install"
    fi
    if ! $FRONTEND_INSTALL; then
        echo "Error: frontend dependency install failed. Run 'npm install' in ./frontend, then re-run ./start.sh"
        exit 1
    fi
fi
npm run dev -- -H "$BIND_HOST" --port 3001 &
FRONTEND_PID=$!

echo "App running!"
echo "Backend: http://localhost:8001"
echo "Frontend: http://localhost:3001"
echo "Press Ctrl+C to stop."

wait
