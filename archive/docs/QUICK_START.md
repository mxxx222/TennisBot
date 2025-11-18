# 🚀 Quick Start Guide

## 1. Setup (5 minutes)

```bash
# Install dependencies
bash scripts/setup_tennisexplorer_scraper.sh

# Configure API keys
nano telegram_secrets.env
# Add: NOTION_API_KEY, NOTION_TENNISEXPLORER_DB_ID, etc.
```

## 2. Create Notion Status Page (2 minutes)

```bash
bash scripts/create_notion_status_page.sh
```

Then:
1. Open the created page in Notion
2. Click "..." → "Add connections"
3. Add your integration

## 3. Test Scraper (1 minute)

```bash
# Quick validation
python3 test_tennisexplorer_setup.py

# Test actual scraping
python3 src/scrapers/tennisexplorer_scraper.py
```

## 4. Run Pipeline (2 minutes)

```bash
python3 src/pipelines/tennisexplorer_pipeline.py
```

Check:
- ✅ Database populated: `sqlite3 data/tennisexplorer.db "SELECT COUNT(*) FROM tennisexplorer_matches;"`
- ✅ Notion page updated (refresh page)
- ✅ Logs: `tail -f logs/tennisexplorer_scraper.log`

## 5. Setup Alerts (Optional, 5 minutes)

### Discord
1. Server Settings → Integrations → Webhooks → New Webhook
2. Copy URL to `telegram_secrets.env`: `DISCORD_WEBHOOK_URL=...`

### Telegram
1. Create bot via @BotFather
2. Get chat ID: send message, visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Add to `telegram_secrets.env`: `TELEGRAM_BOT_TOKEN=...` and `TELEGRAM_CHAT_ID=...`

## 6. Deploy to Production (5 minutes)

```bash
# Setup cron job
bash scripts/setup_tennisexplorer_cron.sh

# Verify cron
crontab -l | grep tennisexplorer
```

## Expected Results

After first run:
- ✅ 50-100 matches in database
- ✅ Status page showing metrics
- ✅ ROI opportunities detected (if any)
- ✅ Alerts sent (if configured)

## Troubleshooting

**No matches scraped?**
- Check TennisExplorer website is accessible
- Verify Selenium is working: `python3 -c "from selenium import webdriver; print('OK')"`
- Check logs: `tail -20 logs/tennisexplorer_scraper.log`

**Notion page not updating?**
- Verify API key is correct
- Check page is shared with integration
- Review logs for Notion API errors

**Alerts not sending?**
- Verify webhook URLs/tokens are correct
- Test manually: `python3 -c "from src.alerts.roi_alert_manager import ROIAlertManager; import asyncio; m = ROIAlertManager(); asyncio.run(m.send_alert({'match_id': 'test', 'expected_value_pct': 20, ...}))"`

## Next Steps

- Review `DEPLOYMENT_CHECKLIST.md` for full deployment guide
- See `MONITORING_ALERTS.md` for alert configuration
- Check `CREATE_NOTION_STATUS.md` for status page details
