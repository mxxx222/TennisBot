# 🤖 Telegram ROI Bot for Tennis Predictions

⚠️ **IMPORTANT DISCLAIMER**: This project is intended for **EDUCATIONAL AND RESEARCH PURPOSES ONLY**.

- This system demonstrates AI-powered tennis prediction and ROI analysis
- Users are responsible for complying with all applicable laws and terms of service
- The authors disclaim any responsibility for misuse or violations
- Use only with explicit permission from website owners
- Implement proper rate limiting and respectful scraping practices

## 🎯 Overview

The **Telegram ROI Bot** is an advanced AI-powered system that automatically analyzes live tennis matches and sends real-time notifications about the most profitable betting opportunities. Using machine learning models with 70%+ accuracy targets, the bot identifies high-ROI matches and provides comprehensive betting recommendations with risk assessments.

### 🎾 Key Features

- **🤖 AI-Powered Predictions**: Ensemble ML models (Random Forest, Gradient Boosting, Logistic Regression) for 70%+ accuracy
- **💰 ROI Analysis**: Automated calculation of return on investment for all predictions
- **📱 Telegram Integration**: Real-time notifications with beautiful formatted messages
- **🛡️ Risk Assessment**: Color-coded risk levels and betting guidance
- **🔄 Continuous Monitoring**: 24/7 analysis of live tennis matches
- **🎨 Interactive Commands**: Multiple bot commands for on-demand analysis
- **📊 Multi-Source Data**: Scraping from multiple tennis websites and APIs
- **⚡ Real-Time Updates**: Automatic notifications for high-value opportunities

## 📋 Requirements

- **Python**: 3.11+
- **Browser**: Chrome/Chromium (for web scraping)
- **Telegram Bot Token**: Required for bot functionality
- **Dependencies**: See `requirements.txt`
- **Optional**: Docker for containerized deployment

## ⚡ Quick Start (5 Minutes)

### 1. **Get Telegram Bot Token**
```bash
# Open Telegram, search for @BotFather
# Send /newbot and follow instructions
# Copy your bot token (format: 123456789:ABCdefGHI...)
```

### 2. **Setup Environment**
```bash
# Clone repository
git clone <repository>
cd TennisBot

# Install dependencies
pip install -r requirements.txt

# Set bot token
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
```

### 3. **Start the Bot**
```bash
# Start Telegram ROI Bot
python tennis_roi_telegram.py
```

### 4. **Subscribe to Notifications**
- Find your bot on Telegram (search for the username you created)
- Send `/start` command
- Start receiving ROI notifications automatically! 🚀

## 🔧 Configuration

### Environment Variables
```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional
TELEGRAM_CHAT_ID=your_chat_id_here
DEBUG=true
```

### Bot Settings (Default)
```json
{
  "min_confidence": 0.25,        // 25% minimum confidence
  "min_roi_percentage": 10.0,    // 10% minimum ROI
  "max_risk_level": 0.3,         // 30% maximum risk
  "notification_cooldown": 300    // 5 minutes between notifications
}
```

### Custom Configuration
Create `config/telegram_config.json`:
```json
{
  "bot_token": "your_bot_token_here",
  "notification_settings": {
    "min_confidence": 0.25,
    "min_roi_percentage": 10.0,
    "max_risk_level": 0.3,
    "notification_cooldown_seconds": 300
  },
  "message_settings": {
    "include_emojis": true,
    "detailed_analysis": true,
    "show_risk_warning": true
  }
}
```

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Subscribe to ROI notifications |
| `/roi` | Get current best ROI matches |
| `/predictions` | See all current predictions |
| `/settings` | View bot configuration |
| `/help` | Show help message |
| `/stop` | Unsubscribe from notifications |

## 💰 ROI Analysis & Notifications

### 🎯 What Gets Notified
The bot automatically sends notifications when it finds:
- ✅ **High-confidence predictions** (≥25% confidence)
- 💰 **High ROI potential** (≥10% return)
- 🛡️ **Acceptable risk levels** (≤30% risk)
- 🎯 **Clear betting recommendations**

### 📊 Sample ROI Notification
```
💰 BEST ROI TENNIS MATCHES

🏆 Match 1: Djokovic N vs Alcaraz C
🎯 Predicted Winner: Djokovic N
📊 Win Probability: 65.3%
⭐ Confidence: 32.1%
💰 ROI: 18.5%
💵 Potential Profit: $185 (on $1000 stake)
🎲 Odds: 1.85
🛡️ Risk Level: 🟢 LOW
🏟️ Surface: Hard
🏆 Tournament: ATP Masters 1000
💎 Recommendation: EXCELLENT BET

🎯 Target Accuracy: 70%+
⚠️ Always bet responsibly and within your limits
```

### 🛡️ Risk Categories
- 🟢 **LOW RISK**: ≤20% risk level
- 🟡 **MEDIUM RISK**: 21-40% risk level
- 🟠 **HIGH RISK**: 41-60% risk level
- 🔴 **VERY HIGH RISK**: >60% risk level

### 💎 Betting Recommendations
- 💎 **EXCELLENT BET**: ROI ≥20%, Low Risk
- 🔥 **STRONG BET**: ROI ≥15%, Low-Medium Risk
- 💡 **GOOD BET**: ROI ≥10%, Medium Risk
- ⚠️ **AVOID**: Low confidence or high risk

## 🚀 Deployment Options

### 🐳 Docker Deployment
```bash
# Build and run with Docker
docker build -t tennis-roi-bot .
docker run -e TELEGRAM_BOT_TOKEN=your_token_here tennis-roi-bot
```

### 🔄 Background Service (Linux)
```bash
# Run deployment script
./deploy_telegram_bot.sh

# Or manually create systemd service
sudo cp /tmp/tennis-roi-bot.service /etc/systemd/system/
sudo systemctl enable tennis-roi-bot
sudo systemctl start tennis-roi-bot
```

### ☁️ Cloud Deployment
- **Vercel**: See `web/VERCEL_DEPLOYMENT_GUIDE.md`
- **AWS/GCP**: Use Docker containers
- **Heroku**: Standard Python deployment

## 📊 System Architecture

### 🔄 Data Flow
```
Live Tennis Matches → Web Scraping → AI Predictions → ROI Analysis → Telegram Notifications
```

### 🤖 AI Models
- **Random Forest**: Ensemble decision trees
- **Gradient Boosting**: XGBoost implementation
- **Logistic Regression**: Probability-based predictions
- **Feature Engineering**: Match statistics, player rankings, surface analysis

### 📈 Performance Metrics
- **Prediction Accuracy**: 70%+ target
- **ROI Identification**: High-value opportunities only
- **Notification Quality**: 2-5 high-ROI matches per day
- **Response Time**: <30 seconds for analysis

## 🔧 Usage Examples

### Start Bot and Monitor
```bash
# Terminal 1: Start the bot
python tennis_roi_telegram.py

# Terminal 2: Test predictions
python demo_predictions.py
```

### Interactive Analysis
```python
from src.telegram_roi_bot import TennisROIBot

# Initialize bot
bot = TennisROIBot(token="your_token")

# Get current ROI matches
roi_matches = await bot.get_best_roi_matches()

# Send notification
await bot.send_roi_notification(roi_matches)
```

### Custom ROI Analysis
```python
from src.predict_winners import TennisWinnerPredictor

# Initialize predictor
predictor = TennisWinnerPredictor()
predictor.setup()

# Get predictions with custom criteria
predictions = predictor.scrape_and_predict(
    max_live_matches=20,
    max_upcoming_matches=30
)
```

## 🔍 Troubleshooting

### Common Issues

**Bot not responding?**
```bash
# Check if bot is running
ps aux | grep tennis_roi_telegram

# Check logs
tail -f data/telegram_bot.log
```

**No notifications received?**
1. Verify bot token is correct
2. Ensure you sent `/start` to your bot
3. Check bot has message sending permissions
4. Review logs for errors

**Import errors?**
```bash
# Install missing packages
pip install python-telegram-bot scikit-learn pandas numpy

# Update requirements
pip install -r requirements.txt
```

### 📁 Important Files
- **Bot logs**: `data/telegram_bot.log`
- **Predictions**: `data/tennis_predictions_*.json`
- **Config**: `config/telegram_config.json`
- **Test results**: `data/telegram_bot_test_*.json`

## 📈 Expected Performance

### 🎯 Accuracy Targets
- **Prediction Accuracy**: 70%+ (ensemble ML models)
- **ROI Identification**: High-value opportunities only
- **Risk Assessment**: Conservative approach with warnings

### 💰 ROI Expectations
- **Excellent Bets**: 20%+ ROI, Low Risk (1-2 per day)
- **Strong Bets**: 15%+ ROI, Low-Medium Risk (2-3 per day)
- **Good Bets**: 10%+ ROI, Medium Risk (3-5 per day)

### 📊 Notification Frequency
- **High ROI matches**: 2-5 per day (depending on tennis schedule)
- **Excellent opportunities**: 1-2 per day
- **Spam prevention**: 5-minute cooldown between similar notifications

## ⚖️ Legal & Ethical Guidelines

### 🛡️ Responsible Betting
- **Always bet responsibly** and within your limits
- **Never bet more than you can afford to lose**
- **Use predictions as guidance, not guarantees**
- **Past performance doesn't guarantee future results**

### ⚖️ Legal Compliance
1. **Rate Limiting**: Minimum 5-second delays between requests
2. **User-Agent**: Clear identification as research bot
3. **Respect robots.txt**: Follow website crawling guidelines
4. **Data Privacy**: Store only aggregated/anonymized data
5. **Terms Compliance**: Verify usage permissions

## 🤝 Contributing

Contributions welcome for educational improvements:
- Documentation enhancements
- AI model optimizations
- Telegram bot features
- Risk assessment improvements
- Security enhancements

## 📝 License

This project is provided for educational purposes. Users are responsible for ensuring compliance with applicable laws and regulations.

## ⚠️ Important Warning

**DO NOT USE FOR ACTUAL BETTING WITHOUT PROPER LICENSING AND LEGAL COMPLIANCE**

This system is designed for learning and research. Any real-money gambling requires proper regulatory approval and licensing.

---

*Built for educational purposes • AI-powered predictions • ROI-focused analysis*