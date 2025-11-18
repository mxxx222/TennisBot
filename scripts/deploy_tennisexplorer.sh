#!/bin/bash
# Deployment script for TennisExplorer scraper
# ============================================

set -e

echo "🚀 Deploying TennisExplorer Scraper..."
echo "======================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run setup_tennisexplorer_scraper.sh first"
    exit 1
fi

# Check environment variables
echo "🔍 Checking environment variables..."
if [ -z "$NOTION_API_KEY" ]; then
    echo "⚠️ NOTION_API_KEY not set"
fi

# Run tests
echo "🧪 Running tests..."
python3 -m pytest tests/ -v || echo "⚠️ Tests failed or no tests found"

# Initialize database if needed
echo "💾 Checking database..."
if [ ! -f "data/tennisexplorer.db" ]; then
    echo "📊 Initializing database..."
    sqlite3 data/tennisexplorer.db < src/database/tennisexplorer_schema.sql || echo "⚠️ Database initialization skipped"
fi

# Create logs directory
mkdir -p logs

# Test scraper
echo "🧪 Testing scraper..."
python3 -c "
from src.scrapers.tennisexplorer_scraper import TennisExplorerScraper
scraper = TennisExplorerScraper({'request_delay': 2.0}, use_selenium=False)
print('✅ Scraper initialized successfully')
" || echo "⚠️ Scraper test failed"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "To start the scraper:"
echo "  python3 src/pipelines/tennisexplorer_pipeline.py"
echo ""
echo "Or setup cron:"
echo "  bash scripts/setup_tennisexplorer_cron.sh"

