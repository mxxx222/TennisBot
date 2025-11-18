# 📊 Create Notion Project Status Page

## Quick Setup

### Option 1: Automatic (Recommended)

```bash
# Run the setup script
bash scripts/create_notion_status_page.sh
```

This will:
1. Create a new Project Status page in Notion
2. Add initial content (checklist, metrics sections)
3. Return the page ID for future reference

### Option 2: Manual

```bash
# Run Python script directly
python3 src/notion/project_status_manager.py
```

## Configuration

### Environment Variables

Add to `telegram_secrets.env`:

```bash
# Required
NOTION_API_KEY=secret_xxx

# Optional: Parent page ID (if you want status page under another page)
NOTION_PROJECT_STATUS_PARENT_ID=your_parent_page_id
```

### Notion API Setup

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it "TennisExplorer Status Manager"
4. Copy the "Internal Integration Token"
5. Add to `telegram_secrets.env` as `NOTION_API_KEY`

### Share Page with Integration

1. After creating the page, click "..." menu
2. Select "Add connections"
3. Add your integration ("TennisExplorer Status Manager")

## What Gets Tracked

The status page automatically tracks:

### ✅ Implementation Checklist
- Core Scraper Module
- Database Schema
- Pipeline Orchestrator
- Enrichment Modules (5)
- ROI Detection (4 modules)
- Notion Integration
- Alerting System
- Scheduler & Monitoring

### 📈 Daily Metrics
- Matches Scraped
- Matches Stored
- H2H Scraped
- Form Scraped
- Odds Scraped
- Enrichment Success Rate
- ROI Opportunities
- Alerts Sent
- Errors
- Uptime

### 🚨 ROI Opportunities
- High-value betting opportunities
- Strategy tags
- Expected Value %
- Kelly Stake recommendations

## Automatic Updates

The pipeline automatically updates the status page:
- **Metrics**: Updated after each scrape cycle
- **ROI Opportunities**: Added when detected
- **Errors**: Logged for troubleshooting

## Manual Updates

You can also manually update the page:

```python
from src.notion.project_status_manager import ProjectStatusManager

manager = ProjectStatusManager()
manager.update_metrics({
    'matches_scraped': 100,
    'roi_opportunities': 5,
    # ... other metrics
})
```

## Troubleshooting

### "Notion client not available"
- Install: `pip install notion-client`

### "NOTION_API_KEY not found"
- Add API key to `telegram_secrets.env`

### "Permission denied"
- Share the page with your integration
- Ensure integration has "Update" permissions

### Page not updating
- Check integration is connected to the page
- Verify API key is correct
- Check logs for errors

## Next Steps

1. ✅ Create status page: `bash scripts/create_notion_status_page.sh`
2. ✅ Share page with integration
3. ✅ Run pipeline: `python3 src/pipelines/tennisexplorer_pipeline.py`
4. ✅ Check status page for updates

The page will automatically update as the scraper runs!

## Ecosystem Linking

### Link to Implementation Documentation

The status page automatically includes a link to:
- **TennisExplorer Scraper — Implementation** (Notion page)
- **🎾 TennisExplorer Live Feed Database** (if `NOTION_TENNISEXPLORER_DB_ID` is set)

### Manual Linking

To link status page to other Notion pages:

1. Open status page in Notion
2. Type `@` and search for page name
3. Or use "Add connections" to link databases

## Monitoring & Alerts

See `MONITORING_ALERTS.md` for:
- Alert threshold configuration
- Discord/Telegram setup
- Weekly report generation
- Testing alerts

## Weekly Reports

Weekly reports are automatically generated every Monday at 8:00 AM.

To generate manually:
```bash
python3 src/notion/weekly_report_generator.py
```

