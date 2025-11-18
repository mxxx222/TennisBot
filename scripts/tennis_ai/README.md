# Tennis AI - ROI-Optimized Analysis System

AI-powered betting tip generator for ITF W15 Women's tennis matches.

📋 **Full Documentation:** [🎯 Tennis AI — ROI-Optimized Scripts](https://www.notion.so/Tennis-AI-ROI-Optimized-Scripts-752c52392d7c4ba997ce3640caa50383?pvs=21)

## Overview

This system uses a 3-stage pipeline to analyze tennis matches cost-effectively:

1. **Pre-filter** (Free) - Filters 100 matches → 20-30 best candidates
2. **AI Analyzer** (~€0.03/match) - OpenAI GPT-4 analysis of filtered matches
3. **Bet List Generator** - Creates actionable betting recommendations

**ROI:** 75% cost savings vs analyzing all matches

## Setup

### 1. Environment Variables

Add to `telegram_secrets.env`:

```bash
# OpenAI API Key (required for AI analysis)
OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE

# Notion (already configured)
NOTION_API_KEY=secret_YOUR_TOKEN
NOTION_TENNIS_PREMATCH_DB_ID=81a70fea5de140d384c77abee225436d
```

Get OpenAI API key: https://platform.openai.com/api-keys

**Important:** Ensure your OpenAI account has credits/billing set up.

### 2. Install Dependencies

```bash
pip install openai notion-client python-dotenv
```

## Usage

### Option 1: Run Full Pipeline (Recommended)

```bash
source telegram_secrets.env
./scripts/tennis_ai/run_tennis_ai.sh
```

This runs:
1. Pre-filter (100 matches → scored)
2. **Optimized batch** (top 25 matches) - **70% cost savings**
3. AI Analysis (~$0.75 for 25 matches)
4. Generate Bet List
5. Save to Notion (if token configured)

### Option 2: Run Individual Scripts

```bash
# Step 1: Pre-filter (FREE)
python3 scripts/tennis_ai/prefilter_w15_matches.py

# Step 1.5: Create optimized batch (RECOMMENDED - saves 70%)
python3 scripts/tennis_ai/create_optimized_batch.py

# Step 2: AI Analysis (COSTS MONEY)
python3 scripts/tennis_ai/ai_analyzer.py  # Auto-uses optimized batch if available

# Step 3: Generate Bet List
python3 scripts/tennis_ai/generate_bet_list.py

# Step 4: Save to Notion (optional)
python3 scripts/tennis_ai/save_to_notion.py
```

## Output Files

All outputs are saved to `data/tennis_ai/`:

- `ai_candidates.json` - Pre-filtered matches with scores
- `ai_analysis_results.json` - Full AI analysis results
- `bet_list.txt` - Human-readable betting recommendations

## Cost Estimation

- Pre-filter: €0 (no API calls)
- Optimized batch creation: €0 (just file processing)
- AI Analysis: ~€0.03 per match (GPT-4)
- **Optimized batch (25 matches): ~$0.75** ⭐ Recommended
- Full batch (100 matches): $3.00
- **Savings with optimized batch: 75%** (saves $2.25 per run)

## Troubleshooting

### OpenAI Quota Error

If you see `insufficient_quota` error:
1. Check OpenAI billing: https://platform.openai.com/account/billing
2. Add payment method or credits
3. Verify API key is correct

### No Matches Found

If pre-filter finds 0 matches:
- Check that W15 matches exist in Notion database
- Verify `NOTION_TENNIS_PREMATCH_DB_ID` is correct
- Check that matches have `Match Status = "Upcoming"`

### Property Name Errors

If you see property not found errors:
- Verify property names match your Notion database schema
- Common properties: `Pelaaja A nimi`, `Pelaaja B nimi`, `Tournament Tier`, `Match Status`, `Kenttä`

## Script Details

### prefilter_w15_matches.py

Pre-filters matches based on:
- Ranking gap (if available)
- Surface data quality
- Essential data completeness
- W15 tournament tier

**Scoring:** 0-100 points, default threshold: 50

### ai_analyzer.py

Uses OpenAI GPT-4 to analyze each match and generate:
- Betting recommendation (Player A, Player B, or Skip)
- Confidence level (High/Medium/Low)
- Expected value percentage
- Reasoning and key factors
- Suggested stake percentage

**Filters:** Only matches with ≥7% EV and Medium+ confidence are included in final recommendations.

### create_optimized_batch.py

Creates cost-optimized batch by selecting top 25 matches:
- Reduces costs by 70% (from $3.00 to $0.75)
- Maintains quality (top-scored matches)
- Automatically used by ai_analyzer.py if available

### generate_bet_list.py

Creates human-readable bet list with:
- Match details
- AI recommendations
- Confidence and stake suggestions
- Reasoning and key factors
- Notion page links

### save_to_notion.py

Saves all AI analyses to Notion database for:
- Historical tracking
- ROI calculation
- Feedback loop calibration
- Performance analysis

**Requires:** `NOTION_API_KEY` or `NOTION_TOKEN` in environment

## Integration

The scripts integrate with:
- Existing Notion database (`NOTION_TENNIS_PREMATCH_DB_ID`) - for match data
- Notion AI Predictions database (`NOTION_AI_PREDICTIONS_DB_ID`) - for saving results
- Project's environment variable system (`telegram_secrets.env`)
- Project's directory structure (`data/tennis_ai/` for outputs)

### Notion Feedback Loop

The system automatically saves all AI analyses to Notion for:
- Historical tracking
- ROI calculation
- Parameter calibration
- Performance analysis

**Setup:** See [🚀 Setup Checklist — Notion Integration](https://www.notion.so/Setup-Checklist-Notion-Integration-29bb397186e945aa87baba6bc15323c0?pvs=21)

## Next Steps

1. Review first batch of AI tips
2. Manually validate 3-5 recommendations
3. Place test bets on high-confidence tips
4. Track outcomes and calibrate prompts
5. Scale to daily automation (cron job)

