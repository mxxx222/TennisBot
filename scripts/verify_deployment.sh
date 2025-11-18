#!/bin/bash
# Deployment Verification Script
# ===============================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "🔍 TennisExplorer Deployment Verification"
echo "========================================"
echo ""

# Check 1: Python environment
echo "1️⃣ Checking Python environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   ✅ Virtual environment found"
else
    echo "   ⚠️  Virtual environment not found - run setup script first"
    exit 1
fi

# Check 2: Dependencies
echo ""
echo "2️⃣ Checking dependencies..."
python3 -c "import notion_client; print('   ✅ notion-client')" 2>/dev/null || echo "   ❌ notion-client missing"
python3 -c "import selenium; print('   ✅ selenium')" 2>/dev/null || echo "   ❌ selenium missing"
python3 -c "from bs4 import BeautifulSoup; print('   ✅ beautifulsoup4')" 2>/dev/null || echo "   ❌ beautifulsoup4 missing"

# Check 3: Environment variables
echo ""
echo "3️⃣ Checking environment variables..."
if [ -f "telegram_secrets.env" ]; then
    source telegram_secrets.env
    [ -n "$NOTION_API_KEY" ] && echo "   ✅ NOTION_API_KEY set" || echo "   ⚠️  NOTION_API_KEY not set"
    [ -n "$NOTION_TENNISEXPLORER_DB_ID" ] && echo "   ✅ NOTION_TENNISEXPLORER_DB_ID set" || echo "   ⚠️  NOTION_TENNISEXPLORER_DB_ID not set"
else
    echo "   ⚠️  telegram_secrets.env not found"
fi

# Check 4: Database
echo ""
echo "4️⃣ Checking database..."
if [ -f "data/tennisexplorer.db" ]; then
    echo "   ✅ SQLite database exists"
    COUNT=$(sqlite3 data/tennisexplorer.db "SELECT COUNT(*) FROM tennisexplorer_matches;" 2>/dev/null || echo "0")
    echo "   📊 Matches in database: $COUNT"
else
    echo "   ⚠️  Database not initialized - will be created on first run"
fi

# Check 5: Module imports
echo ""
echo "5️⃣ Testing module imports..."
python3 test_tennisexplorer_setup.py 2>&1 | grep -E "(PASS|FAIL)" | head -3

# Check 6: Scripts
echo ""
echo "6️⃣ Checking deployment scripts..."
[ -x "scripts/setup_tennisexplorer_scraper.sh" ] && echo "   ✅ Setup script executable" || echo "   ⚠️  Setup script not executable"
[ -x "scripts/create_notion_status_page.sh" ] && echo "   ✅ Status page script executable" || echo "   ⚠️  Status page script not executable"

# Check 7: Logs directory
echo ""
echo "7️⃣ Checking directories..."
[ -d "logs" ] && echo "   ✅ logs/ directory exists" || (mkdir -p logs && echo "   ✅ Created logs/ directory")
[ -d "data" ] && echo "   ✅ data/ directory exists" || (mkdir -p data && echo "   ✅ Created data/ directory")

echo ""
echo "========================================"
echo "✅ Verification complete!"
echo ""
echo "Next steps:"
echo "1. Configure API keys in telegram_secrets.env"
echo "2. Create status page: bash scripts/create_notion_status_page.sh"
echo "3. Test pipeline: python3 src/pipelines/tennisexplorer_pipeline.py"
echo "4. Deploy cron: bash scripts/setup_tennisexplorer_cron.sh"

