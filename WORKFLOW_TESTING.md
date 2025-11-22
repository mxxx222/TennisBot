# 🧪 Workflow Testing Guide

## Testaa GitHub Actions Workflows

### 1. ITF Rankings Scraper Workflow

**Testaus:**
1. Mene GitHub → Actions → "ITF Rankings Scraper"
2. Klikkaa "Run workflow" (oikealla ylhäällä)
3. Valitse branch: `main`
4. Klikkaa "Run workflow"

**Validoi tulokset:**
- Workflow suoritetaan onnistuneesti (vihreä ✓)
- Tarkista Notion Player Cards:
  - ITF Rank -kenttä päivittyy pelaajille
  - Tarkista muutama pelaaja manuaalisesti Notionissa

**Odotettu tulos:**
- ✅ Workflow suoritetaan ilman virheitä
- ✅ ITF Rank -kentät päivittyvät Player Cardseihin
- ✅ Logs eivät näytä Playwright-virheitä

---

### 2. Match History Scraper Workflow

**Testaus:**
1. Mene GitHub → Actions → "Match History Scraper"
2. Klikkaa "Run workflow" (oikealla ylhäällä)
3. Valitse branch: `main`
4. Klikkaa "Run workflow"

**Validoi tulokset:**
- Workflow suoritetaan onnistuneesti (vihreä ✓)
- Tarkista Notion Player Cards:
  - Win Rate -kenttä päivittyy
  - Recent Form -kenttä päivittyy
  - Total Matches -kenttä päivittyy
  - Last Updated -kenttä päivittyy

**Odotettu tulos:**
- ✅ Workflow suoritetaan ilman virheitä
- ✅ Win Rate + Recent Form päivittyvät Player Cardseihin
- ✅ Logs eivät näytä Playwright-virheitä

---

## Validoi Notion Player Cards

### Tarkista ITF Rank

1. Avaa Notion Player Cards database
2. Etsi muutama pelaaja (esim. top 10)
3. Tarkista että "ITF Rank" -kenttä on päivitetty
4. Verrataan ITF:n virallisiin rankingseihin

### Tarkista Match History

1. Avaa Notion Player Cards database
2. Etsi pelaajia joilla on Win Rate -kenttä
3. Tarkista että:
   - Win Rate on prosentti (0-100)
   - Recent Form on merkkijono (esim. "WWLWW")
   - Total Matches on numero
   - Last Updated on päivämäärä

---

## Tarkista Sentry Dashboard

### Playwright-virheet

1. Mene Sentry Dashboard
2. Filtteröi:
   - Component: `itf_rankings_scraper` tai `match_history_scraper`
   - Error type: Playwright-related errors
3. Tarkista että ei uusia Playwright-virheitä

**Odotettu tulos:**
- ✅ Ei Playwright timeout-virheitä
- ✅ Ei Playwright selector-virheitä
- ✅ Ei Playwright browser launch -virheitä

---

## Troubleshooting

### Workflow epäonnistuu

1. **Tarkista logs:**
   - GitHub Actions → Workflow run → Job → Step logs
   - Etsi virheviestit

2. **Yleiset ongelmat:**
   - Playwright browser installation failed
   - Notion API key invalid
   - Database ID incorrect
   - Timeout errors

3. **Korjaus:**
   - Tarkista GitHub Secrets (NOTION_API_KEY, PLAYER_CARDS_DB_ID)
   - Tarkista että Playwright browsers on asennettu
   - Tarkista timeout-asetukset

### Notion-kentät eivät päivity

1. **Tarkista Notion API:**
   - Integration on jaettu Player Cards databaseen
   - API key on validi

2. **Tarkista kenttien nimet:**
   - "ITF Rank" (ei "ITF Ranking")
   - "Win Rate" (ei "WinRate")
   - "Recent Form" (ei "RecentForm")

3. **Tarkista logit:**
   - Etsi "Updated" -viestit
   - Etsi "Error updating" -viestit

---

## Seuraavat askeleet

Jos kaikki testit läpäisevät:

1. ✅ Requirements.txt päivitetty (playwright==1.56.0)
2. ✅ Workflows päivitetty
3. ✅ Commit & push tehty
4. ✅ Workflows testattu GitHub Actionsissa
5. ✅ Notion Player Cards validoitu
6. ✅ Sentry dashboard tarkistettu

**Valmis!** 🎉

