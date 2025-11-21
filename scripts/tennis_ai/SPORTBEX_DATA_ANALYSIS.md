# Sportbex API Data Analysis
## Mitä Sportbex API tarjoaa vs. mitä tarvitaan

## ✅ Sportbex API tarjoaa (toteutettu koodissa)

### Basic Match Data
1. **Event ID** - Yksilöllinen ottelun ID
2. **Event Name** - "Player A v Player B" format
3. **Player 1** - Pelaaja 1 nimi (parsittu event namesta)
4. **Player 2** - Pelaaja 2 nimi (parsittu event namesta)
5. **Tournament/Competition Name** - Turnauksen nimi
6. **Tournament Tier** - Parsittu turnauksen nimestä (W15, W25, W35, etc.)
7. **Start Time/Commence Time** - Ottelun alkamisaika
8. **Surface** - Ei suoraan saatavilla (tarvitaan erillinen haku)

### Odds Data (Betfair Market)
9. **Opening Odds Player 1** - Alkuperäiset kertoimet (availableToBack tai lastPriceTraded)
10. **Opening Odds Player 2** - Alkuperäiset kertoimet
11. **Closing Odds Player 1** - Lopulliset kertoimet (jos haetaan myöhemmin)
12. **Closing Odds Player 2** - Lopulliset kertoimet (jos haetaan myöhemmin)
13. **Market ID** - Betfair market ID
14. **Market Name** - "Match Odds" yleensä

### Tournament Data
15. **Competition ID** - Turnauksen ID
16. **Sport ID** - Tennis = 2
17. **Competition Type** - ITF, ATP, WTA (parsittu nimestä)

### Raw Data
18. **Raw Event Data** - Koko event-objekti (tallennettu raw_data-kenttään)

---

## ❌ Sportbex API EI tarjoa (mutta tarvitaan)

### Player Statistics (kriittiset puuttuvat)
1. **Rank A** - Pelaajan A ranking (WTA/ATP ranking)
2. **Rank B** - Pelaajan B ranking
3. **Rank Delta** - Laskettu: Rank B - Rank A
4. **ELO A** - Pelaajan A ELO-pisteet
5. **ELO B** - Pelaajan B ELO-pisteet
6. **ELO Delta** - Laskettu: ELO A - ELO B
7. **Age A** - Pelaajan A ikä
8. **Age B** - Pelaajan B ikä

### Match Context (puuttuvat)
9. **Surface** - Kenttätyyppi (Hard, Clay, Grass) - ei saatavilla API:sta
10. **League** - ITF, ATP, WTA (voidaan parsia, mutta ei varmaa)

### Historical Performance (puuttuvat)
11. **Form A** - Pelaajan A viimeiset 5 ottelua (W/L-tulos)
12. **Form B** - Pelaajan B viimeiset 5 ottelua
13. **H2H Record** - Head-to-head historia (esim. "2-1")
14. **Surface Win % A** - Pelaajan A voittoprosentti tällä kentällä
15. **Surface Win % B** - Pelaajan B voittoprosentti tällä kentällä

### Match Results (puuttuvat - haetaan myöhemmin)
16. **Actual Winner** - Kuka voitti (Player A/B)
17. **Actual Score** - Tulos (esim. "6-4, 6-2")
18. **Result Date** - Milloin tulos tuli

### Odds Movement (puuttuvat - vaatii seurannan)
19. **Odds Movement** - Kertoimien muutos (CLV tracking)
20. **Opening vs Closing Odds** - Vaatii kaksi hakuhetkeä

---

## 📊 Yhteenveto

### Sportbex API tarjoaa: **~18 kenttää**
- ✅ Basic match info (8)
- ✅ Odds data (5)
- ✅ Tournament info (3)
- ✅ Raw data (2)

### Tarvitaan lisäksi: **~20 kenttää**
- ❌ Player stats (8): Ranking, ELO, Age
- ❌ Match context (2): Surface, League
- ❌ Historical (5): Form, H2H, Surface win %
- ❌ Results (3): Winner, Score, Result date
- ❌ Odds tracking (2): Movement, CLV

### Täydennyslähteet

#### 1. ITF Rankings API / WTA/ATP Rankings
- **Ranking A/B** - Viralliset rankingit
- **Age A/B** - Pelaajan ikä
- **Source**: ITF, WTA, ATP viralliset API:t tai scrapers

#### 2. ELO Rating Systems
- **ELO A/B** - ELO-pisteet
- **Source**: 
  - Tennis Abstract (tennisabstract.com)
  - Ultimate Tennis Statistics
  - Oma ELO-laskenta (jos historiallista dataa)

#### 3. Flashscore / ITF Scrapers
- **Surface** - Kenttätyyppi
- **Form A/B** - Viimeiset ottelut
- **H2H Record** - Head-to-head
- **Surface Win %** - Voittoprosentit
- **Source**: Flashscore scraper, ITF scraper

#### 4. Match Results
- **Actual Winner** - Kuka voitti
- **Actual Score** - Tulos
- **Result Date** - Milloin tulos tuli
- **Source**: 
  - Sportbex API (jos tarjoaa myöhemmin)
  - Flashscore scraper
  - ITF results scraper

#### 5. Odds Tracking
- **Odds Movement** - Seuranta ajan mittaan
- **CLV** - Closing Line Value
- **Source**: 
  - Sportbex API (useita hakuhetkiä)
  - Betfair API (jos saatavilla)

---

## 🔧 Toteutussuositukset

### Vaihe 1: Perusdata (Sportbex API)
```python
# Sportbex API tarjoaa:
- Match ID, Players, Tournament, Start Time
- Opening Odds (yksi hakuhetki)
```

### Vaihe 2: Täydennys Flashscore/ITF scrapereilla
```python
# Flashscore scraper täydentää:
- Surface (Hard/Clay/Grass)
- Form (viimeiset 5 ottelua)
- H2H Record
- Surface Win %
```

### Vaihe 3: Rankings (ITF/WTA/ATP)
```python
# Rankings API/scraper täydentää:
- Rank A/B
- Age A/B (jos saatavilla)
```

### Vaihe 4: ELO (Tennis Abstract / oma laskenta)
```python
# ELO täydentää:
- ELO A/B
- ELO Delta
```

### Vaihe 5: Results (Flashscore / ITF)
```python
# Results scraper täydentää:
- Actual Winner
- Actual Score
- Result Date
```

### Vaihe 6: Odds Tracking (Sportbex API - useita hakuhetkiä)
```python
# Odds tracking (vaatii useita hakuhetkiä):
- Closing Odds (haku ottelun jälkeen)
- Odds Movement (closing - opening)
- CLV % (laskettu)
```

---

## 📈 Prioriteetti

### Korkea prioriteetti (ML-koulutukseen välttämättömät)
1. **Rank A/B** - Ranking-ero on tärkein feature
2. **Surface** - Kenttätyyppi vaikuttaa voittomahdollisuuksiin
3. **Form A/B** - Viimeinen suorituskyky
4. **ELO A/B** - Parempi kuin ranking yksinään
5. **Actual Winner/Score** - ML-koulutuksen target

### Keskiarvoinen prioriteetti (parantavat mallia)
6. **H2H Record** - Historia pelaajien välillä
7. **Surface Win %** - Kenttäkohtainen suorituskyky
8. **Age A/B** - Ikä voi vaikuttaa
9. **Odds Movement** - CLV tracking

### Matala prioriteetti (hyödylliset, mutta ei kriittiset)
10. **League** - Voidaan parsia turnauksen nimestä
11. **Odds Tracking** - Vaatii useita hakuhetkiä

---

## 🎯 Suositus: Hybrid-arkkitehtuuri

**Sportbex API** (perusdata + odds)
  ↓
**Flashscore Scraper** (surface, form, H2H, results)
  ↓
**Rankings API/Scraper** (rankings, age)
  ↓
**ELO Calculator** (ELO-pisteet)
  ↓
**Match Results DB** (Notion) - 50 propertyä täytetty

Tämä yhdistelmä tarjoaa kaikki 50 propertyä ilman riippuvuutta yksittäisestä API:sta.

