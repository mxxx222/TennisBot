# ✅ Deployment Checklist

## Pre-Deployment

- [ ] All tests passing: `python3 test_tennisexplorer_setup.py`
- [ ] Dependencies installed: `bash scripts/setup_tennisexplorer_scraper.sh`
- [ ] Environment variables configured: `telegram_secrets.env`
- [ ] Database initialized: SQLite or PostgreSQL

## Notion Setup

- [ ] Notion API key obtained: https://www.notion.so/my-integrations
- [ ] Status page created: `bash scripts/create_notion_status_page.sh`
- [ ] Status page shared with integration
- [ ] TennisExplorer Live Feed database created (if using)
- [ ] Database ID added to `telegram_secrets.env`

## Alerting Setup

- [ ] Discord webhook created (optional)
- [ ] Telegram bot created (optional)
- [ ] Webhook URLs/tokens added to `telegram_secrets.env`
- [ ] Test alerts sent successfully

## First Run

- [ ] Test scraper: `python3 src/scrapers/tennisexplorer_scraper.py`
- [ ] Test pipeline: `python3 src/pipelines/tennisexplorer_pipeline.py`
- [ ] Verify data in database
- [ ] Verify Notion page updates
- [ ] Check logs for errors

## Production Deployment

- [ ] Cron job setup: `bash scripts/setup_tennisexplorer_cron.sh`
- [ ] Monitoring alerts configured
- [ ] Weekly report scheduler enabled
- [ ] Log rotation configured
- [ ] Backup strategy in place

## Post-Deployment

- [ ] Monitor first 24 hours closely
- [ ] Verify metrics updating correctly
- [ ] Check alert delivery
- [ ] Review first weekly report
- [ ] Document any issues

## Success Criteria

- ✅ Scraper running without errors
- ✅ 50+ matches scraped per day
- ✅ Enrichment success rate > 80%
- ✅ ROI opportunities detected
- ✅ Alerts sending successfully
- ✅ Status page updating automatically

