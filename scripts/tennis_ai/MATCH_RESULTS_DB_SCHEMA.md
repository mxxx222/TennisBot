# Match Results DB Schema - 50 Properties

## Täydellinen property-lista

Tämä dokumentti listaa kaikki 50 propertyä, joita `match_results_logger.py` tukee.

### Basic Data (8 properties)

1. **Match Name** (Title) - Ottelun nimi "Player A vs Player B"
2. **Match ID** (Rich Text) - Yksilöllinen match ID
3. **Player A** (Rich Text) - Pelaaja A nimi
4. **Player B** (Rich Text) - Pelaaja B nimi
5. **Tournament** (Rich Text) - Turnauksen nimi
6. **Tournament Tier** (Select) - W15, W25, W35, etc.
7. **Surface** (Select) - Hard, Clay, Grass
8. **League** (Select) - ITF, ATP, WTA

### Dates (3 properties)

9. **Match Date** (Date) - Ottelun päivämäärä
10. **Result Date** (Date) - Tuloksen päivämäärä
11. **Scan Date** (Date) - Skannauspäivämäärä

### Odds Data (5 properties)

12. **Opening Odds A** (Number) - Alkuperäiset kertoimet pelaajalle A
13. **Opening Odds B** (Number) - Alkuperäiset kertoimet pelaajalle B
14. **Closing Odds A** (Number) - Lopulliset kertoimet pelaajalle A
15. **Closing Odds B** (Number) - Lopulliset kertoimet pelaajalle B
16. **Odds Movement** (Number) - Kertoimien muutos (CLV tracking)

### Player Stats (11 properties)

17. **Rank A** (Number) - Pelaajan A ranking
18. **Rank B** (Number) - Pelaajan B ranking
19. **Rank Delta** (Number) - Ranking-ero
20. **ELO A** (Number) - Pelaajan A ELO-pisteet
21. **ELO B** (Number) - Pelaajan B ELO-pisteet
22. **ELO Delta** (Number) - ELO-ero
23. **Age A** (Number) - Pelaajan A ikä
24. **Age B** (Number) - Pelaajan B ikä
25. **Form A** (Rich Text) - Pelaajan A viimeiset 5 ottelua
26. **Form B** (Rich Text) - Pelaajan B viimeiset 5 ottelua
27. **H2H Record** (Rich Text) - Head-to-head -historia

### AI Predictions (8 properties)

28. **GPT-4 Prediction** (Select) - Strong Bet, Good Bet, Pass, Avoid
29. **GPT-4 Confidence** (Select) - Very High, High, Medium, Low
30. **GPT-4 Score** (Number) - 0-100 pistettä
31. **XGBoost Probability** (Number) - 0-100 todennäköisyys
32. **LightGBM Probability** (Number) - 0-100 todennäköisyys
33. **Ensemble Score** (Number) - Yhdistetty pistemäärä
34. **Ensemble Prediction** (Select) - Player A, Player B, Skip
35. **Model Agreement** (Number) - 0-1 mallien yhtäpitävyys

### Betting Info (7 properties)

36. **Bet Placed** (Checkbox) - Onko veto asetettu
37. **Bet Side** (Select) - Player A, Player B
38. **Bet Odds** (Number) - Veton kertoimet
39. **Stake EUR** (Number) - Panos euroina
40. **Stake %** (Number) - Panos prosentteina
41. **PnL EUR** (Number) - Voitto/tappio euroina
42. **CLV %** (Number) - Closing Line Value prosentteina

### Meta (6 properties)

43. **Actual Winner** (Select) - Player A, Player B
44. **Actual Score** (Rich Text) - Todellinen tulos (esim. "6-4, 6-2")
45. **Status** (Select) - Scanned, Predicted, Resulted
46. **Data Quality** (Checkbox) - Onko data laadukasta
47. **Source** (Rich Text) - Mistä data tulee (Stage 1 Scanner, etc.)
48. **Event ID** (Rich Text) - Sportbex event ID
49. **Notes** (Rich Text) - Muistiinpanot

### Yhteensä: 49-50 properties

**Huom:** Match Name on Title-tyyppi (pakollinen), muut ovat valinnaisia.

## Notion DB:n päivitysohjeet

### Vaihe 1: Tarkista nykyinen schema

1. Avaa Match Results DB Notionissa
2. Laske propertyt (Settings → Properties)
3. Jos < 50, jatka vaiheeseen 2

### Vaihe 2: Lisää puuttuvat propertyt

Käytä tätä listaa tarkistamaan, mitkä propertyt puuttuvat:

**Peruspropertyt (tarkista nämä ensin):**
- Match Name (Title) - pitäisi olla jo
- Player A, Player B
- Tournament, Tournament Tier
- Match Date, Status

**Jos puuttuu, lisää:**
1. Klikkaa "+ Add a property"
2. Valitse property-tyyppi (Number, Select, Rich Text, Date, Checkbox)
3. Anna nimi TÄSMÄLLEEN kuten yllä olevassa listassa
4. Tallenna

### Vaihe 3: Tarkista property-tyypit

Varmista, että property-tyypit vastaavat:

- **Number**: Rank A, Rank B, Odds, Scores, Probabilities
- **Select**: Tournament Tier, Surface, Status, Predictions
- **Rich Text**: Player names, Tournament, Form, Notes
- **Date**: Match Date, Result Date, Scan Date
- **Checkbox**: Bet Placed, Data Quality
- **Title**: Match Name (pakollinen)

### Vaihe 4: Testaa logger

Kun kaikki 50 propertyä on lisätty:

```bash
python3 -c "
from src.notion.match_results_logger import MatchResultsLogger
logger = MatchResultsLogger()
print('✅ Logger initialized')
print('Database ID:', logger.database_id or 'NOT SET')
"
```

## ML-käyttöön tarvittavat propertyt (24)

Kun synkronoidaan Notion → SQLite, tarvitaan vain nämä:

### Core Data (12)
- Match Name, Match ID, Player A, Player B
- Tournament, Tournament Tier, Surface
- Match Date, Result Date
- Status, Actual Winner, Actual Score

### Odds (4)
- Opening Odds A, Opening Odds B
- Closing Odds A, Closing Odds B

### Player Stats (6)
- Rank A, Rank B, Rank Delta
- ELO A, ELO B, ELO Delta

### Results (2)
- Actual Winner, Actual Score

**Yhteensä: 24 propertyä ML:ään**

Muut propertyt (AI predictions, betting info) jätetään pois SQLite-synkronoinnista, koska ne eivät ole ML-treenauksessa välttämättömiä.

