# 🤖 TELEGRAM ROI BOT SETUP GUIDE

## 🎾 Tennis ROI Telegram Bot - Complete Setup

Your Telegram bot will automatically send you notifications about the **best ROI tennis matches** with high-confidence predictions and betting opportunities!

---

## 🚀 **QUICK START (5 Minutes)**

### Step 1: Create Your Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Choose a name for your bot (e.g., "My Tennis ROI Bot")
4. Choose a username (e.g., "my_tennis_roi_bot")
5. **Copy the bot token** you receive (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Set Your Bot Token
```bash
# Method 1: Environment Variable (Recommended)
export TELEGRAM_BOT_TOKEN='your_bot_token_here'

# Method 2: Or create config file
echo '{"bot_token": "your_bot_token_here"}' > config/telegram_config.json
```

### Step 3: Start the Bot
```bash
# Activate virtual environment
source venv/bin/activate

# Start the ROI bot
python tennis_roi_telegram.py
```

### Step 4: Subscribe to Notifications
1. Find your bot on Telegram (search for the username you created)
2. Send `/start` command to your bot
3. You'll start receiving ROI notifications automatically!

---

## 📱 **BOT COMMANDS**

| Command | Description |
|---------|-------------|
| `/start` | Subscribe to ROI notifications |
| `/roi` | Get current best ROI matches |
| `/predictions` | See all current predictions |
| `/settings` | View bot configuration |
| `/help` | Show help message |
| `/stop` | Unsubscribe from notifications |

---

## 💰 **WHAT YOU'LL RECEIVE**

### 🚨 **Automatic ROI Notifications**
The bot monitors tennis matches 24/7 and sends you notifications when it finds:
- ✅ **High-confidence predictions** (≥25% confidence)
- 💰 **High ROI potential** (≥10% return)
- 🛡️ **Acceptable risk levels**

### 📊 **Sample Notification**
```
🚨 NEW HIGH-ROI OPPORTUNITIES!

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
```

---

## ⚙️ **CONFIGURATION**

### ROI Criteria (Default Settings)
- **Minimum Confidence**: 25%
- **Minimum ROI**: 10%
- **Maximum Risk Level**: 30%
- **Notification Cooldown**: 5 minutes

### Notification Settings
- **Real-time monitoring** every 10 minutes
- **Automatic filtering** for best opportunities
- **Risk assessment** included in all recommendations
- **Duplicate prevention** to avoid spam

---

## 🔧 **ADVANCED SETUP**

### Running as Background Service
```bash
# Create systemd service
python tennis_roi_telegram.py --service

# Install and start service
sudo cp /tmp/tennis-roi-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tennis-roi-bot
sudo systemctl start tennis-roi-bot

# Check status
sudo systemctl status tennis-roi-bot
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

---

## 🎯 **ROI CALCULATION**

The bot calculates ROI using:
1. **AI Prediction Confidence** (70% accuracy target)
2. **Implied Odds** from win probability
3. **Market Odds** estimation (with bookmaker margin)
4. **Risk Assessment** based on confidence levels

### ROI Formula
```
ROI = ((Potential Return - Stake) / Stake) × 100
```

### Risk Categories
- 🟢 **LOW RISK**: ≤20% risk level
- 🟡 **MEDIUM RISK**: 21-40% risk level  
- 🟠 **HIGH RISK**: 41-60% risk level
- 🔴 **VERY HIGH RISK**: >60% risk level

---

## 📊 **FEATURES**

### ✅ **What the Bot Does**
- 🔍 **Continuous Monitoring**: Scans live tennis matches 24/7
- 🤖 **AI Analysis**: Uses machine learning for 70% accuracy predictions
- 💰 **ROI Calculation**: Identifies profitable betting opportunities
- 📱 **Smart Notifications**: Only sends high-value opportunities
- 🛡️ **Risk Assessment**: Includes risk levels and warnings
- 📊 **Multiple Commands**: Interactive commands for on-demand data

### 🎯 **Betting Recommendations**
- 💎 **EXCELLENT BET**: ROI ≥20%, Low Risk
- 🔥 **STRONG BET**: ROI ≥15%, Low-Medium Risk
- 💡 **GOOD BET**: ROI ≥10%, Medium Risk
- ⚠️ **AVOID**: Low confidence or high risk

---

## 🔍 **TROUBLESHOOTING**

### Common Issues

**Bot not responding?**
```bash
# Check if bot is running
ps aux | grep tennis_roi_telegram

# Check logs
tail -f data/telegram_bot.log
```

**No notifications received?**
1. Make sure you sent `/start` to your bot
2. Check if bot token is correct
3. Verify bot has permission to send messages

**Import errors?**
```bash
# Install missing packages
pip install python-telegram-bot
pip install scikit-learn pandas numpy
```

### Log Files
- **Bot logs**: `data/telegram_bot.log`
- **Scraping logs**: `data/scraping.log`
- **Predictions**: `data/tennis_predictions_*.json`

---

## 🚀 **USAGE EXAMPLES**

### Start Bot and Get Immediate ROI Analysis
```bash
# Terminal 1: Start the bot
python tennis_roi_telegram.py

# Terminal 2: Test predictions
python demo_predictions.py
```

### Get Current ROI Matches
Send `/roi` to your bot to get:
```
💰 BEST ROI TENNIS MATCHES

🏆 Match 1: Djokovic N vs Musetti L
🎯 Predicted Winner: Djokovic N (68.2%)
💰 ROI: 22.3%
💵 Potential Profit: $223 (on $1000 stake)
🛡️ Risk Level: 🟢 LOW
💎 Recommendation: EXCELLENT BET
```

### Monitor Continuously
The bot automatically:
1. ✅ Scans matches every 10 minutes
2. 🎯 Analyzes with 70% accuracy AI models
3. 💰 Calculates ROI for each prediction
4. 📱 Sends notifications for best opportunities
5. 🛡️ Includes risk warnings and betting guidance

---

## 📈 **EXPECTED PERFORMANCE**

### Accuracy Targets
- **Prediction Accuracy**: 70%+ with ensemble ML models
- **ROI Identification**: High-value opportunities only
- **Risk Assessment**: Conservative approach with warnings

### Notification Frequency
- **High ROI matches**: 2-5 per day (depending on tennis schedule)
- **Excellent opportunities**: 1-2 per day
- **Spam prevention**: 5-minute cooldown between similar notifications

---

## ⚠️ **IMPORTANT DISCLAIMERS**

### Responsible Betting
- 🛡️ **Always bet responsibly** and within your limits
- 💰 **Never bet more than you can afford to lose**
- 📊 **Use predictions as guidance, not guarantees**
- 🎯 **Past performance doesn't guarantee future results**

### Risk Warning
- 📈 All betting involves risk
- 🎾 Tennis matches can be unpredictable
- 💡 Use multiple sources for betting decisions
- ⚠️ Consider this as one tool in your analysis toolkit

---

## 🎾 **READY TO START?**

Your Tennis ROI Telegram Bot is ready to help you find profitable tennis betting opportunities!

```bash
# Quick start command
python tennis_roi_telegram.py
```

**Enjoy profitable tennis betting with AI-powered ROI analysis! 🚀💰**
