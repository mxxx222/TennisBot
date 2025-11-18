#!/bin/bash

# Tennis ITF Screener - Cron Job Wrapper
# Runs the daily screening process with proper environment setup

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

# Run the screener
echo "$(date): Starting Tennis ITF Screener..."
python3 tennis_itf_screener.py >> logs/cron_$(date +%Y%m%d).log 2>&1

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date): Screening completed successfully" >> logs/cron_$(date +%Y%m%d).log
else
    echo "$(date): Screening failed with exit code $EXIT_CODE" >> logs/cron_$(date +%Y%m%d).log
fi

# Clean up old log files (keep last 30 days)
find logs/ -name "cron_*.log" -mtime +30 -delete 2>/dev/null

exit $EXIT_CODE
