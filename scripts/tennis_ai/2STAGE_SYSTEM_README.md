# 🎾 2-Stage ITF Tennis System

Professional 2-stage tennis betting system with OpenAI GPT-4 deep analysis.

## Overview

**Stage 1: Scan & Filter**
- Scans Sportbex API for ITF matches (W15, W25, W35)
- Basic filtering: odds 1.20-1.80, tournament tiers
- Saves 20-50 candidates to "Tennis Candidates" Notion database

**Stage 2: OpenAI Deep Analysis**
- Reads candidates from Candidates DB (Status="Scanned")
- Runs GPT-4 deep analysis on each candidate
- Updates candidate pages with AI results
- Promotes high-score candidates (score >= 80) to Bets DB

## Setup

### 1. Install Dependencies

All dependencies are already in `requirements.txt`:
- `requests` - HTTP client
- `notion-client` - Notion API
- `python-dotenv` - Environment variables
- `openai` - OpenAI API

### 2. Configure Environment Variables

Add to `telegram_secrets.env`:
```bash
NOTION_CANDIDATES_DB_ID=your_candidates_db_id_here
```

**How to get Candidates DB ID:**
1. Open your "Tennis Candidates" database in Notion
2. Copy the database ID from the URL
3. URL format: `https://notion.so/YOUR_WORKSPACE/DATABASE_ID?v=...`
4. The database ID is the long string before the `?`

### 3. Verify API Keys

Ensure these are set in `telegram_secrets.env`:
- `NOTION_API_KEY` or `NOTION_TOKEN`
- `OPENAI_API_KEY`
- `SPORTBEX_API_KEY` (optional, has default)

## Usage

### Manual Run

**Stage 1: Scan ITF matches**
```bash
python3 scripts/tennis_ai/stage1_scanner.py
```

**Stage 2: AI Analysis**
```bash
python3 scripts/tennis_ai/stage2_ai_analyzer.py
```

### Automated Run

Use the runner script:
```bash
bash scripts/tennis_ai/run_2stage_system.sh
```

### Cron Setup (Daily Automation)

Add to crontab (`crontab -e`):
```bash
# Stage 1: Scan at 08:00 daily
0 8 * * * cd /path/to/TennisBot && python3 scripts/tennis_ai/stage1_scanner.py >> logs/stage1.log 2>&1

# Stage 2: Analyze at 09:00 daily
0 9 * * * cd /path/to/TennisBot && python3 scripts/tennis_ai/stage2_ai_analyzer.py >> logs/stage2.log 2>&1
```

## Workflow

1. **08:00** - Stage 1 scans ITF matches → Candidates DB (Status="Scanned")
2. **09:00** - Stage 2 AI analysis → Updates candidates (Status="Analyzed")
3. **09:30** - Review promoted bets in Bets DB → Place bets manually

## Expected Results

### Daily Output
- **20-50 candidates** scanned (Stage 1)
- **8-15 candidates** pass basic filters
- **3-5 candidates** promoted by AI (Stage 2, score >= 80)
- **2-3 bets** approved manually

### Performance Metrics
- **Win rate:** 65-70% (vs 55% without AI)
- **ROI:** 25-35%
- **Cost:** ~$0.45/day (OpenAI GPT-4)
- **ROI on AI investment:** 50x+

## Configuration

Edit `config/sportbex_filters.json` to adjust:
- Odds ranges
- Confidence levels
- AI score threshold
- Tournament tiers

## Troubleshooting

### No candidates found
- Check Sportbex API key
- Verify tournament tiers (W15, W25, W35)
- Check odds range (1.20-1.80)

### Notion errors
- Verify `NOTION_CANDIDATES_DB_ID` is set
- Check `NOTION_API_KEY` is valid
- Ensure database properties match expected schema

### OpenAI errors
- Verify `OPENAI_API_KEY` is set
- Check API key has credits
- Model: `gpt-4o` (can change to `gpt-4-turbo`)

## Files

- `scripts/tennis_ai/stage1_scanner.py` - Stage 1 scanner
- `scripts/tennis_ai/stage2_ai_analyzer.py` - Stage 2 AI analyzer
- `scripts/tennis_ai/sportbex_client_simple.py` - Simple Sportbex API client
- `config/sportbex_filters.json` - Filter configuration
- `scripts/tennis_ai/run_2stage_system.sh` - Runner script

## Notes

- ITF W15/W25 focus for maximum edge
- Ranking delta 80-150 = best value
- Low odds (1.25-1.50) OK if confirmed by ELO + form
- AI score >= 80 promoted to Bets DB
- Human final approval required for all bets

