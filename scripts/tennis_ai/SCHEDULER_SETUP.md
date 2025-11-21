# 🕐 Enhanced Scheduler Setup - 08:00 CET Daily Runs

## Overview

Enhanced scheduler runs ITF Entries Intelligence system daily at 08:00 CET (07:00 UTC).

## Schedule

### Daily Jobs (08:00 CET / 07:00 UTC)

1. **07:00 UTC (08:00 CET)** - ITF Entries Intelligence Scraper
   - Scrapes ITF entries data
   - Generates motivation scores
   - Detects withdrawal risks
   - Identifies home advantages
   - Saves to `data/itf_entries/`

2. **07:15 UTC (08:15 CET)** - Enhanced Tennis AI Pipeline
   - Pre-filters W15 matches
   - Runs GPT-4 analysis
   - Enhances with entries intelligence
   - Saves to Notion with intelligence fields
   - Generates bet list

## Time Zone Notes

- **CET (Central European Time)**: UTC+1 (winter) or UTC+2 (summer)
- **Scheduler uses UTC**: 07:00 UTC = 08:00 CET (winter) or 09:00 CET (summer)
- For exact 08:00 CET year-round, adjust UTC time based on DST

## Local Testing

```bash
# Test scheduler locally
python3 scripts/tennis_ai/scheduler_enhanced.py

# Or test individual jobs
python3 scripts/tennis_ai/itf_entries_intelligence_scraper.py
./scripts/tennis_ai/run_tennis_ai_enhanced.sh
```

## Fly.io Deployment

### Update fly.toml

The `fly.toml` is already configured to use `scheduler_enhanced.py`:

```toml
[processes]
  app = "python scripts/tennis_ai/scheduler_enhanced.py"
```

### Deploy

```bash
# Deploy to Fly.io
fly deploy

# Monitor logs
fly logs

# Check status
fly status
```

### Environment Variables

Required secrets (set via `fly secrets set`):

```bash
fly secrets set NOTION_API_KEY="<token>"
fly secrets set NOTION_TENNIS_PREMATCH_DB_ID="<db-id>"
fly secrets set OPENAI_API_KEY="<key>"
fly secrets set ENABLE_ENTRIES_INTELLIGENCE="true"
```

## Verification

After deployment, verify jobs run correctly:

1. Check logs at scheduled time
2. Verify ITF entries data in `data/itf_entries/`
3. Verify enhanced analysis results in `data/tennis_ai/ai_analysis_results.json`
4. Check Notion database for new predictions with intelligence fields

## Troubleshooting

### Jobs not running
- Check Fly.io app is running: `fly status`
- Check logs: `fly logs`
- Verify environment variables: `fly secrets list`

### Time zone issues
- Scheduler uses UTC internally
- Adjust UTC time if exact CET time needed
- Consider using cron expressions for DST handling

### Script errors
- Check script paths in scheduler_enhanced.py
- Verify all dependencies installed
- Check file permissions (scripts must be executable)

