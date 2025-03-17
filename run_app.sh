#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Multi-Model Chatbot Application...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed. Please install Node.js and try again.${NC}"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed. Please install npm and try again.${NC}"
    exit 1
fi

# Activate virtual environment or create it if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd backend
pip install "fastapi>=0.110.0" "uvicorn>=0.27.0" "pydantic>=2.0.0" "requests>=2.31.0"

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install backend dependencies.${NC}"
    cd ..
    deactivate
    exit 1
fi

# Return to project root
cd ..

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend

echo -e "${YELLOW}Installing Next.js and React dependencies...${NC}"
npm install --legacy-peer-deps

echo -e "${YELLOW}Installing Tailwind CSS v3...${NC}"
npm install tailwindcss@3 postcss autoprefixer tailwindcss-animate@1.0.7 --legacy-peer-deps

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install frontend dependencies.${NC}"
    cd ..
    deactivate
    exit 1
fi

# Return to project root
cd ..

# Start the backend server in the background
echo -e "${YELLOW}Starting backend server...${NC}"
cd backend
python simple_app.py &
BACKEND_PID=$!
cd ..

# Wait for the backend server to start
echo -e "${YELLOW}Waiting for the backend server to start...${NC}"
sleep 5

# Check if backend server is running
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${RED}Error: Backend server failed to start. Please check the logs and try again.${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    deactivate
    exit 1
fi

echo -e "${GREEN}Backend server is running at http://localhost:8000${NC}"

# Start the frontend server in the background
echo -e "${YELLOW}Starting frontend server...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for the frontend server to start
echo -e "${YELLOW}Waiting for the frontend server to start...${NC}"
sleep 10

echo -e "${GREEN}Frontend server is running at http://localhost:3000${NC}"
echo -e "${GREEN}The Multi-Model Chatbot application is now running!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the application...${NC}"

# Wait for user to press Ctrl+C
trap "echo -e '${YELLOW}Stopping the application...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; deactivate; echo -e '${GREEN}Application stopped.${NC}'; exit 0" INT

# Keep the script running
while true; do
    sleep 1
done
