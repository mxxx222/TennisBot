# Football OU2.5 AI - ROI-Optimized Analysis System

Football Over/Under 2.5 goals betting agent cloned from proven Tennis AI architecture.

## 🎯 Overview

This system uses the same validated methodology as the Tennis AI agent:
- **Pre-filtering** to reduce API costs
- **AI analysis** with GPT-4
- **70% impliedP threshold** (validated 100% win rate in tennis)
- **Notion integration** for tracking
- **ROI optimization** through quality filtering

## 📋 Architecture

```
scripts/football_ai/
├── prefilter_ou25_matches.py    # Pre-filter matches (FREE)
├── ai_analyzer.py                # GPT-4 analysis (~€0.03/match)
├── generate_bet_list.py          # Generate bet list
├── save_to_notion.py            # Save to Notion (with 70% filter)
├── validate_predictions.py       # Validate results
└── run_football_ai.sh           # Full pipeline script
```

## 🚀 Quick Start

### 1. Setup Environment Variables

Add to `telegram_secrets.env`:
```bash
OPENAI_API_KEY=your_key_here
NOTION_API_KEY=your_notion_key
NOTION_FOOTBALL_PREMATCH_DB_ID=your_prematch_db_id
NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID=your_predictions_db_id
```

### 2. Run Full Pipeline

```bash
./scripts/football_ai/run_football_ai.sh
```

Or run steps individually:
```bash
# Step 1: Pre-filter (FREE)
python3 scripts/football_ai/prefilter_ou25_matches.py

# Step 2: AI Analysis (Costs money)
python3 scripts/football_ai/ai_analyzer.py

# Step 3: Generate bet list
python3 scripts/football_ai/generate_bet_list.py

# Step 4: Save to Notion (optional)
python3 scripts/football_ai/save_to_notion.py
```

## 🎯 70% ImpliedP Threshold

**Validated from Tennis Agent:**
- 100% win rate (12/12) for 70%+ impliedP bets
- ROI: +39.3% with filter vs +5.8% without
- Filter automatically applied in `save_to_notion.py`

## 📊 Expected Performance

Based on Tennis validation:
- **Win Rate:** 75-100% (depending on impliedP threshold)
- **ROI:** +30-40% with 70% filter
- **Bets per week:** 12-15 (quality over quantity)

## 📁 Output Files

- `data/football_ai/ai_candidates.json` - Pre-filtered matches
- `data/football_ai/ai_analysis_results.json` - AI recommendations
- `data/football_ai/bet_list.txt` - Ready-to-bet list
- `data/football_ai/validation_summary.json` - Validation results

## 🔧 Configuration

### Pre-filter Scoring

Matches are scored (0-100) based on:
- **Goal averages** (30p) - Key for OU2.5
- **Defensive stats** (25p) - Weak defenses = more goals
- **League quality** (20p) - Top leagues preferred
- **Form data** (15p) - Recent performance
- **Data quality** (10p) - Complete information

Minimum score: 50 points

### AI Analyzer

- **Model:** GPT-4 (can use GPT-3.5-turbo for cheaper)
- **Temperature:** 0.3 (conservative)
- **70% impliedP threshold** enforced
- **Output:** OVER/UNDER/Skip recommendations

## 📝 Notion Database Schema

Required fields:
- `Match` (title) - Match name
- `League` (text) - League name
- `AI Recommendation` (select) - OVER/UNDER/Skip
- `AI Confidence` (number) - 0-1
- `Predicted Edge` (number) - Expected value
- `Actual Result` (select) - OVER/UNDER/Pending
- `ImpliedP` (number) - Implied probability %

## 🔄 Validation

Run validation after matches complete:
```bash
python3 scripts/football_ai/validate_predictions.py
```

Tracks:
- Overall accuracy
- Accuracy by impliedP range
- 70%+ performance highlight
- ROI calculations

## 💡 Tips

1. **Start conservative:** Monitor first 10-15 bets before scaling
2. **Use 70% filter:** Automatically applied, but verify it's working
3. **Track results:** Update Notion with actual results for validation
4. **Compare with Tennis:** Both systems use same methodology

## 🆚 Differences from Tennis Agent

- **Bet type:** OVER/UNDER 2.5 goals (vs Home/Away)
- **Data focus:** Goal averages, defensive stats (vs rankings, surface)
- **League filtering:** Top 5 leagues preferred
- **Same core:** 70% threshold, AI analysis, validation system

## 📚 Related

- Tennis AI: `scripts/tennis_ai/`
- Validation methodology: Same as tennis (proven 100% win rate on 70%+)

