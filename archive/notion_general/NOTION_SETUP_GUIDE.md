# 📝 NOTION BET LOGGER - Setup Guide

**Tarkoitus:** Automaattinen betin kirjaus Notion Bets-tietokantaan  
**ROI:** 95% säästö kirjausajassa (30 sek vs 10 min)  
**Takaisinmaksu:** 5 päivää

---

## 🚀 QUICK SETUP (5 min)

### 1. Asenna Notion Client

```bash
pip install notion-client
```

### 2. Hae Notion API Key

1. Avaa: https://www.notion.so/my-integrations
2. Klikkaa "New integration"
3. Nimi: "TennisBot Bet Logger"
4. Valitse workspace
5. Kopioi "Internal Integration Token"

### 3. Hae Bets Database ID

1. Avaa Bets-tietokanta Notioniin
2. URL näyttää: `https://www.notion.so/09a1af5850eb4cd39bff88e79ce69865?pvs=21`
3. Database ID on: `09a1af5850eb4cd39bff88e79ce69865` (32 merkkiä)

### 4. Lisää telegram_secrets.env

```bash
# Notion API
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_BETS_DATABASE_ID=09a1af5850eb4cd39bff88e79ce69865
```

### 5. Testaa

```bash
python3 notion_bet_logger.py
```

---

## 📋 BETTING_LOG_TEMPLATE.MD - Database Structure

Varmista että Bets-tietokanta Notioniin vastaa tätä rakennetta:

### Required Properties

- **Date & Time** (Date)
- **Tournament** (Text)
- **Player 1** (Text)
- **Player 2** (Text)
- **Selected Player** (Select: Player 1 / Player 2)
- **Odds** (Number, 2 decimals)
- **Stake** (Number, Currency $)
- **Bet Type** (Select: SINGLE / COMBO)
- **Result** (Select: Win / Loss / Pending / Void)
- **Tournament Level** (Select: ITF W15 / W25 / W35 / etc.)
- **Bookmaker** (Select: Bet365 / Pinnacle / etc.)

### Optional Properties

- **Player 1 Ranking** (Number)
- **Player 2 Ranking** (Number)
- **Surface** (Select: Hard / Clay / Grass)
- **Notes** (Text)
- **Profit/Loss** (Number, Currency $) - Calculated
- **ROI** (Number, Percentage) - Calculated

---

## 💻 KÄYTTÖ

### Automaattinen kirjaus

```python
from notion_bet_logger import NotionBetLogger

logger = NotionBetLogger()

# Kirjaa bet
page_id = logger.log_bet(
    tournament="ITF W15 Sharm ElSheikh 20 Women",
    player1="Maria Garcia",
    player2="Anna Smith",
    selected_player="Maria Garcia",
    odds=1.75,
    stake=10.00,
    player1_ranking=245,
    player2_ranking=312,
    surface="Hard",
    bookmaker="Bet365"
)

# Päivitä tulos
logger.update_bet_result(page_id, "Win", profit_loss=7.50)
```

### Integroitu check_itf_matches.py:hen

Skripti tarkistaa automaattisesti onko Notion logger saatavilla ja näyttää sen statuksen.

---

## 🔧 TROUBLESHOOTING

### "Notion client not available"

```bash
pip install notion-client
```

### "NOTION_API_KEY not found"

1. Tarkista että `telegram_secrets.env` sisältää `NOTION_API_KEY`
2. Tarkista että `.env` tiedosto ladataan

### "NOTION_BETS_DATABASE_ID not set"

1. Hae database ID Notion URL:sta
2. Lisää `NOTION_BETS_DATABASE_ID` `telegram_secrets.env`:ään

### "Database not found"

1. Varmista että integration on yhdistetty Bets-tietokantaan
2. Notion → Database → Connections → Add "TennisBot Bet Logger"

### "Property not found"

1. Tarkista että Bets-tietokanta vastaa `BETTING_LOG_TEMPLATE.md` rakennetta
2. Varmista että property-nimet täsmäävät

---

## 📊 ROI-ANALYYSI

### Manual Kirjaus

- **Aika:** 10 min/bet
- **5 bet/päivä:** 50 min/päivä
- **30 päivää:** 25 tuntia

### Automaattinen Kirjaus

- **Aika:** 30 sek/bet
- **5 bet/päivä:** 2.5 min/päivä
- **30 päivää:** 1.25 tuntia

### Säästö

- **Päivittäinen:** 47.5 min
- **Kuukausittainen:** 23.75 tuntia
- **Vuosittainen:** 285 tuntia

---

## ✅ VALIDATION

### Testaa Setup

```bash
python3 notion_bet_logger.py
```

**Odotettu output:**
```
✅ Notion Bet Logger initialized
✅ Test bet logged successfully!
📄 Page ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Tarkista Notioniin

1. Avaa Bets-tietokanta
2. Etsi test bet
3. Varmista että kaikki kentät täytetty oikein

---

## 🎯 NEXT STEPS

Kun automaattinen kirjaus toimii:

1. ✅ Testaa 5 betillä
2. ✅ Varmista että kaikki kentät täytetty
3. ✅ Tarkista että ROI lasketaan oikein
4. ✅ Integroi workflow:een

---

*Setup guide created: 18.11.2025*  
*ROI: 95% säästö kirjausajassa*

