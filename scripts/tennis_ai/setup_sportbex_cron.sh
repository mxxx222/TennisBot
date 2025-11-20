#!/bin/bash
# Setup cron job for Sportbex daily candidates
# Runs daily at 08:00 EET

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_PATH=$(which python3)

# Path to the script
SCRIPT_PATH="$SCRIPT_DIR/sportbex_daily_candidates.py"

# Log file
LOG_FILE="$PROJECT_ROOT/logs/sportbex_daily_candidates.log"

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Cron schedule: 08:00 EET = 06:00 UTC (adjust as needed)
# Format: minute hour day month weekday
CRON_SCHEDULE="0 6 * * *"

# Create cron job entry
CRON_ENTRY="$CRON_SCHEDULE cd $PROJECT_ROOT && $PYTHON_PATH $SCRIPT_PATH >> $LOG_FILE 2>&1"

echo "🔧 Setting up Sportbex cron job..."
echo ""
echo "Schedule: Daily at 08:00 EET (06:00 UTC)"
echo "Script: $SCRIPT_PATH"
echo "Log: $LOG_FILE"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "⚠️  Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "📋 Current crontab:"
crontab -l
echo ""
echo "💡 To remove the cron job, run:"
echo "   crontab -e"
echo "   (then delete the line with sportbex_daily_candidates.py)"

