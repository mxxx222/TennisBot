# Sprint 1 Setup Guide
====================

Human-in-the-loop tennis candidate screening system using Sportbex API.

## Overview

**Workflow:**
- **08:00 (Automatic):** Python script fetches matches from Sportbex API, filters by odds 1.40-1.80, pushes 5-20 candidates to Notion with Status="Review"
- **08:30 (Human + AI):** Review candidates in Notion, use AI prompt to analyze top picks
- **09:00 (Human):** Select 2-3 best picks, change Status to "Approved", place bets manually

## Prerequisites

- Python 3.8+
- Notion account with master database
- Sportbex API key (trial: 500 requests free)

## Step 1: Sportbex API Setup (15 min)

### 1.1 Get API Key

1. Go to: https://trial.sportbex.com
2. Sign up with email
3. Get trial API key (500 requests free)
4. Save API key: `Fbmm5Xt57NzVjdKdGwPIQY7EXKOmYAt2MfFWXVCb`

### 1.2 Test API (cURL)

```bash
curl -X GET "https://api.sportbex.com/v1/matches?sport=tennis&days=2" \
  -H "Authorization: Bearer Fbmm5Xt57NzVjdKdGwPIQY7EXKOmYAt2MfFWXVCb" \
  -H "Content-Type: application/json"
```

**Expected:** JSON response with tennis matches

**Note:** API structure may vary. The client handles multiple endpoint patterns.

### 1.3 Set Environment Variable

Add to `telegram_secrets.env`:

```bash
SPORTBEX_API_KEY=Fbmm5Xt57NzVjdKdGwPIQY7EXKOmYAt2MfFWXVCb
```

## Step 2: Notion Setup (10 min)

### 2.1 Get Notion API Key

1. Go to: https://www.notion.so/my-integrations
2. Create new integration
3. Copy API key
4. Add to `telegram_secrets.env`:

```bash
NOTION_API_KEY=secret_xxx
```

### 2.2 Get Master Database ID

1. Open your master database in Notion
2. Copy database ID from URL:
   - URL format: `https://www.notion.so/09a1af5850eb4cd39bff88e79ce69865`
   - Database ID: `09a1af5850eb4cd39bff88e79ce69865`
3. Add to `telegram_secrets.env`:

```bash
NOTION_MASTER_DB_ID=09a1af5850eb4cd39bff88e79ce69865
```

### 2.3 Share Database with Integration

1. Open database in Notion
2. Click "..." menu → "Connections"
3. Add your integration
4. Grant access

### 2.4 Verify Database Schema

Ensure your master database has these fields:
- **Date & Time** (Date)
- **Tournament** (Text)
- **Player 1** (Text)
- **Player 2** (Text)
- **Selected Player** (Select: Player 1 / Player 2)
- **Odds** (Number)
- **Stake** (Number, optional)
- **Bet Type** (Select: SINGLE)
- **Result** (Select: Pending / Win / Loss)
- **Tournament Level** (Select: ITF W15 / W25 / W35 / ATP Challenger)
- **Bookmaker** (Select)
- **Status** (Select: Review / Approved / Pending / Won / Lost) - **IMPORTANT**
- **Notes** (Text, for AI analysis)
- **Player 1 Ranking** (Number, optional)
- **Player 2 Ranking** (Number, optional)
- **Surface** (Select: Hard / Clay / Grass, optional)

**Note:** If Status field doesn't exist, create it manually in Notion with options: Review, Approved, Pending, Won, Lost

## Step 3: Install Dependencies (5 min)

```bash
cd /path/to/TennisBot
pip install -r requirements.txt
```

**Required packages:**
- `aiohttp` - Async HTTP client
- `notion-client` - Notion API
- `schedule` - Python scheduler (already in requirements.txt)
- `python-dotenv` - Environment variables

## Step 4: Test Pipeline (10 min)

### 4.1 Manual Test

```bash
cd scripts/tennis_ai
python sportbex_daily_candidates.py --test
```

**Expected output:**
```
🚀 Starting Sportbex Daily Candidates Pipeline...
📥 Step 1: Fetching matches from Sportbex API...
✅ Fetched X matches from Sportbex API
🔍 Step 2: Filtering matches...
✅ Filtered to Y candidates
📤 Step 3: Logging candidates to Notion...
✅ Logged Z candidates, W duplicates, E errors
```

### 4.2 Verify in Notion

1. Open master database
2. Check for new entries with Status="Review"
3. Verify data is correct

## Step 5: Setup Scheduler (10 min)

### Option A: Python Scheduler (Recommended for Development)

```bash
cd scripts/tennis_ai
python sportbex_scheduler.py
```

**Note:** This runs continuously. For production, use cron (Option B).

### Option B: Cron Job (Recommended for Production)

```bash
cd scripts/tennis_ai
./setup_sportbex_cron.sh
```

**Verify cron job:**
```bash
crontab -l
```

**Expected:**
```
0 6 * * * cd /path/to/TennisBot && /usr/bin/python3 scripts/tennis_ai/sportbex_daily_candidates.py >> logs/sportbex_daily_candidates.log 2>&1
```

**Note:** Adjust timezone in script if needed (08:00 EET = 06:00 UTC)

## Step 6: Daily Workflow (Human-in-the-Loop)

### 6.1 Morning (08:00) - Automatic

Pipeline runs automatically:
- Fetches matches from Sportbex API
- Filters by odds 1.40-1.80, tournaments (ITF W15/W25/W35, ATP Challenger)
- Pushes 5-20 candidates to Notion with Status="Review"

### 6.2 Morning (08:30) - Human + AI Review

1. **Open Notion database**
   - Filter by Status = "Review"
   - See new candidates

2. **Use AI Analysis Prompt**
   - Open `ai_analysis_prompt.md`
   - Copy list of Review candidates
   - Paste into ChatGPT/Claude with prompt template
   - Get AI analysis of top 3 picks

3. **Review AI suggestions**
   - Check reasoning
   - Look for red flags
   - Verify ELO/ranking data if available

### 6.3 Morning (09:00) - Human Selection

1. **Select 2-3 best picks**
   - Based on AI analysis + your judgment
   - Change Status to "Approved" in Notion

2. **Place bets**
   - Go to betfury.io
   - Place bets on approved picks
   - Update Status to "Pending" when bet placed

3. **Update after match**
   - Change Status to "Won" or "Lost"
   - Update Stake and Profit/Loss if needed

## Troubleshooting

### Issue: No matches found from Sportbex API

**Possible causes:**
- API key invalid
- API endpoint changed
- No matches available

**Solutions:**
1. Test API with cURL (Step 1.2)
2. Check API key in `telegram_secrets.env`
3. Check logs: `logs/sportbex_daily_candidates.log`
4. API structure may vary - check `src/scrapers/sportbex_client.py` for endpoint patterns

### Issue: Notion pages not created

**Possible causes:**
- Notion API key invalid
- Database ID incorrect
- Database not shared with integration
- Missing required fields

**Solutions:**
1. Verify API key: `NOTION_API_KEY` in `telegram_secrets.env`
2. Verify database ID: `NOTION_MASTER_DB_ID` in `telegram_secrets.env`
3. Check database sharing (Step 2.3)
4. Verify database schema (Step 2.4)
5. Check logs for specific errors

### Issue: Status field not working

**Possible causes:**
- Status field doesn't exist in database
- Status field options don't match

**Solutions:**
1. Create Status field manually in Notion
2. Add options: Review, Approved, Pending, Won, Lost
3. Re-run pipeline

### Issue: Too few/many candidates

**Adjust filters:**
- Edit `config/sportbex_config.yaml`:
  - `candidates.min_candidates`: Minimum (default: 5)
  - `candidates.max_candidates`: Maximum (default: 20)
  - `filters.min_odds`: Minimum odds (default: 1.40)
  - `filters.max_odds`: Maximum odds (default: 1.80)

### Issue: Cron job not running

**Check:**
1. Verify cron job exists: `crontab -l`
2. Check cron logs: `grep CRON /var/log/syslog` (Linux) or check system logs
3. Verify script path is correct
4. Check script permissions: `chmod +x sportbex_daily_candidates.py`
5. Test script manually first

## Configuration

Edit `config/sportbex_config.yaml` to customize:

- **API settings:** API key, rate limits
- **Filters:** Odds range, tournaments, ranking delta
- **Candidates:** Min/max count
- **Scheduler:** Run time, timezone

## Files Created

- `src/scrapers/sportbex_client.py` - Sportbex API client
- `src/pipelines/sportbex_filter.py` - Match filtering logic
- `src/notion/sportbex_notion_logger.py` - Notion integration
- `scripts/tennis_ai/sportbex_daily_candidates.py` - Main pipeline
- `scripts/tennis_ai/sportbex_scheduler.py` - Python scheduler
- `scripts/tennis_ai/setup_sportbex_cron.sh` - Cron setup script
- `scripts/tennis_ai/ai_analysis_prompt.md` - AI prompt template
- `config/sportbex_config.yaml` - Configuration

## Next Steps (Sprint 2)

- Add ELO data enrichment
- Improve ranking delta filtering with ELO
- Add more sophisticated filters
- Automated result tracking

## Support

For issues:
1. Check logs: `logs/sportbex_daily_candidates.log`
2. Test components individually:
   - API: `python src/scrapers/sportbex_client.py`
   - Filter: `python src/pipelines/sportbex_filter.py`
   - Notion: `python src/notion/sportbex_notion_logger.py`
3. Check environment variables in `telegram_secrets.env`

---

**Setup time:** 4-6 hours  
**Daily time:** 30 minutes (human review)  
**Expected output:** 5-20 candidates daily, 2-3 approved picks

