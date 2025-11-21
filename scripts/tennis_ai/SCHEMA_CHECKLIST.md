# Match Results DB Schema Checklist

## Tarkistuslista Notion DB:n päivittämiseen

### Vaihe 1: Tarkista nykyinen tila

- [ ] Avaa Match Results DB Notionissa
- [ ] Laske propertyt (Settings → Properties)
- [ ] Tallenna lukumäärä: _____ propertyä

### Vaihe 2: Vertaa loggerin propertyihin

Avaa `scripts/tennis_ai/MATCH_RESULTS_DB_SCHEMA.md` ja tarkista:

- [ ] Onko kaikki 50 propertyä Notion DB:ssä?
- [ ] Vastaavatko propertynimet täsmälleen loggerin propertyihin?
- [ ] Ovatko property-tyypit oikein (Number, Select, Rich Text, Date, Checkbox)?

### Vaihe 3: Jos propertyjä puuttuu

Käytä tätä listaa tarkistamaan puuttuvat propertyt:

#### Basic Data (8)
- [ ] Match Name (Title) - **Pakollinen!**
- [ ] Match ID (Rich Text)
- [ ] Player A (Rich Text)
- [ ] Player B (Rich Text)
- [ ] Tournament (Rich Text)
- [ ] Tournament Tier (Select)
- [ ] Surface (Select)
- [ ] League (Select) - *Vapaaehtoinen*

#### Dates (3)
- [ ] Match Date (Date)
- [ ] Result Date (Date)
- [ ] Scan Date (Date)

#### Odds Data (5)
- [ ] Opening Odds A (Number)
- [ ] Opening Odds B (Number)
- [ ] Closing Odds A (Number)
- [ ] Closing Odds B (Number)
- [ ] Odds Movement (Number)

#### Player Stats (11)
- [ ] Rank A (Number)
- [ ] Rank B (Number)
- [ ] Rank Delta (Number)
- [ ] ELO A (Number)
- [ ] ELO B (Number)
- [ ] ELO Delta (Number)
- [ ] Age A (Number)
- [ ] Age B (Number)
- [ ] Form A (Rich Text)
- [ ] Form B (Rich Text)
- [ ] H2H Record (Rich Text)

#### AI Predictions (8)
- [ ] GPT-4 Prediction (Select)
- [ ] GPT-4 Confidence (Select)
- [ ] GPT-4 Score (Number)
- [ ] XGBoost Probability (Number)
- [ ] LightGBM Probability (Number)
- [ ] Ensemble Score (Number)
- [ ] Ensemble Prediction (Select)
- [ ] Model Agreement (Number)

#### Betting Info (7)
- [ ] Bet Placed (Checkbox)
- [ ] Bet Side (Select)
- [ ] Bet Odds (Number)
- [ ] Stake EUR (Number)
- [ ] Stake % (Number)
- [ ] PnL EUR (Number)
- [ ] CLV % (Number)

#### Meta (6)
- [ ] Actual Winner (Select)
- [ ] Actual Score (Rich Text)
- [ ] Status (Select)
- [ ] Data Quality (Checkbox)
- [ ] Source (Rich Text)
- [ ] Event ID (Rich Text)
- [ ] Notes (Rich Text)

### Vaihe 4: Lisää puuttuvat propertyt

Jokaiselle puuttuvalle propertylle:

1. Klikkaa "+ Add a property" Notion DB:ssä
2. Valitse oikea tyyppi:
   - **Number**: Kaikki kertoimet, rankingit, ELO, iät, scoret, todennäköisyydet
   - **Select**: Tournament Tier, Surface, Status, Predictions, Winner
   - **Rich Text**: Nimet, turnaukset, form, H2H, score, notes
   - **Date**: Kaikki päivämäärät
   - **Checkbox**: Bet Placed, Data Quality
   - **Title**: Match Name (pakollinen)
3. Anna nimi **TÄSMÄLLEEN** kuten yllä olevassa listassa
4. Tallenna

### Vaihe 5: Tarkista Select-tyyppien arvot

Varmista, että Select-tyyppisillä propertyillä on oikeat vaihtoehdot:

**Status:**
- Scanned
- Predicted
- Resulted

**Tournament Tier:**
- W15
- W25
- W35
- W50
- M15
- M25
- (lisää tarvittaessa)

**Surface:**
- Hard
- Clay
- Grass

**GPT-4 Prediction:**
- Strong Bet
- Good Bet
- Pass
- Avoid

**GPT-4 Confidence:**
- Very High
- High
- Medium
- Low

**Actual Winner:**
- Player A
- Player B

### Vaihe 6: Testaa logger

Kun kaikki propertyt on lisätty:

```bash
# 1. Aseta DB ID
# Muokkaa telegram_secrets.env:
# NOTION_MATCH_RESULTS_DB_ID=your_actual_db_id

# 2. Testaa logger
python3 -c "
from src.notion.match_results_logger import MatchResultsLogger
logger = MatchResultsLogger()
print('✅ Logger initialized')
print('Database ID:', logger.database_id or 'NOT SET')
"
```

### Vaihe 7: Testaa synkronointi

```bash
# Synkronoi Notion → SQLite
python3 src/ml/notion_sync.py --days 7
```

## Yhteenveto

- **Tavoite:** 50 propertyä Notion DB:ssä
- **ML-käyttö:** 24 propertyä synkronoidaan SQLiteen
- **Workflow:** Notion (50 prop) → SQLite (24 prop) → ML training

## Ongelmatilanteet

### Propertynimi ei täsmää
- Tarkista kirjainkoko (Match Name vs match name)
- Tarkista välilyönnit ja erikoismerkit
- Logger käyttää täsmälleen näitä nimiä

### Property-tyyppi väärä
- Number → Select: Muuta Select → Number
- Select → Rich Text: Muuta Rich Text → Select (jos tarvitaan vaihtoehdot)

### Duplikaatti propertyt
- Jos on kaksi samannimistä propertyä, poista toinen
- Varmista, että käytössä on oikea property

