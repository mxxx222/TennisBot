#!/bin/bash

# Telegram ROI Bot Deployment Script
# ==================================
# This script sets up environment variables and starts the Telegram ROI bot
# with proper configuration for production deployment.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🤖 TELEGRAM ROI BOT DEPLOYMENT"
echo "================================"
echo ""

# Step 1: Check system requirements
print_status "Checking system requirements..."

# Check Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python 3 found: $PYTHON_VERSION"
else
    print_error "Python 3 not found! Please install Python 3.8+"
    exit 1
fi

# Check pip
if command -v pip3 >/dev/null 2>&1 || command -v pip >/dev/null 2>&1; then
    print_success "pip found"
else
    print_error "pip not found! Please install pip"
    exit 1
fi

echo ""

# Step 2: Setup environment variables
print_status "Setting up environment variables..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env file created from .env.example"
    else
        print_error ".env.example file not found!"
        exit 1
    fi
fi

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    print_success "Environment variables loaded from .env"
else
    print_error "Failed to load .env file"
    exit 1
fi

# Check required environment variables
REQUIRED_VARS=("TELEGRAM_BOT_TOKEN")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please set these variables in your .env file:"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token_here"
    exit 1
fi

print_success "All required environment variables are set"

echo ""

# Step 3: Install Python dependencies
print_status "Installing Python dependencies..."

# Install from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    pip3 install --user -r requirements.txt
    print_success "Dependencies installed from requirements.txt"
else
    print_warning "requirements.txt not found. Installing core dependencies..."
    pip3 install --user python-telegram-bot aiohttp beautifulsoup4 selenium pandas numpy scikit-learn requests openai
    print_success "Core dependencies installed"
fi

echo ""

# Step 4: Test bot token
print_status "Testing Telegram bot token..."

python3 -c "
import os
import sys
sys.path.append('src')

try:
    from telegram import Bot
    import asyncio
    
    async def test_token():
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        bot_info = await bot.get_me()
        print(f'✅ Bot connected: @{bot_info.username}')
        return True
    
    asyncio.run(test_token())
except Exception as e:
    print(f'❌ Bot token test failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Bot token test passed"
else
    print_error "Bot token test failed - please check your TELEGRAM_BOT_TOKEN"
    exit 1
fi

echo ""

# Step 5: Create necessary directories
print_status "Creating necessary directories..."

mkdir -p logs data config
print_success "Directories created"

echo ""

# Step 6: Configure continuous monitoring
print_status "Configuring continuous monitoring..."

# Create systemd service file for continuous operation
SERVICE_FILE="/tmp/tennis-roi-bot.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Tennis ROI Telegram Bot - Continuous Monitoring
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
ExecStart=$(which python3) $(pwd)/tennis_roi_telegram.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service file created at $SERVICE_FILE"

# Step 7: Start the bot
print_status "Starting Telegram ROI Bot..."

# Check if bot script exists
if [ ! -f "tennis_roi_telegram.py" ]; then
    print_error "tennis_roi_telegram.py not found!"
    exit 1
fi

# Start the bot in background for continuous monitoring
print_success "Starting bot with continuous monitoring..."
python3 tennis_roi_telegram.py &

BOT_PID=$!
echo "Bot started with PID: $BOT_PID"

# Wait a moment for bot to initialize
sleep 5

# Check if bot is still running
if kill -0 $BOT_PID 2>/dev/null; then
    print_success "Bot is running and monitoring tennis matches continuously"
else
    print_error "Bot failed to start properly"
    exit 1
fi

echo ""
print_success "Telegram ROI Bot deployment completed!"
echo ""
echo "🎯 The bot is now:"
echo "   • Analyzing tennis matches continuously"
echo "   • Sending Telegram notifications for high-ROI opportunities"
echo "   • Monitoring all games in real-time"
echo ""
echo "📱 To interact with the bot:"
echo "   • Start a chat with your bot on Telegram"
echo "   • Use /start to begin receiving notifications"
echo "   • Use /roi to get current best opportunities"
echo ""
echo "🔄 The bot will continue running in the background."
echo "   To stop: kill $BOT_PID"
echo "   To restart: ./deploy_telegram_bot.sh"