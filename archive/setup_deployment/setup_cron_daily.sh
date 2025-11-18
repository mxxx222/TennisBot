#!/bin/bash
# Setup ITF scraper cron job (2x per day: 08:00 and 20:00 EET = 06:00 and 18:00 UTC)

PROJECT_ROOT="/Users/herbspotturku/sportsbot/TennisBot"
RUNNER_SCRIPT="$PROJECT_ROOT/run_itf_scraper.py"

# Create cron jobs (2x per day at 06:00 and 18:00 UTC = 08:00 and 20:00 EET)
CRON_JOB_1="0 6 * * * cd $PROJECT_ROOT && source venv/bin/activate 2>/dev/null || true && python3 $RUNNER_SCRIPT >> logs/itf_scraper.log 2>&1"
CRON_JOB_2="0 18 * * * cd $PROJECT_ROOT && source venv/bin/activate 2>/dev/null || true && python3 $RUNNER_SCRIPT >> logs/itf_scraper.log 2>&1"

# Get existing crontab
EXISTING_CRON=$(crontab -l 2>/dev/null || echo "")

# Check if cron jobs already exist
if echo "$EXISTING_CRON" | grep -q "$RUNNER_SCRIPT"; then
    echo "⚠️  Cron job already exists for ITF scraper"
    echo "   Removing old entries..."
    # Remove existing entries
    echo "$EXISTING_CRON" | grep -v "$RUNNER_SCRIPT" | crontab -
fi

# Add new cron jobs
(crontab -l 2>/dev/null; echo "$CRON_JOB_1"; echo "$CRON_JOB_2") | crontab -

echo "✅ ITF Scraper cron jobs added:"
echo "   • 06:00 UTC (08:00 EET) - Daily morning scrape"
echo "   • 18:00 UTC (20:00 EET) - Daily evening scrape"
echo ""
echo "📊 View cron jobs: crontab -l"
echo "📋 Monitor logs: tail -f $PROJECT_ROOT/logs/itf_scraper.log"
