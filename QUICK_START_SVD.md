# 🚀 SMART VALUE DETECTOR - NOPEA KÄYTTÖÖNOTTO

## ⚡ 5 MINUUTIN SETUP

### **1. Asenna riippuvuudet**

```bash
cd TennisBot
pip install pandas numpy scipy scikit-learn aiohttp python-telegram-bot pyyaml
```

### **2. Testaa järjestelmä**

```bash
# Testaa Smart Value Detector
python src/smart_value_detector.py

# Testaa profit projection
python src/profit_projection.py
```

### **3. Konfiguroi Telegram (valinnainen)**

```bash
# Aseta environment variables
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'

# TAI käytä simple_secrets.py
python simple_secrets.py telegram
python simple_secrets.py load
```

### **4. Käynnistä järjestelmä**

```bash
# Täysi järjestelmä (Telegram-ilmoitukset)
python start_svd_system.py

# TAI vain arvovetojen tunnistus
python -c "
from src.smart_value_detector import SmartValueDetector, MatchData, PlayerStats
from datetime import datetime

# Create test match
p1 = PlayerStats(id='p1', name='Djokovic', elo=2100.0, 
                 surface_stats={'hard': 0.75}, recent_form=[0.9, 0.85, 0.9])
p2 = PlayerStats(id='p2', name='Sinner', elo=1950.0,
                 surface_stats={'hard': 0.65}, recent_form=[0.7, 0.75, 0.8])

match = MatchData(match_id='m1', player1=p1, player2=p2, 
                  surface='hard', tournament='ATP', round='Final',
                  date=datetime.now(),
                  market_odds={'player1': 2.50, 'player2': 1.55})

# Find value trades
svd = SmartValueDetector(bankroll=1000.0)
trades = svd.find_value_trades([match])

if trades:
    print(f'✅ Found {len(trades)} value trade(s)!')
    for t in trades:
        print(f'Match: {t.match_name}')
        print(f'Edge: {t.edge_percentage:.1f}%')
        print(f'Expected Value: {t.expected_value_percentage:.1f}%')
        print(f'Recommended Stake: €{t.recommended_stake:.2f}')
else:
    print('❌ No value trades found')
"
```

---

## 📊 KATSO ENNUSTEET

```bash
# Konservatiivinen ennuste (12% kuukausi ROI)
python -c "
from src.profit_projection import ProfitProjection
proj = ProfitProjection.project_conservative(1000)
ProfitProjection.print_projection(proj)
"

# Keskitaso ennuste (15% kuukausi ROI)
python -c "
from src.profit_projection import ProfitProjection
proj = ProfitProjection.project_12_months(1000, 0.15, True)
ProfitProjection.print_projection(proj)
"

# Vertaa skenaarioita
python -c "
from src.profit_projection import ProfitProjection
ProfitProjection.compare_scenarios(1000)
"
```

---

## 🎯 KESKEISET KOMENNOT

### **Smart Value Detector**

```python
from src.smart_value_detector import SmartValueDetector

svd = SmartValueDetector(bankroll=1000.0)
trades = svd.find_value_trades(matches)
report = svd.generate_daily_report()
```

### **High ROI Scraper**

```python
from src.high_roi_scraper import HighROIScraper
import asyncio

scraper = HighROIScraper()
odds = asyncio.run(scraper.scrape_all_bookmakers(['match1', 'match2']))
```

### **Backtester**

```python
from src.svd_backtester import SVDBacktester

backtester = SVDBacktester(initial_bankroll=1000.0)
result = backtester.backtest(matches, actual_results, svd)
print(backtester.generate_report(result))
```

---

## 📱 TELEGRAM BOT

```bash
# Käynnistä Telegram bot
python start_svd_system.py

# Komennot botissa:
/start - Aloita käyttö
/trades - Näytä trade-suositukset
/report - Päivittäinen raportti
/status - Botin tila
```

---

## ⚙️ KONFIGURAATIO

Muokkaa `config/svd_config.yaml`:

```yaml
smart_value_detector:
  min_edge: 0.05  # Min 5% edge
  min_confidence: 0.65  # Min 65% todennäköisyys
  kelly_fraction: 0.25  # 25% Kelly
  bankroll:
    initial: 1000.0
    daily_max_risk: 0.03  # Max 3% päivässä
```

---

## 🎉 VALMIS!

Järjestelmä on nyt käyttövalmis! Se:

✅ Tunnistaa arvovetoja automaattisesti  
✅ Käyttää Kelly Criterion -panoksen optimointia  
✅ Lähettää Telegram-ilmoituksia  
✅ Seuraa arbitraasi-mahdollisuuksia  
✅ Generoi päivittäisiä raportteja  

**Tavoite:** 15-30% kuukausi ROI konservatiivisella riskinhallinnalla

**🎾 Onnea kannattaviin tradeihin! 💰**

