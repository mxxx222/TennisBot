# ITF Scrapers Overview

## Kaksi Eri Lähdettä

ITF-tennisprojekti käyttää **kahta eri lähdettä** eri tietotarpeisiin:

### 1. FlashScore.com - Ottelutiedot

**Tiedostot:**
- `src/scrapers/flashscore_itf_scraper.py` - Pääscraper
- `src/scrapers/flashscore_itf_enhanced.py` - Parannettu versio (suositeltu)
- `src/scrapers/flashscore_itf_scraper_old.py` - Vanha versio (voidaan poistaa)

**Mitä scrapaa:**
- ITF W15/W35/W50 turnausten ottelut
- Reaaliaikaiset tulokset
- Otteluaikataulut
- Turnausinformaatio
- Pelaajien ottelutiedot

**Käyttö:**
- Päivittäiset ottelutiedot
- Live-seuranta
- Notion-pipelineen syöttö

### 2. ITFTennis.com - Pelaajatiedot

**Tiedosto:**
- `src/scrapers/itf_player_scraper.py`

**Mitä scrapaa:**
- Viralliset ITF-rankingit
- Pelaajien tilastot (voitto%, erät, jne.)
- Alustakohtaiset tilastot (Hard/Clay/Grass)
- Viimeisimmät tulokset
- Pelaajaprofiilit

**Käyttö:**
- Viikoittaiset pelaajaprofiilien päivitykset
- Notion Player Profiles -tietokantaan
- AI-analyysin tueksi

## Miksi Kaksi Lähdettä?

1. **FlashScore**: Paras reaaliaikaisille ottelutiedoille ja tuloksille
2. **ITFTennis**: Virallinen lähde pelaajatilastoille ja rankingeille

## Integraatio

Molemmat scraperit integroituvat Notion-pipelineen:
- FlashScore → Tennis Prematch Database (ottelut)
- ITFTennis → Player Profiles Database (pelaajat)

## Käyttö

```bash
# FlashScore scraper (ottelut)
python run_itf_scraper.py

# ITF Player scraper (pelaajat) - tulevaisuudessa
python src/scrapers/itf_player_scraper.py
```
