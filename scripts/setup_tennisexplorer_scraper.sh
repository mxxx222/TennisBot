#!/bin/bash
# Setup script for TennisExplorer scraper
# ========================================

set -e

echo "🚀 Setting up TennisExplorer Scraper..."
echo "========================================"

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies if needed
echo "📥 Installing additional dependencies..."
pip install playwright geopy apscheduler || echo "⚠️ Some optional dependencies failed to install"

# Install Playwright browsers
if command -v playwright &> /dev/null; then
    echo "🌐 Installing Playwright browsers..."
    playwright install chromium
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Create .env file if it doesn't exist
if [ ! -f "telegram_secrets.env" ]; then
    echo "📝 Creating telegram_secrets.env template..."
    cat > telegram_secrets.env << EOF
# Notion API
NOTION_API_KEY=your_notion_api_key_here
NOTION_TENNISEXPLORER_DB_ID=your_database_id_here

# Discord Webhook (optional)
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# API Keys (optional)
TENNIS_ABSTRACT_API_KEY=your_tennis_abstract_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
EOF
    echo "⚠️ Please edit telegram_secrets.env and add your API keys"
fi

# Initialize database (SQLite)
echo "💾 Initializing database..."
if [ -f "src/database/tennisexplorer_schema.sql" ]; then
    sqlite3 data/tennisexplorer.db < src/database/tennisexplorer_schema.sql || echo "⚠️ Database initialization skipped (may already exist)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit telegram_secrets.env and add your API keys"
echo "2. Run: python3 src/pipelines/tennisexplorer_pipeline.py"
echo "3. Or setup cron: bash scripts/setup_tennisexplorer_cron.sh"

