#!/bin/bash

# Soccer Screener - Cron Job Wrapper
# Runs the daily soccer screening process

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set up environment
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export TZ="Europe/Helsinki"

# Load virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "$(date): Activated virtual environment"
fi

# Load environment variables
if [ -f "telegram_secrets.env" ]; then
    set -a  # automatically export all variables
    source telegram_secrets.env
    set +a
    echo "$(date): Loaded environment variables"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the soccer screener
echo "$(date): Starting Soccer Screener..."
python3 soccer_screener.py >> logs/soccer_cron_$(date +%Y%m%d).log 2>&1

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date): Soccer screening completed successfully" >> logs/soccer_cron_$(date +%Y%m%d).log
else
    echo "$(date): Soccer screening failed with exit code $EXIT_CODE" >> logs/soccer_cron_$(date +%Y%m%d).log
fi

# Clean up old log files (keep last 30 days)
find logs/ -name "soccer_cron_*.log" -mtime +30 -delete 2>/dev/null

exit $EXIT_CODE
