# 🎾 Real-Time Match Result Tracking & ROI System

## Overview
Complete system for tracking match results, calculating profit/loss, and generating ROI reports for the Tennis AI betting engine.

## Components

### 1. `track_results.py`
**Purpose:** Query Notion for pending matches, check if they're completed, and update results.

**Features:**
- Queries all matches with "Pending" status
- Checks match dates to determine if matches should be completed
- Attempts to fetch results from prematch database
- Updates "Actual Result" field (W/L/PUSH/Pending)
- Calculates Profit/Loss if odds are available
- Updates Notion with results and P/L

**Usage:**
```bash
python3 scripts/tennis_ai/track_results.py
```

**Output:**
- Lists all pending matches
- Shows which matches are still pending vs completed
- Updates Notion database with results
- Calculates P/L for completed matches with odds

### 2. `calculate_roi.py`
**Purpose:** Aggregate all completed matches and generate comprehensive ROI report.

**Features:**
- Fetches all matches with completed results (W/L/PUSH)
- Calculates key metrics:
  - Total bets, wins, losses, pushes
  - Win rate
  - Total stake and P/L
  - ROI percentage
  - Average profit per bet
- Performance breakdown by confidence level
- Recent matches summary
- Saves report to `data/tennis_ai/roi_report.txt`

**Usage:**
```bash
python3 scripts/tennis_ai/calculate_roi.py
```

**Output:**
- Comprehensive ROI report printed to console
- Report saved to file for historical tracking

### 3. `monitor_results.py`
**Purpose:** Automated periodic monitoring of match results.

**Features:**
- Runs `track_results.py` periodically (default: every 30 minutes)
- Can run indefinitely or for a set number of iterations
- Logs all activity
- Can be stopped with Ctrl+C

**Usage:**
```bash
# Run continuously (every 30 min)
python3 scripts/tennis_ai/monitor_results.py

# Or add to cron for automated monitoring
```

**Configuration:**
- `CHECK_INTERVAL`: Minutes between checks (default: 30)
- `MAX_ITERATIONS`: Max number of checks (None = unlimited)

## Profit/Loss Calculation

The P/L calculation uses the following formula:

```python
if result == 'W':
    profit = stake_pct * (actual_odds - 1)
elif result == 'L':
    loss = -stake_pct
elif result == 'PUSH':
    profit = 0
```

**Example:**
- Stake: 2% of bankroll
- Odds: 2.5 (decimal)
- Result: W
- P/L = 2 * (2.5 - 1) = 2 * 1.5 = +3.0

## ROI Calculation

ROI is calculated as:
```
ROI = (Total P/L / Total Stake) * 100
```

**Example:**
- Total Stake: $100
- Total P/L: $15
- ROI = (15 / 100) * 100 = 15%

## Notion Database Properties

The system uses the following Notion properties:

**Required:**
- `Match` (title): Match name
- `AI Recommendation` (select): Player A / Player B / Skip
- `Actual Result` (select): W / L / PUSH / Pending
- `Match Date` (date): When the match is scheduled

**Optional:**
- `Suggested Stake` (number): Stake percentage
- `Actual Odds` (number): Decimal odds used
- `Profit/Loss` (number): Calculated P/L
- `AI Confidence` (number): Confidence level (0-1)
- `Predicted Edge` (number): Expected edge (0-1)
- `Result Updated At` (date): When result was updated

## Workflow

1. **AI Analysis** → Creates predictions in Notion with "Pending" status
2. **Track Results** → Checks for completed matches and updates results
3. **Calculate ROI** → Generates comprehensive ROI report

## Manual Result Entry

If matches need manual result entry:

1. Go to Notion database "Tennis AI — Predictions & Results"
2. Find the match
3. Update "Actual Result" field:
   - `W` if the recommended player won
   - `L` if the recommended player lost
   - `PUSH` if match was cancelled/postponed
4. Add "Actual Odds" if available
5. Run `calculate_roi.py` to update ROI metrics

## Automation

### Cron Job Setup
```bash
# Check results every 30 minutes
*/30 * * * * cd /path/to/TennisBot && source venv/bin/activate && python3 scripts/tennis_ai/track_results.py >> logs/result_tracking.log 2>&1

# Generate ROI report daily at 23:00
0 23 * * * cd /path/to/TennisBot && source venv/bin/activate && python3 scripts/tennis_ai/calculate_roi.py >> logs/roi_report.log 2>&1
```

## Troubleshooting

**No completed matches found:**
- Run `track_results.py` first to update match results
- Check that matches have "Actual Result" set to W/L/PUSH (not Pending)

**P/L not calculated:**
- Ensure "Actual Odds" is set in Notion
- Check that "Suggested Stake" is set (defaults to 2% if missing)

**Matches not updating:**
- Verify Notion API token is set correctly
- Check that database ID is correct
- Ensure integration has edit permissions

## Next Steps

1. **FlashScore Integration:** Enhance `track_results.py` to automatically fetch results from FlashScore
2. **Odds Tracking:** Integrate with odds API to automatically capture actual odds
3. **Alerts:** Add Telegram notifications for completed matches and ROI milestones
4. **Dashboard:** Create web dashboard for real-time ROI visualization

