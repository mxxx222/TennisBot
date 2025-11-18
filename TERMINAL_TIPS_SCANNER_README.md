# 🔍 Terminaali Vihjeskanneri

Terminaaliin tulostava vihjeskanneri, joka tarkistaa kaikki API-yhteydet ja skannaa vihjeet useista lähteistä.

## 🚀 Käyttö

### Peruskäyttö

```bash
python3 terminal_tips_scanner.py
```

### Mitä skanneri tekee:

1. **Tarkistaa API-yhteydet**
   - Odds API
   - Multi-Sport Scraper
   - Prematch Analyzer
   - Strategy Engine
   - Telegram Bot
   - OpenAI
   - Venice AI

2. **Skannaa vihjeet**
   - Odds API:sta
   - Multi-Sport Scraperista
   - Analysoi ROI ja luottamus

3. **Näyttää vihjeet terminaalissa**
   - Värikoodattu tulostus
   - ROI, luottamus, edge
   - Suositukset ja mahdollinen voitto

## 📋 Vaatimukset

### API-avaimet

Aseta ympäristömuuttujat tai `.env` tiedostoon:

```bash
export ODDS_API_KEY="your_odds_api_key"
export TELEGRAM_BOT_TOKEN="your_telegram_token"  # Vapaaehtoinen
export OPENAI_API_KEY="your_openai_key"  # Vapaaehtoinen
export VENICE_API_KEY="your_venice_key"  # Vapaaehtoinen
```

### Python-paketit

```bash
pip install colorama  # Värillinen terminaalitulostus (vapaaehtoinen)
```

## 📊 Vihjeiden tiedot

Jokainen vihje sisältää:

- **Ottelu**: Kotijoukkue vs Vierasjoukkue
- **Urheilulaji**: ⚽ Football, 🎾 Tennis, 🏀 Basketball, 🏒 Ice Hockey
- **Liga**: Esim. English Premier League
- **Aika**: Ottelun alkamisaika
- **Markkina**: Esim. Match Winner
- **Valinta**: Ennustettu voittaja
- **Kertoimet**: Parhaat saatavilla olevat kertoimet
- **ROI**: Odotettu tuotto prosentteina
- **Luottamus**: Ennusteen luottamustaso (0-100%)
- **Edge**: Markkinoiden yliarviointi
- **Suositus**: Suositeltu panos prosentteina
- **Mahdollinen voitto**: Odotettu voitto dollareina

## 🎨 Värikoodit

- 🔥 **Vihreä**: ROI ≥ 15% (Erinomainen)
- ⭐ **Keltainen**: ROI ≥ 10% (Hyvä)
- 💡 **Syan**: ROI ≥ 5% (Hyväksyttävä)

## ⚙️ Jatkuva skannaus

Kun vihjeitä löytyy, voit valita jatkuvan skannauksen:

```
Haluatko ajaa jatkuvaa skannausta? (y/n): y
```

Jatkuva skannaus:
- Skannaa vihjeet automaattisesti
- Oletusväli: 5 minuuttia
- Pysäytä: `Ctrl+C`

## 🔧 Vianetsintä

### Ei vihjeitä löytynyt

1. Tarkista API-avaimet:
   ```bash
   echo $ODDS_API_KEY
   ```

2. Tarkista että API-avaimet ovat voimassa

3. Tarkista verkkoyhteys

### Import-virheet

Jos näet `ModuleNotFoundError`:
- Varmista että olet projektin juurikansiossa
- Tarkista että `src/` hakemisto on olemassa

### API-virheet

Jos Odds API antaa 401-virheen:
- Tarkista API-avain
- Varmista että avain on voimassa
- Tarkista API-kvootit

## 📝 Esimerkki tulostus

```
================================================================================
🔍 TERMINAALI VIHJESKANNERI
================================================================================

============================================================
🔍 TARKISTETAAN API-YHTEYDET
============================================================

📊 Tarkistetaan Odds API...
✅ Odds API saatavilla
🌐 Tarkistetaan Multi-Sport Scraper...
✅ Scraper saatavilla
...

💰 LÖYDETYT VIHJEET (3 kpl)

🔥 VIHJE #1
⚽ Manchester United vs Liverpool
   📅 English Premier League
   ⏰ 2025-11-18 20:00
   🎯 Match Winner: Liverpool
   💰 Kertoimet: 2.10
   🔥 ROI: 18.5%
   📊 Luottamus: 72.0%
   📈 Edge: 8.2%
   💵 Suositus: 3.5% panoksesta
   💰 Mahdollinen voitto: $77
   📡 Lähde: Odds API
```

## 🎯 Vinkit

1. **Parhaat vihjeet**: Korkea ROI (≥15%) + korkea luottamus (≥70%)
2. **Riskinhallinta**: Älä panosta yli suositeltua prosenttia
3. **Diversifiointi**: Älä panosta kaikkea yhteen otteluun
4. **Aikataulu**: Parhaat vihjeet löytyvät 2-6 tuntia ennen ottelua

## 📞 Tuki

Jos kohtaat ongelmia:
1. Tarkista että kaikki riippuvuudet on asennettu
2. Tarkista API-avaimet
3. Tarkista verkkoyhteys
4. Katso logitiedostot virheilmoituksista

---

**Huomio**: Tämä on työkalu vihjeiden löytämiseen. Älä panosta enempää kuin voit menettää. Vedonlyönti sisältää riskejä.

