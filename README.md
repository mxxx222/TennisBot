# 🎾 ITF Tennis AI Pipeline

⚠️ **IMPORTANT DISCLAIMER**: This project is intended for **EDUCATIONAL AND RESEARCH PURPOSES ONLY**.

- This system demonstrates AI-powered ITF tennis match analysis and ROI optimization
- Users are responsible for complying with all applicable laws and terms of service
- The authors disclaim any responsibility for misuse or violations
- Use only with explicit permission from website owners
- Implement proper rate limiting and respectful scraping practices

## 🎯 Overview

The **ITF Tennis AI Pipeline** is a specialized system for analyzing ITF (International Tennis Federation) women's tournaments, focusing on W15, W35, and W50 level matches. The system uses a cost-optimized 3-stage pipeline to identify high-value betting opportunities.

### 🎾 Key Features

- **🔍 FlashScore ITF Scraper**: Automated scraping of ITF tournament matches from FlashScore
- **🤖 AI-Powered Analysis**: OpenAI GPT-4 analysis of filtered matches (~€0.03/match)
- **💰 ROI Optimization**: 75% cost savings through intelligent pre-filtering
- **📊 Notion Integration**: Automatic data sync to Notion databases
- **📈 Backtesting System**: Historical match analysis and strategy testing
- **🔔 Telegram Notifications**: Real-time alerts for high-value opportunities
- **📉 Live Monitoring**: Track live matches and detect momentum shifts

## 📋 Requirements

- **Python**: 3.11+
- **Browser**: Chrome/Chromium (for Selenium web scraping)
- **OpenAI API Key**: Required for AI analysis
- **Notion API Token**: Required for database integration
- **Dependencies**: See `requirements.txt`

## ⚡ Quick Start

### 1. **Environment Setup**

```bash
# Clone repository
git clone <repository>
cd TennisBot

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp telegram_secrets.env.example telegram_secrets.env
# Edit telegram_secrets.env and add:
# - OPENAI_API_KEY
# - NOTION_API_KEY
# - NOTION_TENNIS_PREMATCH_DB_ID
```

### 2. **Run ITF Scraper**

```bash
# Run the full ITF pipeline
python run_itf_scraper.py

# Or run individual components
python scripts/tennis_ai/prefilter_w15_matches.py  # Pre-filter matches
python scripts/tennis_ai/ai_analyzer.py            # AI analysis
python scripts/tennis_ai/generate_bet_list.py      # Generate bet list
```

### 3. **Tennis AI Pipeline**

The complete pipeline can be run with:

```bash
source telegram_secrets.env
./scripts/tennis_ai/run_tennis_ai.sh
```

This executes:
1. **Pre-filter**: Filters 100 matches → 20-30 best candidates (free)
2. **AI Analyzer**: GPT-4 analysis of filtered matches (~€0.03/match)
3. **Bet List Generator**: Creates actionable betting recommendations

## 📁 Project Structure

```
TennisBot/
├── scripts/tennis_ai/          # Tennis AI pipeline scripts
│   ├── prefilter_w15_matches.py
│   ├── ai_analyzer.py
│   ├── generate_bet_list.py
│   ├── save_to_notion.py
│   └── run_tennis_ai.sh
├── src/
│   ├── scrapers/
│   │   ├── flashscore_itf_scraper.py      # FlashScore match scraper
│   │   ├── flashscore_itf_enhanced.py     # Enhanced FlashScore scraper
│   │   ├── flashscore_itf_scraper_old.py  # Legacy version
│   │   └── itf_player_scraper.py          # ITFTennis.com player scraper
│   ├── pipelines/
│   │   └── itf_notion_pipeline.py         # Notion integration
│   ├── notion/
│   │   ├── itf_database_updater.py        # Database updater
│   │   └── create_itf_player_profiles.py  # Player profiles
│   ├── analytics/
│   │   ├── itf_backtester.py             # Backtesting
│   │   └── itf_roi_tracker.py             # ROI tracking
│   ├── ml/
│   │   └── itf_match_predictor.py         # ML predictor
│   ├── monitors/
│   │   └── itf_live_monitor.py            # Live monitoring
│   ├── notifiers/
│   │   └── itf_telegram_notifier.py      # Telegram alerts
│   └── trackers/
│       └── itf_odds_tracker.py            # Odds tracking
├── config/
│   └── itf_scraper_config.yaml           # Scraper configuration
├── data/
│   └── tennis_ai/                         # Pipeline data
├── run_itf_scraper.py                     # Main runner
└── check_itf_matches.py                   # Match checker
```

## 🔧 Configuration

### ITF Scraper Config

Edit `config/itf_scraper_config.yaml`:

```yaml
scraper:
  target_tournaments: ['W15', 'W35', 'W50']
  rate_limit: 2.5  # seconds between requests
  use_selenium: true
  headless: true

notion:
  tennis_prematch_db_id: "your_database_id"
  rate_limit: 3  # requests per second
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-proj-...
NOTION_API_KEY=secret_...
NOTION_TENNIS_PREMATCH_DB_ID=...

# Optional
TELEGRAM_BOT_TOKEN=...  # For notifications
DEBUG=true
```

## 📊 Data Flow

```
┌─────────────────┐
│  FlashScore.com │ → ITF Match Scraper → Pre-filter → AI Analyzer → Bet List
└─────────────────┘                                                          ↓
                                                                      Notion Database
┌─────────────────┐                                                          ↓
│ ITFTennis.com   │ → ITF Player Scraper → Player Profiles → ──────────────┘
└─────────────────┘                                                          ↓
                                                                    Telegram Notifications
```

**Two Data Sources:**
1. **FlashScore.com**: Real-time match data, scores, schedules
2. **ITFTennis.com**: Official player statistics, rankings, profiles

## 🎯 Tennis AI Pipeline Details

### Stage 1: Pre-filter (Free)
- Filters matches from Notion database
- Applies basic criteria (tournament tier, player rankings, etc.)
- Output: 20-30 best candidates from 100+ matches

### Stage 2: AI Analyzer (~€0.03/match)
- Uses OpenAI GPT-4 for deep analysis
- Analyzes player form, surface stats, head-to-head
- Generates confidence scores and recommendations
- Output: Detailed analysis for each candidate

### Stage 3: Bet List Generator
- Creates actionable betting recommendations
- Filters by ROI and confidence thresholds
- Output: High-value bet list

**Cost Efficiency**: 75% savings vs analyzing all matches

## 📈 Features

### Scraping (Two Data Sources)

**1. FlashScore.com** - Match Data
- **FlashScore ITF Scraper**: Scrapes W15/W35/W50 tournament matches
- **Enhanced Scraper**: Improved reliability with Selenium for dynamic content
- **Data**: Live scores, match schedules, tournament info, odds

**2. ITFTennis.com** - Player Data  
- **ITF Player Scraper**: Collects player statistics from official ITF website
- **Data**: Rankings, surface statistics, recent form, player profiles
- **Updates**: Weekly player profile updates

### Analysis
- **AI Analysis**: GPT-4 powered match analysis
- **Backtesting**: Historical strategy testing
- **ROI Tracking**: Performance monitoring
- **ML Predictor**: Machine learning model for match predictions

### Monitoring
- **Live Monitor**: Real-time match tracking
- **Odds Tracker**: Line movement detection
- **Telegram Notifier**: Automated alerts

### Notion Integration
- **Tennis Prematch Database**: Match data storage
- **Player Profiles**: Comprehensive player statistics
- **Automated Updates**: Pipeline-driven data sync

## 🚀 Deployment

### Cron Job Setup

```bash
# Setup ITF scraper cron job
./scripts/setup_itf_scraper_cron.sh

# Or manually add to crontab
# Run every 10 minutes
*/10 * * * * cd /path/to/TennisBot && python run_itf_scraper.py
```

### API Deployment

The system includes a Vercel API endpoint for cron-based execution:

```bash
# Deploy to Vercel
vercel deploy

# Set cron schedule in Vercel dashboard
```

## 📊 Expected Results

### Match Analysis
- **Daily Matches**: 20-50 ITF matches per day (depending on tournament schedule)
- **Pre-filtered**: 20-30 candidates after filtering
- **AI Analyzed**: All pre-filtered matches analyzed
- **High-Value Bets**: 0-5 recommendations per day

### Cost Analysis
- **Pre-filter**: Free (uses existing data)
- **AI Analysis**: ~€0.03 per match
- **Daily Cost**: ~€0.60-€0.90 (20-30 matches)
- **Monthly Cost**: ~€18-€27

## 🔍 Troubleshooting

### Common Issues

**No matches found?**
- Check if tournaments are active (ITF tournaments are seasonal)
- Verify scraper configuration
- Check FlashScore website structure hasn't changed

**AI analysis failing?**
- Verify OPENAI_API_KEY is set correctly
- Check OpenAI account has credits
- Review API rate limits

**Notion sync issues?**
- Verify NOTION_API_KEY and database ID
- Check database permissions
- Review rate limiting (max 3 req/s)

**Import errors?**
```bash
# Install missing packages
pip install -r requirements.txt

# Verify Python version
python --version  # Should be 3.11+
```

## 📝 Documentation

- **Tennis AI Pipeline**: [scripts/tennis_ai/README.md](scripts/tennis_ai/README.md)
- **ITF Pipeline Updates**: [ITF_PIPELINE_UPDATE.md](ITF_PIPELINE_UPDATE.md)
- **Pipeline Test Results**: [PIPELINE_TEST_RESULTS.md](PIPELINE_TEST_RESULTS.md)

## ⚖️ Legal & Ethical Guidelines

### 🛡️ Responsible Use
- **Always bet responsibly** and within your limits
- **Never bet more than you can afford to lose**
- **Use predictions as guidance, not guarantees**
- **Past performance doesn't guarantee future results**

### ⚖️ Legal Compliance
1. **Rate Limiting**: Minimum 2.5-second delays between requests
2. **User-Agent**: Clear identification as research bot
3. **Respect robots.txt**: Follow website crawling guidelines
4. **Data Privacy**: Store only aggregated/anonymized data
5. **Terms Compliance**: Verify usage permissions

## 🤝 Contributing

Contributions welcome for:
- Scraper improvements
- AI analysis enhancements
- Backtesting strategies
- Documentation updates
- Bug fixes

## 📝 License

This project is provided for educational purposes. Users are responsible for ensuring compliance with applicable laws and regulations.

## ⚠️ Important Warning

**DO NOT USE FOR ACTUAL BETTING WITHOUT PROPER LICENSING AND LEGAL COMPLIANCE**

This system is designed for learning and research. Any real-money gambling requires proper regulatory approval and licensing.

---

*Built for ITF tennis analysis • AI-powered predictions • ROI-focused optimization*
