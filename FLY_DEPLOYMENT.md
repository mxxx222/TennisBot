# Fly.io ITF Tennis Pipeline Deployment Guide

## Overview

This guide explains how to deploy the ITF tennis pipeline to Fly.io. The deployment uses a single long-running app with an internal scheduler that manages three cron jobs.

## Architecture

- **Single Fly.io app**: `itf-tennis-pipeline`
- **Long-running process**: Enhanced scheduler script runs continuously
- **Two scheduled jobs (Enhanced Pipeline with ITF Entries Intelligence)**:
  1. ITF Entries Intelligence Scraper: 07:00 UTC (08:00 CET) - Daily
  2. Enhanced Tennis AI Pipeline: 07:15 UTC (08:15 CET) - Daily (after intelligence update)
  
**Note**: Enhanced pipeline includes:
- ITF entries intelligence scraping
- Pre-filtering matches
- GPT-4 analysis with entries intelligence enhancement
- Notion integration with intelligence fields

## Prerequisites

- Fly.io account (existing account can be used)
- Fly.io CLI installed (`curl -L https://fly.io/install.sh | sh`)
- GitHub repository with code pushed

## Setup Steps

### 1. Install Fly.io CLI

```bash
curl -L https://fly.io/install.sh | sh
```

### 2. Authenticate

```bash
fly auth login
```

### 3. Initialize App (if not already exists)

```bash
fly launch --name itf-tennis-pipeline --dockerfile Dockerfile
```

Or if app already exists:

```bash
fly apps create itf-tennis-pipeline
```

### 4. Set Environment Variables (Secrets)

All secrets must be set via `fly secrets set`:

```bash
# Required environment variables
fly secrets set NOTION_TOKEN="<your-notion-token>"
# OR
fly secrets set NOTION_API_KEY="<your-notion-token>"

fly secrets set NOTION_TENNIS_PREMATCH_DB_ID="<your-database-id>"
# OR
fly secrets set NOTION_PREMATCH_DB_ID="<your-database-id>"

fly secrets set OPENAI_API_KEY="<your-openai-key>"

# Optional environment variables
fly secrets set ODDS_API_KEY="<your-odds-api-key>"  # For odds fetching
fly secrets set NOTION_ITF_PLAYER_CARDS_DB_ID="<your-db-id>"  # For player card linking
fly secrets set NOTION_ROI_SCRAPING_TARGETS_DB_ID="<your-db-id>"  # For scraper relations
```

**Note**: Scripts accept multiple variable names:
- `NOTION_TOKEN` or `NOTION_API_KEY` (both work)
- `NOTION_TENNIS_PREMATCH_DB_ID` or `NOTION_PREMATCH_DB_ID` (both work)

### 5. Deploy

```bash
fly deploy
```

### 6. Monitor

```bash
# View logs
fly logs

# Check status
fly status

# Open dashboard
fly dashboard
```

## Configuration Files

### fly.toml

Main Fly.io configuration file. Key settings:

- **App name**: `itf-tennis-pipeline` (changeable)
- **Primary region**: `iad` (US East - change to your preference)
- **Memory**: 512 MB (adjustable via `fly scale memory`)
- **CPU**: 1 shared CPU
- **Mount**: `itf_data` volume mounted at `/app/data`

### scripts/tennis_ai/scheduler.py

Main scheduler script that:
- Runs continuously in a loop
- Checks every minute for scheduled tasks
- Executes jobs in subprocesses with proper error handling
- Logs all activity to stdout (visible via `fly logs`)

### Dockerfile

Updated to run `scripts/tennis_ai/scheduler.py` as the default command.

## Known Issues & Solutions

### Missing `config/screening_config.py`

**Issue**: The file `config/screening_config.py` is referenced by:
- `utils/odds_fetcher.py`
- `utils/bet_calculator.py`
- `utils/notifiers.py`

**Impact**: This will cause import errors if odds fetching is attempted without this file.

**Solution**: 
1. **Option A (Recommended for production)**: Create the missing config file:
   ```python
   # config/screening_config.py
   import os
   
   class ScreeningConfig:
       ODDS_API_KEY = os.getenv('ODDS_API_KEY', '')
       ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
       SPORT = "tennis"
       REGIONS = "us,uk,au"
       MARKETS = "h2h"
       ODDS_FORMAT = "decimal"
       DATE_FORMAT = "iso"
       REQUEST_DELAY = 1.0
       MAX_RETRIES = 3
       RETRY_DELAY = 5.0
       
       # Tournament filtering
       ALLOWED_TOURNAMENTS = ["ITF", "W15", "W25", "W35", "W50", "W75", "W100"]
       EXCLUDED_TOURNAMENTS = ["ATP", "WTA", "Grand Slam"]
   ```

2. **Option B (Current workaround)**: Odds fetching is optional and gracefully skips if not configured. The ITF scraper will work without odds.

**Note**: This doesn't block deployment - the main pipeline works without odds fetching.

### Selenium Chrome Dependencies

**Status**: ✅ Already handled in Dockerfile

Chrome and ChromeDriver are installed in the Dockerfile, so Selenium-based scraping will work out of the box.

### Timezone Handling

The scheduler uses UTC internally. All scheduled times are in UTC:
- ITF Scraper: 06:00 & 18:00 UTC
- Player Card Linker: 06:30 UTC
- GPT Analyzer: 07:00 & 19:00 UTC

Ensure Fly.io machine time is correctly set (defaults to UTC).

### Long-Running Process

Fly.io machines run continuously. The scheduler script loops forever, checking every minute for scheduled tasks. This is the expected behavior.

If the machine stops, Fly.io will automatically restart it.

## Monitoring & Troubleshooting

### View Logs

```bash
fly logs
```

Logs include:
- Scheduler startup messages
- Job execution start/end times
- Success/failure status for each job
- Error messages with stack traces

### Check Machine Status

```bash
fly status
```

### View Metrics

```bash
fly dashboard
```

### Manual Testing

To test jobs manually without waiting for schedule:

1. SSH into machine:
   ```bash
   fly ssh console
   ```

2. Run jobs directly:
   ```bash
   python run_itf_scraper.py
   python scripts/tennis_ai/link_existing_matches.py
   python scripts/tennis_ai/analyze_filtered_matches.py
   ```

### Common Issues

**Issue**: Job fails with "ModuleNotFoundError"
- **Solution**: Ensure all dependencies are in `requirements.txt` and Dockerfile installs them

**Issue**: Job fails with "NOTION_TOKEN not set"
- **Solution**: Set secrets via `fly secrets set NOTION_TOKEN=<value>`

**Issue**: Selenium fails to start
- **Solution**: Check Chrome/ChromeDriver installation in Dockerfile (already configured)

**Issue**: Job times out
- **Solution**: Jobs have 1-hour timeout. If job takes longer, increase timeout in `scheduler.py` or optimize the script

## Deployment Flow

1. **06:00 UTC** → ITF Scraper runs, scrapes ~100 matches, saves to Notion
2. **06:30 UTC** → Player Card Linker runs, links 80-90% of matches to player cards
3. **07:00 UTC** → GPT Analyzer runs, analyzes 5-10 matches marked as "KIINNOSTAVA"

Same sequence repeats at 18:00 UTC (scraper) and 19:00 UTC (analyzer), but linker only runs once daily at 06:30.

## Scaling

To adjust resources:

```bash
# Increase memory
fly scale memory 1024

# Increase CPU
fly scale vm shared-cpu-2x

# View current resources
fly status
```

## Cost Estimation

Fly.io pricing (as of 2024):
- **Free tier**: 3 shared-cpu-1x VMs with 256MB RAM (lifetime)
- **Paid**: ~$1.94/month per shared-cpu-1x 512MB VM

For this deployment:
- **Single VM**: ~$2/month (or free if within free tier limits)
- **Storage**: Volume storage costs apply (~$0.15/GB/month)

**Total estimated cost**: ~$2-5/month depending on usage and storage.

## Support

For issues:
1. Check logs: `fly logs`
2. Check status: `fly status`
3. Review this documentation
4. Check Fly.io status: https://status.fly.io/

