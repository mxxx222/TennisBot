#!/bin/bash
# Cron setup script for TennisExplorer scraper
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python"
PIPELINE_SCRIPT="$PROJECT_DIR/src/pipelines/tennisexplorer_pipeline.py"

echo "⏰ Setting up TennisExplorer Cron Jobs..."
echo "=========================================="

# Check if virtual environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Virtual environment not found. Run setup_tennisexplorer_scraper.sh first"
    exit 1
fi

# Create cron job
CRON_JOB="*/30 * * * * cd $PROJECT_DIR && $PYTHON_PATH $PIPELINE_SCRIPT >> logs/tennisexplorer_cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$PIPELINE_SCRIPT"; then
    echo "⚠️ Cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added (runs every 30 minutes)"
fi

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

echo ""
echo "✅ Cron setup complete!"
echo ""
echo "Current cron jobs:"
crontab -l | grep -i tennisexplorer || echo "No TennisExplorer cron jobs found"

