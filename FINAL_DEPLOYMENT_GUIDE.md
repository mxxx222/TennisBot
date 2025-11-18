# 🚀 Final Deployment Guide

## Pre-Flight Checklist

Run verification:
```bash
bash scripts/verify_deployment.sh
```

This checks:
- ✅ Python environment
- ✅ Dependencies installed
- ✅ Environment variables
- ✅ Database initialized
- ✅ Module imports
- ✅ Scripts executable

## Step-by-Step Deployment

### Step 1: Environment Setup (5 min)

```bash
cd /Users/herbspotturku/sportsbot/TennisBot

# Install dependencies
bash scripts/setup_tennisexplorer_scraper.sh

# Verify
bash scripts/verify_deployment.sh
```

### Step 2: Configure Secrets (5 min)

Edit `telegram_secrets.env`:

```bash
# Required
NOTION_API_KEY=secret_xxx
NOTION_TENNISEXPLORER_DB_ID=your_db_id

# Optional but recommended
OPENWEATHER_API_KEY=your_key
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=xxx:xxx
TELEGRAM_CHAT_ID=your_chat_id
NOTION_PROJECT_STATUS_PAGE_ID=your_status_page_id
```

### Step 3: Create Notion Status Page (2 min)

```bash
bash scripts/create_notion_status_page.sh
```

Then:
1. Open the created page
2. Click "..." → "Add connections"
3. Add your integration
4. Copy page ID to `telegram_secrets.env` as `NOTION_PROJECT_STATUS_PAGE_ID`

### Step 4: First Test Run (5 min)

```bash
# Quick validation
python3 test_tennisexplorer_setup.py

# Test actual scraping (dry run)
python3 src/scrapers/tennisexplorer_scraper.py

# Full pipeline test
python3 src/pipelines/tennisexplorer_pipeline.py
```

**Expected output:**
- ✅ Matches scraped: 50-100
- ✅ Database populated
- ✅ Status page updated
- ✅ No critical errors

### Step 5: Verify Notion Integration (2 min)

1. Open status page in Notion
2. Refresh page
3. Check "Daily Metrics" section updated
4. Verify cross-references work

### Step 6: Setup Alerts (Optional, 10 min)

**Discord:**
1. Server Settings → Integrations → Webhooks
2. New Webhook → Copy URL
3. Add to `telegram_secrets.env`: `DISCORD_WEBHOOK_URL=...`

**Telegram:**
1. Create bot via @BotFather
2. Get chat ID: send message, visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Add to `telegram_secrets.env`

### Step 7: Deploy to Production (5 min)

```bash
# Setup cron job
bash scripts/setup_tennisexplorer_cron.sh

# Verify cron
crontab -l | grep tennisexplorer

# Monitor logs
tail -f logs/tennisexplorer_scraper.log
```

## Monitoring First 24 Hours

### Hour 1
- ✅ Check scraper started
- ✅ Verify matches being scraped
- ✅ Check database populating
- ✅ Verify Notion updates

### Hour 6
- ✅ Check error rates (<5%)
- ✅ Verify enrichment working
- ✅ Check ROI opportunities detected
- ✅ Verify alerts sending (if configured)

### Hour 24
- ✅ Review daily metrics
- ✅ Check uptime (>95%)
- ✅ Analyze error patterns
- ✅ Review first ROI opportunities

## Troubleshooting

### Issue: No matches scraped
```bash
# Check Selenium
python3 -c "from selenium import webdriver; d = webdriver.Chrome(); print('OK')"

# Check TennisExplorer accessible
curl -I https://www.tennisexplorer.com/live-tennis/

# Review logs
tail -50 logs/tennisexplorer_scraper.log
```

### Issue: Notion page not updating
```bash
# Verify API key
python3 -c "import os; from dotenv import load_dotenv; load_dotenv('telegram_secrets.env'); print('API Key:', os.getenv('NOTION_API_KEY')[:10] + '...')"

# Test Notion connection
python3 -c "from src.notion.project_status_manager import ProjectStatusManager; m = ProjectStatusManager(); print('Status:', 'OK' if m.client else 'FAILED')"
```

### Issue: Alerts not sending
```bash
# Test Discord
curl -X POST "$DISCORD_WEBHOOK_URL" -H "Content-Type: application/json" -d '{"content":"Test"}'

# Test Telegram
python3 -c "from telegram import Bot; import asyncio; bot = Bot('$TELEGRAM_BOT_TOKEN'); asyncio.run(bot.send_message(chat_id='$TELEGRAM_CHAT_ID', text='Test'))"
```

## Success Indicators

After 24 hours, you should see:

- ✅ **Matches**: 50-100 scraped
- ✅ **Database**: Populated with match data
- ✅ **Status Page**: Metrics updating
- ✅ **ROI Opportunities**: 5-10 detected
- ✅ **Uptime**: >95%
- ✅ **Error Rate**: <5%

## Next Steps After Deployment

1. **Week 1**: Monitor closely, adjust thresholds
2. **Week 2**: Review first weekly report
3. **Week 3**: Add Tennis Abstract ELO (Sprint 3)
4. **Week 4**: Optimize based on data

## Support

- Documentation: See `QUICK_START.md`, `MONITORING_ALERTS.md`
- Status Page: Auto-updates with metrics
- Logs: `logs/tennisexplorer_scraper.log`

---

**Ready to deploy?** Run:
```bash
bash scripts/verify_deployment.sh && bash scripts/setup_tennisexplorer_scraper.sh
```

Good luck! 🚀

