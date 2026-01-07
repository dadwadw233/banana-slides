#!/bin/bash

# Banana Slides - Development Server Startup Script
# This script starts both frontend and backend development servers
# Press Ctrl+C to stop both servers gracefully

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_PATH="$PROJECT_ROOT/.venv"

# PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"

    # Kill backend process
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${BLUE}   Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill -TERM $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
    fi

    # Kill frontend process
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${BLUE}   Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill -TERM $FRONTEND_PID 2>/dev/null || true
        wait $FRONTEND_PID 2>/dev/null || true
    fi

    # Kill any remaining processes on ports 5000 and 3000
    echo -e "${BLUE}   Cleaning up ports...${NC}"
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true

    echo -e "${GREEN}✅ Servers stopped successfully${NC}"
    exit 0
}

# Register cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}   Please create it first: python3 -m venv .venv${NC}"
    exit 1
fi

# Print banner
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║        🍌  Banana Slides Development Server  🍌             ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Clean up any existing processes on ports
echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend
echo -e "${BLUE}🚀 Starting backend server...${NC}"
cd "$BACKEND_DIR"

# Activate virtual environment and start backend in background
(
    source "$VENV_PATH/bin/activate"
    python app.py
) &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}   → http://localhost:5000${NC}"

# Start frontend
echo -e "${BLUE}🚀 Starting frontend server...${NC}"
cd "$FRONTEND_DIR"

npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 2

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Frontend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo -e "${BLUE}   → http://localhost:3000${NC}"

# Success message
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Development servers are running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "\n${YELLOW}📝 Services:${NC}"
echo -e "   ${BLUE}Frontend:${NC}  http://localhost:3000"
echo -e "   ${BLUE}Backend:${NC}   http://localhost:5000"
echo -e "   ${BLUE}API:${NC}       http://localhost:5000/api"
echo -e "\n${YELLOW}💡 Tips:${NC}"
echo -e "   • Press ${RED}Ctrl+C${NC} to stop both servers"
echo -e "   • Backend logs: backend/logs/"
echo -e "   • Frontend hot-reload is enabled"
echo -e "\n${YELLOW}🔍 Monitoring processes...${NC}"
echo -e "   Backend PID: $BACKEND_PID"
echo -e "   Frontend PID: $FRONTEND_PID"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}\n"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
