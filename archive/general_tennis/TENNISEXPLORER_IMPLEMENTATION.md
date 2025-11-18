# TennisExplorer Scraper Implementation

## Overview

Complete implementation of TennisExplorer scraper that complements the existing FlashScore scraper. The system scrapes data from TennisExplorer, enriches it with ELO ratings, weather data, and statistics, detects ROI opportunities, and integrates with Notion.

## Files Created

### Core Scraper
- `src/scrapers/tennisexplorer_scraper.py` - Main scraper for TennisExplorer endpoints

### Database
- `src/database/tennisexplorer_schema.sql` - PostgreSQL/SQLite schema

### Pipeline
- `src/pipelines/tennisexplorer_pipeline.py` - Main pipeline orchestrator

### Enrichment Modules
- `src/enrichment/elo_enricher.py` - ELO ratings (Tennis Abstract API or calculation)
- `src/enrichment/stats_enricher.py` - Service/return statistics
- `src/enrichment/weather_enricher.py` - Weather data (OpenWeatherMap API)
- `src/enrichment/tiebreak_enricher.py` - Tiebreak and deciding set stats
- `src/enrichment/recovery_enricher.py` - Travel and recovery calculator

### ROI Detection
- `src/roi_detection/momentum_detector.py` - Momentum shift detection
- `src/roi_detection/fatigue_detector.py` - Fatigue risk detection
- `src/roi_detection/h2h_detector.py` - H2H exploit detection
- `src/roi_detection/kelly_calculator.py` - Kelly criterion calculator

### Integration
- `src/notion/tennisexplorer_notion_updater.py` - Notion database integration
- `src/alerts/roi_alert_manager.py` - Discord/Telegram alerting
- `src/schedulers/tennisexplorer_scheduler.py` - Job scheduler
- `src/monitoring/tennisexplorer_monitor.py` - Monitoring and metrics

### Configuration & Deployment
- `config/tennisexplorer_config.yaml` - Configuration file
- `scripts/setup_tennisexplorer_scraper.sh` - Setup script
- `scripts/setup_tennisexplorer_cron.sh` - Cron setup
- `scripts/deploy_tennisexplorer.sh` - Deployment script

## Quick Start

1. **Setup environment:**
   ```bash
   bash scripts/setup_tennisexplorer_scraper.sh
   ```

2. **Configure API keys:**
   Edit `telegram_secrets.env` and add:
   - `NOTION_API_KEY`
   - `NOTION_TENNISEXPLORER_DB_ID`
   - `OPENWEATHER_API_KEY` (optional)
   - `DISCORD_WEBHOOK_URL` (optional)
   - `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (optional)

3. **Run pipeline:**
   ```bash
   python3 src/pipelines/tennisexplorer_pipeline.py
   ```

4. **Setup cron (optional):**
   ```bash
   bash scripts/setup_tennisexplorer_cron.sh
   ```

## Features Implemented

### Sprint 1: Core Scraper
- ✅ Live matches scraping
- ✅ H2H data (overall + surface-specific)
- ✅ Recent form (last 5, last 10)
- ✅ Odds comparison (20+ bookmakers)
- ✅ Tournament history
- ✅ PostgreSQL/SQLite database schema

### Sprint 2: Data Enrichment
- ✅ ELO ratings (API or calculation)
- ✅ Service/return stats (aces, DFs, hold%, break%)
- ✅ Weather data (temp, wind, humidity)
- ✅ Tiebreak and deciding set stats
- ✅ Travel/recovery calculator

### Sprint 3: ROI Detection
- ✅ Momentum shift detector
- ✅ Fatigue risk detector
- ✅ H2H exploit detector
- ✅ Kelly criterion calculator
- ✅ Notion database integration
- ✅ Alerting system (Discord + Telegram)

### Sprint 4: Automation
- ✅ Job scheduler (APScheduler)
- ✅ Monitoring and metrics
- ✅ Deployment scripts
- ✅ Configuration management

## Data Flow

```
TennisExplorer.com → Scraper → PostgreSQL/SQLite → Enrichment Pipeline → Notion API → TennisExplorer Live Feed DB
                                                                    ↓
                                                          ROI Detection → Discord/Telegram Alerts
```

## Next Steps

1. **Test the scraper:**
   - Run `python3 src/scrapers/tennisexplorer_scraper.py` to test basic scraping
   - Run `python3 src/pipelines/tennisexplorer_pipeline.py` to test full pipeline

2. **Create Notion database:**
   - Create a new Notion database called "TennisExplorer Live Feed"
   - Add all properties as defined in `tennisexplorer_notion_updater.py`
   - Copy database ID to `telegram_secrets.env`

3. **Configure APIs:**
   - Get OpenWeatherMap API key (free tier: 1000 calls/day)
   - Optional: Get Tennis Abstract API key for ELO ratings

4. **Deploy:**
   - Run deployment script: `bash scripts/deploy_tennisexplorer.sh`
   - Setup cron for automated runs: `bash scripts/setup_tennisexplorer_cron.sh`

## Notes

- The scraper uses Selenium for dynamic content (similar to FlashScore scraper)
- Database defaults to SQLite for MVP (can switch to PostgreSQL)
- All enrichment modules have fallback mechanisms if APIs are unavailable
- ROI detection runs every 30 seconds for live matches
- Alerts are sent for opportunities with EV > 15%

## Dependencies Added

- `playwright==1.40.0` - Alternative to Selenium
- `apscheduler==3.10.4` - Job scheduling
- `geopy==2.4.1` - Geocoding for weather

All other dependencies were already in `requirements.txt`.

