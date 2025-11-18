# 🚨 Monitoring & Alerts Setup

## Alert Thresholds

The system automatically monitors and alerts on:

### 1. Error Rate Alert (>10%)
- **Trigger**: Error rate exceeds 10% of total requests
- **Severity**: Critical
- **Cooldown**: 60 minutes
- **Action**: Review scraper stability, check logs

### 2. ROI Opportunity Alert (>5% EV)
- **Trigger**: ROI opportunity with EV > 5% detected
- **Severity**: Info
- **Cooldown**: None (always alert on high-value opportunities)
- **Action**: Review opportunity, consider placing bet

### 3. Pipeline Timeout Alert (>2 hours)
- **Trigger**: Pipeline hasn't updated in 2+ hours
- **Severity**: Critical
- **Cooldown**: 60 minutes
- **Action**: Check if scraper is running, restart if needed

## Configuration

Edit `config/tennisexplorer_config.yaml`:

```yaml
monitoring:
  alert_thresholds:
    error_rate_percent: 10.0
    roi_opportunity_ev_percent: 5.0
    pipeline_timeout_minutes: 120
    alert_cooldown_minutes: 60
```

## Alert Channels

### Discord
1. Create Discord webhook:
   - Server Settings → Integrations → Webhooks → New Webhook
   - Copy webhook URL
2. Add to `telegram_secrets.env`:
   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

### Telegram
1. Create bot via @BotFather
2. Get chat ID (send message to bot, visit `https://api.telegram.org/bot<TOKEN>/getUpdates`)
3. Add to `telegram_secrets.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=xxx:xxx
   TELEGRAM_CHAT_ID=your_chat_id
   ```

## Testing Alerts

```python
from src.monitoring.tennisexplorer_monitor import TennisExplorerMonitor
from src.alerts.roi_alert_manager import ROIAlertManager

# Test monitor
monitor = TennisExplorerMonitor()

# Simulate high error rate
for _ in range(20):
    monitor.record_error(Exception("Test error"), "test_context")

# Check alert
alert = monitor.record_error(Exception("Test"), "test")
if alert.get('should_alert'):
    print(f"🚨 Alert: {alert['message']}")

# Test ROI opportunity alert
manager = ROIAlertManager()
test_opportunity = {
    'match_id': 'test_123',
    'player_a': 'Player A',
    'player_b': 'Player B',
    'tournament': 'ITF W15 Test',
    'current_score': '4-6, 3-2',
    'strategy': 'Momentum Shift',
    'expected_value_pct': 18.5,
    'kelly_stake_pct': 2.3,
    'current_odds': 2.10,
    'reasoning': 'Test opportunity'
}

await manager.send_alert(test_opportunity)
```

## Weekly Reports

Weekly reports are automatically generated every Monday at 8:00 AM.

### Report Contents
- Total matches scraped
- Average matches per day
- ROI opportunities detected
- Enrichment success rate
- Error rate
- Uptime statistics
- Insights and recommendations

### Manual Report Generation

```python
from src.notion.weekly_report_generator import WeeklyReportGenerator
from datetime import datetime, timedelta

generator = WeeklyReportGenerator()

end_date = datetime.now()
start_date = end_date - timedelta(days=7)

# Get metrics from monitor
metrics = monitor.get_metrics_summary()

# Generate and store
report = generator.generate_weekly_report(metrics, start_date, end_date)
page_id = generator.store_weekly_report(report)
```

## Monitoring Dashboard

View real-time metrics:
- Project Status page in Notion (auto-updates)
- Logs: `logs/tennisexplorer_scraper.log`
- Monitor summary: `python3 -c "from src.monitoring.tennisexplorer_monitor import TennisExplorerMonitor; m = TennisExplorerMonitor(); print(m.get_metrics_summary())"`

