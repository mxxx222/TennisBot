# 🔄 ZAPIER/MAKE.COM AUTOMATION GUIDE

**Tavoite:** Automatisoi Notion ROI -järjestelmän päivitykset ja notifikaatiot

---

## 📋 SISÄLLYSLUETTELO

1. [Zapier vs Make.com](#zapier-vs-makecom)
2. [Flow 1: Match Results Auto-Update](#flow-1-match-results-auto-update)
3. [Flow 2: Odds Monitor](#flow-2-odds-monitor)
4. [Flow 3: Strategy Alert](#flow-3-strategy-alert)
5. [Telegram-integraatio](#telegram-integraatio)
6. [Testaus](#testaus)

---

## ZAPIER VS MAKE.COM

### Zapier
- ✅ Helpompi käyttää (drag & drop)
- ✅ Enemmän integraatioita (5000+)
- ❌ Kalliimpi (alk. 19.99$/kk)
- ❌ Rajoitetumpi logiikka

### Make.com (Integromat)
- ✅ Halvempi (alk. 9$/kk)
- ✅ Tehokkaampi logiikka
- ✅ Visuaalinen scenario builder
- ❌ Vähemmän integraatioita

**Suositus:** Make.com (parempi hinta/laatu -suhde)

---

## FLOW 1: MATCH RESULTS AUTO-UPDATE

**Tavoite:** Päivitä ottelutulokset automaattisesti Notioniin

### Vaihe 1: Luo Make.com -tili

1. Mene: https://www.make.com/en/register
2. Luo tili (ilmainen 14 päivän trial)
3. Vahvista sähköposti

### Vaihe 2: Luo Scenario

1. **Klikkaa:** `Create a new scenario`
2. **Nimeä:** `Football Match Results Auto-Update`

### Vaihe 3: Lisää Trigger (Webhook)

1. **Lisää moduuli:** `Webhooks` → `Custom webhook`
2. **Luo webhook:** `Add` → Nimeä: `Match Results Webhook`
3. **Kopioi webhook URL** (esim: `https://hook.eu1.make.com/abc123...`)
4. **Tallenna:** `config/zapier_webhooks.json` → `match_results_update.url`

### Vaihe 4: Lisää SofaScore/API-Football Trigger (vaihtoehtoinen)

**Jos haluat automaattisen triggeröinnin:**

1. **Lisää moduuli:** `HTTP` → `Make a request`
2. **URL:** `https://api.sofascore.com/api/v1/sport/football/events/live`
3. **Method:** `GET`
4. **Schedule:** Every 5 minutes
5. **Parse response:** JSON

### Vaihe 5: Lisää Notion Update (Ottelut)

1. **Lisää moduuli:** `Notion` → `Update a Database Item`
2. **Connection:** Luo Notion-yhteys (käytä Notion Integration Tokenia)
3. **Database ID:** Kopioi `Jalkapallo - Ottelut` database ID
4. **Mapping:**
   - `Status` → `Finished`
   - `Koti maalit` → `{{home_goals}}`
   - `Vieras maalit` → `{{away_goals}}`

### Vaihe 6: Lisää Notion Query (Hae Vedot)

1. **Lisää moduuli:** `Notion` → `Search Objects`
2. **Database ID:** Kopioi `Jalkapallo - Vedot` database ID
3. **Filter:**
   - `Analytiikka` → `Ottelu` → `Match ID` = `{{match_id}}`
   - `Tulos` = `Pending`

### Vaihe 7: Lisää Notion Update (Vedot)

1. **Lisää moduuli:** `Notion` → `Update a Database Item`
2. **Iterator:** Käy läpi kaikki löydetyt vedot
3. **Mapping:**
   - `Tulos` → `Won` tai `Lost` (logiikka alla)

**Logiikka (Won/Lost):**

```javascript
// Esimerkki: OU2.5 veto
if (bet_type === "OU2.5") {
  total_goals = home_goals + away_goals;
  if (total_goals > 2.5) {
    return "Won";
  } else {
    return "Lost";
  }
}

// Esimerkki: 1X2 veto (koti voittaa)
if (bet_type === "1X2" && selection === "Home") {
  if (home_goals > away_goals) {
    return "Won";
  } else {
    return "Lost";
  }
}

// Lisää logiikkaa muille bet-tyypeille...
```

### Vaihe 8: Testaa Scenario

1. **Klikkaa:** `Run once`
2. **Lähetä test webhook:**

```bash
curl -X POST https://hook.eu1.make.com/abc123... \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": "test123",
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "home_goals": 3,
    "away_goals": 2,
    "status": "Finished"
  }'
```

3. **Tarkista Notionissa:** Päivittyikö ottelu ja vedot?

### Vaihe 9: Aktivoi Scenario

1. **Klikkaa:** `ON` (yläreunassa)
2. **Scenario on nyt aktiivinen!**

---

## FLOW 2: ODDS MONITOR

**Tavoite:** Seuraa kerroinmuutoksia ja lähetä notifikaatio kun Edge > 4%

### Vaihe 1: Luo Scenario

1. **Luo:** `Football Odds Monitor`

### Vaihe 2: Lisää Schedule Trigger

1. **Lisää moduuli:** `Tools` → `Schedule`
2. **Interval:** Every 30 minutes
3. **Start time:** 08:00
4. **End time:** 23:00

### Vaihe 3: Lisää Pinnacle API Call

1. **Lisää moduuli:** `HTTP` → `Make a request`
2. **URL:** `https://api.pinnacle.com/v1/odds`
3. **Method:** `GET`
4. **Headers:**
   - `Authorization`: `Basic [base64(username:password)]`
5. **Query parameters:**
   - `sportId`: `29` (Football)
   - `leagueIds`: `1980,2196,2627` (Premier League, La Liga, Bundesliga)

**Huom:** Tarvitset Pinnacle API-avaimen (https://www.pinnacle.com/en/api/)

### Vaihe 4: Lisää Notion Query (Hae Analytiikka)

1. **Lisää moduuli:** `Notion` → `Search Objects`
2. **Database ID:** `Jalkapallo - Analytiikka`
3. **Filter:** `Ottelu` → `Status` = `Scheduled`

### Vaihe 5: Lisää Iterator

1. **Lisää moduuli:** `Flow Control` → `Iterator`
2. **Array:** `{{notion_results}}`

### Vaihe 6: Lisää Odds Comparison Logic

1. **Lisää moduuli:** `Tools` → `Set variable`
2. **Variables:**
   - `old_odds` = `{{notion_item.Kerroin}}`
   - `new_odds` = `{{pinnacle_odds}}`
   - `market_prob` = `1 / new_odds * 100`

### Vaihe 7: Lisää Notion Update (Analytiikka)

1. **Lisää moduuli:** `Notion` → `Update a Database Item`
2. **Mapping:**
   - `Markkina probability %` → `{{market_prob}}`

**Edge % lasketaan automaattisesti Notionissa!**

### Vaihe 8: Lisää Filter (Edge > 4%)

1. **Lisää moduuli:** `Flow Control` → `Router`
2. **Filter:** `Edge %` > 4

### Vaihe 9: Lisää Telegram Notification

1. **Lisää moduuli:** `Telegram Bot` → `Send a Text Message`
2. **Bot Token:** Kopioi `config/zapier_webhooks.json` → `telegram.bot_token`
3. **Chat ID:** Kopioi `config/zapier_webhooks.json` → `telegram.chat_id`
4. **Message:**

```
🎯 VALUE BET ALERT!

Match: {{home_team}} vs {{away_team}}
League: {{league}}
Bet Type: {{bet_type}}

📊 Analysis:
Edge: {{edge_pct}}%
Oma probability: {{own_prob}}%
Markkina probability: {{market_prob}}%

💰 Odds: {{new_odds}}
Min kerroin: {{min_odds}}

🎲 Recommendation: PLAY
```

### Vaihe 10: Testaa & Aktivoi

1. **Testaa:** `Run once`
2. **Aktivoi:** `ON`

---

## FLOW 3: STRATEGY ALERT

**Tavoite:** Lähetä notifikaatio kun strategia tarvitsee tarkistusta

### Vaihe 1: Luo Scenario

1. **Luo:** `Strategy Alert Monitor`

### Vaihe 2: Lisää Notion Trigger

1. **Lisää moduuli:** `Notion` → `Watch Database Items`
2. **Database ID:** `Jalkapallo - Strategiat`
3. **Trigger:** When item is updated

### Vaihe 3: Lisää Filter (Alert Check)

1. **Lisää moduuli:** `Flow Control` → `Router`
2. **Filter 1:** `Alert` contains `⚠️`
3. **Filter 2:** `Alert` contains `❌`

### Vaihe 4: Lisää Telegram Notification (Warning)

**Route 1 (⚠️):**

1. **Lisää moduuli:** `Telegram Bot` → `Send a Text Message`
2. **Message:**

```
⚠️ STRATEGY WARNING

Strategy: {{strategy_name}}
Alert: {{alert}}

📊 Performance:
Win Rate: {{win_rate}}%
ROI: {{roi}}%
Vedot yhteensä: {{total_bets}}

🔍 Action Required:
- Review strategy criteria
- Analyze recent losses
- Consider pausing strategy
```

### Vaihe 5: Lisää Telegram Notification (Critical)

**Route 2 (❌):**

1. **Lisää moduuli:** `Telegram Bot` → `Send a Text Message`
2. **Message:**

```
❌ STRATEGY CRITICAL ALERT

Strategy: {{strategy_name}}
Alert: {{alert}}

📊 Performance:
Win Rate: {{win_rate}}%
ROI: {{roi}}%
Vedot yhteensä: {{total_bets}}

🚨 IMMEDIATE ACTION REQUIRED:
- PAUSE strategy immediately
- Review all recent bets
- Analyze what went wrong
- Update criteria before reactivating
```

### Vaihe 6: Testaa & Aktivoi

1. **Testaa:** Päivitä strategian Alert-kenttä Notionissa
2. **Tarkista:** Saapuiko Telegram-notifikaatio?
3. **Aktivoi:** `ON`

---

## TELEGRAM-INTEGRAATIO

### Vaihe 1: Luo Telegram Bot

1. **Avaa Telegram**
2. **Etsi:** `@BotFather`
3. **Lähetä:** `/newbot`
4. **Nimeä bot:** `Football ROI Bot`
5. **Username:** `football_roi_bot` (tai muu vapaa)
6. **Kopioi:** Bot Token (esim: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Vaihe 2: Hae Chat ID

1. **Lähetä viesti botillesi:** `/start`
2. **Avaa selaimessa:**
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. **Etsi:** `"chat":{"id":123456789`
4. **Kopioi:** Chat ID

### Vaihe 3: Tallenna Telegram-tiedot

1. **Avaa:** `config/zapier_webhooks.json`
2. **Päivitä:**
   ```json
   {
     "telegram": {
       "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
       "chat_id": "123456789"
     }
   }
   ```

### Vaihe 4: Testaa Telegram-integraatio

```bash
# Testaa webhook_handler.py
python src/webhook_handler.py

# Toisessa terminaalissa, lähetä test webhook:
curl -X POST http://localhost:5000/webhook/strategy-alert \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "Form Edge OU2.5",
    "alert": "⚠️ Palauta, WR alle 48%",
    "win_rate": 45,
    "roi": -5
  }'
```

**Tarkista:** Saapuiko Telegram-notifikaatio?

---

## TESTAUS

### Test 1: Match Results Auto-Update

```bash
# Lähetä test webhook
curl -X POST https://hook.eu1.make.com/YOUR_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": "test_match_1",
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "home_goals": 3,
    "away_goals": 2,
    "status": "Finished"
  }'
```

**Tarkista Notionissa:**
1. ✅ Ottelu päivitetty (Status = Finished, maalit)
2. ✅ Vedot päivitetty (Tulos = Won/Lost)
3. ✅ ROI % laskettu automaattisesti

### Test 2: Odds Monitor

1. **Aja scenario manuaalisesti:** `Run once`
2. **Tarkista Notionissa:**
   - ✅ Markkina probability % päivitetty
   - ✅ Edge % laskettu automaattisesti
3. **Tarkista Telegramissa:**
   - ✅ Notifikaatio saapui (jos Edge > 4%)

### Test 3: Strategy Alert

1. **Päivitä Notionissa:** Strategian Alert-kenttä → `⚠️ Palauta, WR alle 48%`
2. **Tarkista Telegramissa:**
   - ✅ Warning-notifikaatio saapui
3. **Päivitä Notionissa:** Alert → `❌ Poistetaan, negatiivinen ROI`
4. **Tarkista Telegramissa:**
   - ✅ Critical-notifikaatio saapui

---

## 🎯 YHTEENVETO

**Olet konfiguroinut:**

- ✅ 3 Make.com -scenariota
- ✅ Automaattinen ottelutulospäivitys
- ✅ Kerroinmuutosten seuranta (30 min välein)
- ✅ Strategia-alertit
- ✅ Telegram-notifikaatiot

**Odotettu hyöty:**

- ⏱️ Säästää 1-2 tuntia päivässä
- 🎯 Ei missaa value-vetoja (automaattinen notifikaatio)
- 🚨 Nopea reagointi huonoihin strategioihin
- 📊 Reaaliaikainen ROI-seuranta

**Seuraavat askeleet:**

1. Seuraa scenarioiden toimintaa 1-2 viikkoa
2. Optimoi notifikaatioiden kynnysarvoja (Edge % > 4% → 5%?)
3. Lisää uusia scenarioita (esim. Live-betting alerts)
4. Integroi lisää bookmaker-API:ta (Bet365, 1xBet)

**🚀 Automatisointi valmis! 💰**

