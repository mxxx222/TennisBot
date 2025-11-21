# 🎾 Tennis Betting System

> Automated ITF Women's tennis betting analytics platform with 15%+ ROI target

## 🚀 Quick Start

### Setup environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure
Edit `.env` with your `NOTION_TOKEN`

### Test monitoring
```bash
python -c "from monitoring.scraper_monitor import ScraperMonitor; print('✅ Monitoring works!')"
```

## 📊 Architecture

```
scrapers/          → Data collection (FlashScore, TennisExplorer, etc.)
monitoring/        → Unified scraper monitoring library
databases/         → Notion schema definitions
analytics/         → ROI calculators, Kelly optimizer
shared/            → Common utilities (validators, config)
deploy/            → Fly.io configuration
tests/             → Unit & integration tests
```

## 🗄️ Databases

- **Tennis Master DB:** Unified match database
- **Players Master DB:** 70+ metrics per player
- **H2H Records:** Head-to-head matchup database
- **Odds Tracking:** Live odds movements & CLV
- **Monitoring:** Scraper health, errors, data quality

## 📚 Documentation

See Notion workspace for:

- Master Cursor Prompt (complete system context)
- Monitoring Implementation Guide
- Git Repository Strategy
- Database Architecture

## 📄 License

Proprietary - All Rights Reserved

