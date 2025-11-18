#!/bin/bash
# ITF Scraper Cron Setup Script
# Deploys scraper to run every 10 minutes
# Supports Render free tier, Heroku, or local cron

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 ITF Scraper Cron Setup"
echo "========================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Check for required files
if [ ! -f "$PROJECT_ROOT/src/pipelines/itf_notion_pipeline.py" ]; then
    echo "❌ ITF pipeline not found"
    exit 1
fi

# Create main runner script
RUNNER_SCRIPT="$PROJECT_ROOT/run_itf_scraper.py"
cat > "$RUNNER_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
ITF Scraper Runner
Runs the ITF Notion pipeline
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipelines.itf_notion_pipeline import ITFNotionPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """Run ITF pipeline"""
    config = {
        'scraper': {
            'target_tournaments': ['W15', 'W35', 'W50'],
            'rate_limit': 2.5,
        },
        'notion': {
            'tennis_prematch_db_id': None,  # Will load from env
        }
    }
    
    pipeline = ITFNotionPipeline(config)
    result = await pipeline.run_pipeline()
    
    if result.get('success'):
        print(f"✅ Pipeline completed: {result['matches_created']} matches created")
        sys.exit(0)
    else:
        print(f"❌ Pipeline failed: {result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x "$RUNNER_SCRIPT"
echo "✅ Created runner script: $RUNNER_SCRIPT"

# Setup based on deployment type
echo ""
echo "Select deployment type:"
echo "1) Local cron"
echo "2) Render (free tier)"
echo "3) Heroku"
read -p "Choice [1-3]: " choice

case $choice in
    1)
        # Local cron setup - runs 2x per day at 08:00 and 20:00 EET (06:00 and 18:00 UTC)
        CRON_JOB1="0 6 * * * cd $PROJECT_ROOT && source venv/bin/activate 2>/dev/null || true && python3 $RUNNER_SCRIPT >> logs/itf_scraper.log 2>&1"
        CRON_JOB2="0 18 * * * cd $PROJECT_ROOT && source venv/bin/activate 2>/dev/null || true && python3 $RUNNER_SCRIPT >> logs/itf_scraper.log 2>&1"
        
        # Check if cron job already exists
        if crontab -l 2>/dev/null | grep -q "$RUNNER_SCRIPT"; then
            echo "⚠️ Cron job already exists, removing old entries..."
            crontab -l 2>/dev/null | grep -v "$RUNNER_SCRIPT" | crontab -
        fi
        
        # Add new cron jobs
        (crontab -l 2>/dev/null; echo "$CRON_JOB1"; echo "$CRON_JOB2") | crontab -
        echo "✅ Added cron jobs (runs at 08:00 and 20:00 EET / 06:00 and 18:00 UTC)"
        
        # Create logs directory
        mkdir -p "$PROJECT_ROOT/logs"
        echo "✅ Created logs directory"
        ;;
    2)
        # Render setup
        echo ""
        echo "📋 Render Setup Instructions:"
        echo "1. Create new Web Service on Render"
        echo "2. Connect your GitHub repository"
        echo "3. Set build command: pip install -r requirements.txt"
        echo "4. Set start command: python3 run_itf_scraper.py"
        echo "5. Add environment variables:"
        echo "   - NOTION_API_KEY"
        echo "   - NOTION_TENNIS_PREMATCH_DB_ID"
        echo "   - TELEGRAM_BOT_TOKEN (optional)"
        echo "   - TELEGRAM_CHAT_ID (optional)"
        echo "6. Set schedule: Cron (0,10,20,30,40,50 * * * *)"
        echo ""
        echo "✅ Render configuration ready"
        ;;
    3)
        # Heroku setup
        echo ""
        echo "📋 Heroku Setup Instructions:"
        echo "1. Create Heroku app: heroku create your-app-name"
        echo "2. Add scheduler addon: heroku addons:create scheduler:standard"
        echo "3. Set config vars:"
        echo "   heroku config:set NOTION_API_KEY=your_key"
        echo "   heroku config:set NOTION_TENNIS_PREMATCH_DB_ID=your_db_id"
        echo "4. Add to scheduler: python3 run_itf_scraper.py (every 10 minutes)"
        echo ""
        echo "✅ Heroku configuration ready"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Setup complete!"
echo ""
echo "💡 Next steps:"
echo "1. Configure environment variables (NOTION_API_KEY, etc.)"
echo "2. Test runner: python3 $RUNNER_SCRIPT"
echo "3. Monitor logs: tail -f logs/itf_scraper.log"

