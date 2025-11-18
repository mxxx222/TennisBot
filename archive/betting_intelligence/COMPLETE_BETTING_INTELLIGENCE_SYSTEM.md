# 🎯 COMPLETE BETTING INTELLIGENCE SYSTEM

## Järjestelmän Kuvaus

Jatkuva vedonlyönti-äly järjestelmä, joka:

1. **🔄 Analysoi jatkuvasti pelejä** kannattavuuden, ROI:n ja riskin perusteella
2. **⚡ Ilmoittaa välittömästi Telegramiin** uusista mahdollisuuksista  
3. **🎰 Liittää Betfury.io linkit** jokaiseen matsiin
4. **🕷️ Skrapaa verkkosivuja** reaaliaikaisille tiedoille

## 🚀 Käynnistys

### Nopea käynnistys:
```bash
cd /Users/herbspotturku/sportsbot/TennisBot
python start_betting_intelligence.py
```

### Demo-tila:
```bash
python demo_betting_intelligence.py
```

## 📊 Järjestelmän Komponentit

### 1. 🔄 Continuous Betting Intelligence (`continuous_betting_intelligence.py`)
- **Jatkuva analysointi**: Skannaa pelejä 2 minuutin välein
- **ROI-analyysi**: Laskee kannattavuuden, riskin ja luottamuksen
- **Monipuolinen data**: Yhdistää useita tietolähteitä
- **Älykkäät suodattimet**: Vain parhaat mahdollisuudet

**Ominaisuudet:**
- ✅ Jatkuva pelien skannaus
- ✅ ROI, riski ja kannattavuusanalyysi  
- ✅ Välittömät Telegram-ilmoitukset
- ✅ Betfury.io vedonlyöntilinkit
- ✅ Web scraping reaaliaikaisille kertoimille
- ✅ Monipuolinen data-analyysi

### 2. 🎰 Betfury Integration (`src/betfury_integration.py`)
- **Suorat vedonlyöntilinkit** jokaiseen matsiin
- **Markkinakohtaiset linkit** (Match Winner, Over/Under, jne.)
- **Affiliate-tuki** lisätuloille
- **Mobiilioptimoidut linkit**

**Tuetut markkinat:**
- 💰 Match Winner
- 📊 Over/Under
- ⚽ Both Teams Score
- 🎯 Asian Handicap
- 🎲 Correct Score

### 3. 🤖 Enhanced Telegram Bot (`src/enhanced_telegram_roi_bot.py`)
- **Kauniit viestit** yksityiskohtaisella analyysillä
- **AI-ennustukset** voittajista
- **Riski-arviointi** ja panokset
- **Välittömät ilmoitukset** uusista mahdollisuuksista

**Viestin sisältö:**
- 🏆 Matsitiedot (joukkueet, liiga, aika)
- 💰 ROI-analyysi (kannattavuus, luottamus, edge)
- 🎯 Vedonlyöntisuositus (panos, voitto, riski)
- 🎰 Suorat Betfury.io linkit
- 🤖 AI-ennuste voittajasta

### 4. 📊 Odds API Integration (`src/odds_api_integration.py`)
- **Reaaliaikaiset kertoimet** The Odds API:sta
- **Monipuolinen bookmaker-vertailu**
- **Arbitraasi-mahdollisuuksien tunnistus**
- **Value bet -havaitseminen**

**API-ominaisuudet:**
- 🔄 Reaaliaikaiset kertoimet
- 📊 Useiden bookmakereiden vertailu
- 💰 Value betting tunnistus
- 🎯 Arbitraasi-mahdollisuudet
- 📈 Kertoimien liikkeiden seuranta

### 5. 🕷️ Web Scraping (`continuous_betting_intelligence.py`)
- **Betfury.io scraping**
- **Stake.com scraping** 
- **Rollbit.com scraping**
- **Anti-detection tekniikat**

## 🎯 Käyttöesimerkki

Kun järjestelmä löytää kannattavan mahdollisuuden, se lähettää Telegramiin viestin:

```
🚨 UUSI KANNATTAVA MAHDOLLISUUS ⚽

Real Madrid vs Barcelona
🏆 La Liga
📅 08.11.2025 13:58

💰 ANALYYSI:
• ROI: 18.5%
• Luottamus: 75%
• Edge: 12.8%
• Todennäköisyys: 69%

🎯 SUOSITUS:
• Panos: 4.2% (420€)
• Voitto: 485€
• Riski: 🟡 MODERATE

🎰 BETFURY.IO LINKIT:
• 🎰 LYÖNNIT BETFURY.IO
• 💰 Match Winner
• 📊 Over/Under

⏰ Vanhenee: 13:28
```

## ⚙️ Konfiguraatio

Järjestelmä on konfiguroitavissa:

```python
config = {
    'scan_interval': 120,        # 2 minuuttia skannauksien välillä
    'min_roi_threshold': 8.0,    # 8% minimi ROI
    'min_confidence': 0.60,      # 60% minimi luottamus
    'min_edge': 3.0,            # 3% minimi edge
    'max_daily_stake': 20.0,    # 20% max päivittäinen panos
    'sports': ['football', 'tennis', 'basketball', 'ice_hockey'],
    'telegram_notifications': True,
    'web_scraping_enabled': True,
    'odds_api_enabled': True
}
```

## 🔐 Turvallisuus

- **Salatut API-avaimet** (`simple_secrets.py`)
- **The Odds API avain** turvallisesti tallennettu
- **Telegram bot token** salattu
- **Rate limiting** API-kutsuille

## 📈 Suorituskyky

**Demo-testissä:**
- ✅ Betfury integration toimii
- ✅ Telegram bot luo viestejä Betfury-linkeillä
- ✅ Odds API yhdistetty (500 kutsua/kk)
- ✅ Web scraping kirjastot valmiina
- ✅ Jatkuva järjestelmä alustettu

## 🛠️ Riippuvuudet

Järjestelmä käyttää:
- `python-telegram-bot` - Telegram-viestintä
- `requests` - HTTP-pyynnöt
- `beautifulsoup4` - HTML-parsinta
- `selenium` - Web scraping
- `undetected-chromedriver` - Anti-detection (valinnainen)
- `pandas` - Data-analyysi
- `numpy` - Numeeriset laskut

## 🎯 Käyttöohjeet

### 1. Käynnistä järjestelmä:
```bash
python start_betting_intelligence.py
```

### 2. Järjestelmä:
- Skannaa pelejä automaattisesti
- Analysoi ROI:n ja riskin
- Lähettää Telegram-ilmoituksia
- Sisällyttää Betfury.io linkit

### 3. Seuraa Telegram-kanavaasi:
- Saat välittömiä ilmoituksia
- Klikkaa Betfury-linkkejä
- Lyö vetoa suositusten mukaan

## 🔄 Jatkuva Toiminta

Järjestelmä toimii jatkuvasti:

1. **Skannaa** pelejä useista lähteistä
2. **Analysoi** ROI:n ja riskin
3. **Suodattaa** parhaat mahdollisuudet
4. **Lähettää** Telegram-ilmoituksen
5. **Sisällyttää** Betfury.io linkit
6. **Toistaa** prosessin

## 🎉 Yhteenveto

Järjestelmä on valmis ja toimiva:

✅ **Jatkuva analysointi** - Skannaa pelejä automaattisesti  
✅ **Välittömät ilmoitukset** - Telegram-viestit uusista mahdollisuuksista  
✅ **Betfury.io integraatio** - Suorat vedonlyöntilinkit jokaiseen matsiin  
✅ **Web scraping** - Reaaliaikaiset tiedot useista lähteistä  
✅ **ROI-analyysi** - Kannattavuus, riski ja luottamus  
✅ **API-integraatiot** - The Odds API reaaliaikaisille kertoimille  

**Käynnistä järjestelmä:** `python start_betting_intelligence.py`

Järjestelmä on nyt valmis jatkuvaan käyttöön! 🚀
