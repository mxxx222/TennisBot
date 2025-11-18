# Tennis ITF Screening System - Setup Guide

## 🎯 Overview

This system automates your proven Tennis ITF betting edge (+17.81% ROI) by screening ITF Women's tennis matches daily and alerting you to opportunities in the 1.30-1.80 odds range.

## 📋 Prerequisites

- Python 3.8+ installed
- Virtual environment activated (`source venv/bin/activate`)
- Telegram bot token (already configured)
- The Odds API key (needs setup)

## 🔧 Quick Setup (5 minutes)

### Step 1: Get The Odds API Key

1. Go to [The Odds API](https://the-odds-api.com)
2. Sign up for free account (500 requests/month)
3. Get your API key from dashboard
4. Update `telegram_secrets.env`:

```bash
# Replace this line:
ODDS_API_KEY=1108325cf70df63e93c3d2aa09813f63

# With your actual key:
ODDS_API_KEY=your_actual_api_key_here
```

### Step 2: Test API Connection

```bash
cd /Users/herbspotturku/sportsbot/TennisBot
source venv/bin/activate
python3 test_api_connection.py
```

You should see:
```
✅ API connection successful!
🎾 Tennis sports available: X
✅ ITF Women's tennis found: Tennis ITF Women
```

### Step 3: Test Full System

```bash
python3 tennis_itf_screener.py --test --verbose
```

Expected output:
```
✅ Screening completed successfully!
Found X opportunities
```

### Step 4: Setup Daily Automation

```bash
python3 setup_cron.py --setup
```

This creates a cron job to run daily at 08:00 EET.

## 🎾 System Features

### What It Does Automatically

1. **Daily Screening** (08:00 EET)
   - Fetches ITF Women's tennis matches
   - Filters odds 1.30-1.80 (proven range)
   - Calculates optimal bet sizes

2. **Smart Notifications**
   - Telegram alerts for each opportunity
   - Daily summary with statistics
   - Notion database logging (if configured)

3. **Risk Management**
   - Kelly Criterion bet sizing
   - Maximum 3 picks per day
   - Bankroll percentage limits

### Manual Usage

```bash
# Test run (no notifications)
python3 tennis_itf_screener.py --test

# Live run with custom bankroll
python3 tennis_itf_screener.py --bankroll 500

# Check cron job status
python3 setup_cron.py --status
```

## 📊 Expected Performance

Based on your historical data:

- **Volume**: 40-50 bets/month (vs 14 manual)
- **ROI**: 12-18% (maintain proven edge)
- **Time**: 7 min/day (vs 30 min manual)
- **Profit**: $500-1,500/year potential

## 🔧 Configuration

### Bet Sizing Rules

- **Bankroll**: $1000 default (adjustable)
- **Unit Size**: 1% of bankroll
- **Odds 1.30-1.50**: Full unit (1.0x)
- **Odds 1.51-2.00**: 0.8 units
- **Odds 2.01-2.50**: 0.5 units
- **Max Stake**: $15 safety cap

### Filtering Criteria

- ✅ **Sport**: ITF Women's tennis only
- ✅ **Odds Range**: 1.30-1.80 (proven edge)
- ✅ **Tournament Level**: ITF/Challenger (avoid WTA/ATP)
- ✅ **Time Window**: Next 48 hours
- ✅ **Daily Limit**: Top 3 opportunities

## 🚨 Troubleshooting

### API Key Issues

```bash
# Test API connection
python3 test_api_connection.py

# Common issues:
# - 401 Error: Invalid API key
# - 429 Error: Rate limit exceeded
# - 404 Error: Sport not available
```

### No Opportunities Found

This is normal on some days. The system looks for:
- ITF Women's matches in next 48h
- Odds between 1.30-1.80
- Quality bookmaker coverage

### Telegram Not Working

Check `telegram_secrets.env`:
```bash
TELEGRAM_BOT_TOKEN=8481385860:AAGBRbsDA8--t373COn2mgM4_c1ngc2fGRM
TELEGRAM_CHAT_ID=-4956738581
```

Test with:
```bash
python3 -c "
from utils.notifiers import TelegramNotifier
import asyncio
notifier = TelegramNotifier()
asyncio.run(notifier.bot.send_message(-4956738581, 'Test message'))
"
```

### Cron Job Issues

```bash
# Check if cron job exists
crontab -l | grep screener

# Check logs
tail -f logs/cron_$(date +%Y%m%d).log

# Reinstall cron job
python3 setup_cron.py --remove
python3 setup_cron.py --setup
```

## 📈 Monitoring

### Daily Checks (2 minutes)

1. Check Telegram for alerts
2. Review opportunities in messages
3. Place bets manually
4. Log results (optional)

### Weekly Review (10 minutes)

1. Check `tennis_itf_screener.log`
2. Verify system is finding 2-3 picks/day
3. Monitor ROI in betting records
4. Adjust bankroll if needed

### Monthly Optimization

Track these metrics:
- Picks generated per day
- Win rate percentage
- ROI trend
- API usage (should be <500/month)

## 🎯 Success Metrics

### Week 1 Targets
- ✅ System runs daily without errors
- ✅ 2-3 qualified picks per day average
- ✅ All picks in 1.30-1.80 range
- ✅ Telegram alerts working

### Month 1 Targets
- ✅ 30-50 bets placed (vs 14 baseline)
- ✅ ROI maintained at +12-18%
- ✅ Zero manual screening time
- ✅ System runs autonomously

## 💰 ROI Projections

**Conservative (current edge maintained):**
- 40 bets/month × $8 avg × 15% ROI = +$576/year

**Optimistic (volume scaling):**
- 100 bets/month × $10 avg × 12% ROI = +$1,440/year

**Key**: Maintain discipline on odds range and bet sizing!

## 🆘 Support

If you encounter issues:

1. Check logs: `tail -f tennis_itf_screener.log`
2. Test components individually
3. Verify API quotas and limits
4. Review configuration files

The system is designed to be robust and self-healing. Most issues resolve automatically on the next run.

## 🚀 Next Steps

1. **Get valid API key** (most important)
2. **Run test to verify setup**
3. **Install cron job for automation**
4. **Monitor for 1 week**
5. **Scale volume gradually**

Remember: You have a proven edge. The system just automates the tedious screening work so you can focus on placing the bets and managing your bankroll.
