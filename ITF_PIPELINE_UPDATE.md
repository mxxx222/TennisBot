# ✅ ITF Notion Pipeline - Päivitetty

## 🎯 Yhteenveto

ITF Notion Pipeline on päivitetty käyttämään uusia Notion-tietokantakenttiä, jotka vastaavat FlashScore-scraperin dataa.

## ✅ Tehdyt muutokset

### 1. Päivitetty `transform_match_to_notion()` -metodi

**Uudet kentät:**
- ✅ **Turnaus** (text) - Tournament name
- ✅ **Pelaaja 1** (text) - Player 1 name
- ✅ **Pelaaja 2** (text) - Player 2 name
- ✅ **Päivämäärä** (date) - Match date/time
- ✅ **Scraper Source** (select) - "FlashScore"
- ✅ **Alusta** (select) - Hard, Clay, Grass, Indoor
- ✅ **Status** (select) - Scheduled, Live, Finished, Postponed, Cancelled

### 2. Status-mapping

Scraperin `match_status` mappataan Notion-arvoksi:
- `not_started` → `Scheduled`
- `scheduled` → `Scheduled`
- `live` → `Live`
- `finished` → `Finished`
- `completed` → `Finished`
- `postponed` → `Postponed`
- `cancelled` → `Cancelled`

### 3. Surface-mapping

Alusta normalisoidaan Notion-arvoksi:
- `hard` → `Hard`
- `clay` → `Clay`
- `grass` → `Grass`
- `indoor` / `indoor hard` → `Indoor`
- `outdoor hard` → `Hard`

### 4. Päivämäärä-logiikka

- Käyttää `scheduled_time` jos saatavilla
- Muuten käyttää `scraped_at`

## 📊 Data Mapping

```python
# Scraper data → Notion properties
match_dict = {
    "Turnaus": match.tournament,
    "Pelaaja 1": match.player1,
    "Pelaaja 2": match.player2,
    "Päivämäärä": match.scheduled_time or match.scraped_at,
    "Scraper Source": "FlashScore",
    "Alusta": match.surface (normalized),
    "Status": match.match_status (mapped),
}
```

## 🧪 Testaus

Testi onnistui:
```bash
python3 test_itf_pipeline.py
```

**Tulokset:**
- ✅ Kaikki pakolliset kentät mappattu oikein
- ✅ Status-mapping toimii
- ✅ Surface-mapping toimii
- ✅ Päivämäärä-logiikka toimii

## 🚀 Käyttö

### 1. Varmista credentials
```bash
# Tarkista että telegram_secrets.env sisältää:
NOTION_API_KEY=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
NOTION_TENNIS_PREMATCH_DB_ID=81a70fea5de140d384c77abee225436d
```

### 2. Testaa pipeline
```bash
source venv/bin/activate
python3 src/pipelines/itf_notion_pipeline.py
```

### 3. Deploy cron-job (valinnainen)
```bash
bash scripts/setup_itf_scraper_cron.sh
```

## 📝 Tiedostot

**Päivitetty:**
- ✅ `src/pipelines/itf_notion_pipeline.py` - Päivitetty data-mapping

**Luotu:**
- ✅ `test_itf_pipeline.py` - Testiskripti

## ✅ Status

- ✅ Pipeline päivitetty uusilla kentillä
- ✅ Status- ja surface-mapping toimii
- ✅ Testit läpäisty
- ✅ Valmis tuotantokäyttöön

**ITF Notion Pipeline on nyt valmis käyttöön! 🎉**

