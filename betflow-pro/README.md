# BetFlow Pro - High ROI Betting System

**Target: 25-40% ROI through advanced edge detection, arbitrage, and ML predictions**

## Overview

BetFlow Pro is a comprehensive betting intelligence system that combines:
- **Multi-method edge detection** (base, arbitrage, line movement, ML)
- **Advanced Kelly Criterion** with variance adjustment
- **Multi-bookmaker optimization** for best odds
- **Real-time Notion dashboards** with automated formulas
- **Automated alerts** for opportunities
- **Backtesting engine** for strategy validation

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         DASHBOARD (Notion) — Frontend               │
│    Real-time ROI, Alerts, Betting Pipeline          │
├─────────────────────────────────────────────────────┤
│      ANALYSIS ENGINE (Python) — Backend             │
│    Edge detection, Kelly, Arbitrage, ML models      │
├─────────────────────────────────────────────────────┤
│      DATA PIPELINE (Bookmaker APIs) — ETL          │
│    Real-time odds, Placement, Settlement          │
├─────────────────────────────────────────────────────┤
│      DATABASE (Notion) — Storage                    │
│    All matches, bets, results, metrics              │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Installation

```bash
cd betflow-pro
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your:
- Notion API token
- Bookmaker API keys (Pinnacle, Bet365)
- Bankroll and risk settings
- Email for alerts

### 3. Create Notion Databases

```bash
python create_notion_databases.py --page-id YOUR_PAGE_ID --token YOUR_NOTION_TOKEN
```

This creates three databases:
- **Master Control Panel** - Real-time ROI metrics
- **Advanced Analytiikka** - Edge detection and analysis
- **Real-Time Arbitrage** - Arbitrage opportunities

### 4. Run the System

```bash
python main.py
```

## Components

### Edge Detection (`edge_detection.py`)

Multi-method edge detection:

- **Base Edge**: Traditional probability vs market probability
- **Arbitrage Edge**: Cross-bookmaker opportunities
- **Line Movement Edge**: Odds movement in your favor
- **ML Edge**: Machine learning probability predictions

**Composite Edge Formula:**
```
TOTAL_EDGE% = (Base_Edge * 0.60) + 
              (Arbitrage_Edge * 0.20) + 
              (Movement_Edge * 0.10) + 
              (ML_Edge * 0.10)
```

### Kelly Criterion (`kelly_criterion.py`)

Advanced Kelly Criterion with:
- **Scaled Kelly** (default: 50% for safety)
- **Variance adjustment** (reduces stake for high variance)
- **Drawdown protection** (reduces stake during drawdowns)
- **Streak adjustment** (increases after wins, decreases after losses)

### Bookmaker Optimizer (`bookmaker_optimizer.py`)

- Compares odds across multiple bookmakers
- Detects arbitrage opportunities
- Calculates optimal stake distribution
- Supports Pinnacle, Bet365, and mock APIs

### Notion Integration

#### Master Control Panel

Real-time metrics dashboard:
- YTD ROI %
- Bankroll tracking
- Win rate
- Sharpe ratio
- Alerts

#### Advanced Analytiikka

Analysis database with formulas:
- **Total Edge %**: `Base Edge * 0.6 + Arbitrage Edge * 0.2 + Movement Edge * 0.1 + ML Edge * 0.1`
- **Kelly %**: Conditional formula based on edge
- **Stake (€)**: `Bankroll * Kelly % / 100`
- **Potential Win (€)**: `Stake * (Odds - 1)`

#### Real-Time Arbitrage

Arbitrage tracking:
- **Arbitrage %**: `(1 / Odds_A + 1 / Odds_B - 1) * 100`
- **Expected Profit**: `Min Stake * Arbitrage % / 100`

## Usage Examples

### Analyze a Single Match

```python
from main import BetFlowProEngine

engine = BetFlowProEngine()

match = {
    'id': 'match123',
    'home_team': 'Team A',
    'away_team': 'Team B',
    'my_probability': 0.55,
    'market_probability': 0.50,
    'opening_odds': 2.0,
    'current_odds': 2.05,
    'hours_to_match': 24,
    'bet_type': '1X2',
    'xg_diff': 0.5,
    'form_diff': 0.2,
    'h2h_win_pct': 60,
    'data_points': 15
}

analysis = engine.analyze_match(match)
print(f"Total Edge: {analysis['total_edge']}%")
print(f"Stake: €{analysis['stake']}")
print(f"Recommendation: {analysis['recommendation']}")
```

### Detect Arbitrage Opportunities

```python
from bookmaker_optimizer import BookmakerOptimizer

optimizer = BookmakerOptimizer()

matches = [
    {'id': 'match1', 'home_team': 'Team A', 'away_team': 'Team B'},
    {'id': 'match2', 'home_team': 'Team C', 'away_team': 'Team D'}
]

arbs = optimizer.detect_arbitrage(matches)

for arb in arbs:
    print(f"{arb['match_name']}: {arb['arbitrage_percent']:.2f}% profit")
```

### Backtest a Strategy

```python
from backtester import Backtester
import pandas as pd

# Load historical data
historical_data = pd.read_csv('historical_matches.csv')

backtester = Backtester(historical_data)

strategy = {
    'name': 'High Edge Strategy',
    'criteria': {
        'min_edge': 4.0,
        'min_confidence': 6,
        'max_odds': 3.0,
        'max_stake_percent': 3.0
    }
}

results = backtester.backtest_strategy(
    strategy=strategy,
    start_date='2024-01-01',
    end_date='2024-12-31'
)

print(f"Total ROI: {results['total_roi_percent']}%")
print(f"Win Rate: {results['win_rate']}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']}")
```

### Sync to Notion

```python
from notion_sync import NotionSync

notion = NotionSync()

analysis_data = {
    'match_id': 'match123',
    'match_name': 'Team A vs Team B',
    'base_edge': 8.5,
    'arb_edge': 2.1,
    'movement_edge': 1.5,
    'ml_edge': 0.8,
    'total_edge': 12.1,
    'confidence': 8,
    'best_book': 'Pinnacle',
    'best_odds': 1.95,
    'recommendation': 'PLAY'
}

notion.update_analysis('match123', analysis_data)
```

## API Integration

### Pinnacle API

1. Sign up at [Pinnacle](https://www.pinnacle.com/en/api)
2. Get your API key
3. Add to `.env`:
   ```
   PINNACLE_API_KEY=your_key
   PINNACLE_USERNAME=your_username
   PINNACLE_PASSWORD=your_password
   ```

### Bet365 API

1. Contact Bet365 for API access
2. Add to `.env`:
   ```
   BET365_API_KEY=your_key
   ```

### Mock Mode (Development)

Set in `.env`:
```
USE_MOCK_APIS=true
```

This uses mock odds generators for testing without real API access.

## Scheduled Tasks

The system runs scheduled tasks automatically:

- **06:00** - Daily analysis routine
- **14:00** - Line movement check
- **20:00** - Results update
- **Every 30 minutes** - Arbitrage check

## Configuration

### Bankroll Settings

```env
BANKROLL=5000                    # Starting bankroll (€)
MIN_EDGE_PERCENT=4.0             # Minimum edge to bet (%)
KELLY_SCALE=0.5                  # Kelly scaling factor (0.5 = half Kelly)
MAX_STAKE_PERCENT=3.0            # Maximum stake per bet (%)
MAX_DRAWDOWN_TOLERANCE=15.0      # Max drawdown before reducing stakes (%)
```

### Alert Settings

```env
ALERT_EMAIL=your_email@example.com
GMAIL_USER=your_gmail@gmail.com
GMAIL_PASS=your_app_password
```

## Notion Formulas Reference

### Total Edge %
```
prop("Base Edge %") * 0.6 + 
prop("Arbitrage Edge %") * 0.2 + 
prop("Movement Edge %") * 0.1 + 
prop("ML Edge %") * 0.1
```

### Kelly %
```
if(prop("Total Edge %") > 8,
  (prop("Total Edge %") * (prop("Best Odds") - 1)) / (prop("Best Odds") - 1) * 0.75,
  if(prop("Total Edge %") > 4,
    (prop("Total Edge %") * (prop("Best Odds") - 1)) / (prop("Best Odds") - 1) * 0.5,
    0
  )
)
```

### Stake (€)
```
if(prop("Total Edge %") > 4,
  5000 * prop("Kelly %") / 100,
  0
)
```

### Arbitrage %
```
(1 / prop("Odds A") + 1 / prop("Odds B") - 1) * 100
```

## Troubleshooting

### Notion API Errors

- Verify your token is correct
- Check that databases are created
- Ensure integration has access to the page

### Bookmaker API Errors

- Check API keys are valid
- Verify rate limits aren't exceeded
- Use mock mode for testing

### ML Model Not Training

- Ensure historical data has required columns:
  - `xg_diff`, `form_diff`, `h2h_win_pct`
  - `home_advantage`, `recent_goals_diff`
  - `injury_count_diff`, `result`

## Performance Metrics

The system tracks:
- **ROI %**: Return on investment
- **Win Rate**: Percentage of winning bets
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Wins / Losses ratio

## Security

- Never commit `.env` file
- Use environment variables for sensitive data
- Rotate API keys regularly
- Monitor API usage

## License

This is a personal betting intelligence system. Use responsibly and within legal boundaries.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in console output
3. Verify configuration settings

## Roadmap

- [ ] Real-time odds streaming
- [ ] Additional bookmaker integrations
- [ ] Advanced ML models (XGBoost, Neural Networks)
- [ ] Portfolio optimization
- [ ] Live betting support
- [ ] Mobile app integration

