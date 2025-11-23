# 🔍 GitHub Actions Workflow Status Check

## Cron-ajot (Scheduled Workflows)

### ITF Rankings Scraper
- **Schedule:** Daily at 08:00 EET (06:00 UTC)
- **Cron:** `0 6 * * *`
- **Workflow file:** `.github/workflows/itf-rankings-scraper.yml`
- **Created:** 2025-11-23

### Match History Scraper
- **Schedule:** Daily at 09:00 EET (07:00 UTC)
- **Cron:** `0 7 * * *`
- **Workflow file:** `.github/workflows/match-history-scraper.yml`
- **Created:** 2025-11-23

---

## Tarkista Workflow Status

### Vaihtoehto 1: GitHub CLI (paikallinen)

```bash
# Asenna GitHub CLI jos ei ole
brew install gh

# Autentikoi
gh auth login

# Tarkista workflow runs
gh run list --workflow=itf-rankings-scraper.yml --limit 5
gh run list --workflow=match-history-scraper.yml --limit 5

# Tai käytä skriptiä
./scripts/check_workflow_status.sh
```

### Vaihtoehto 2: GitHub Web UI

1. Mene: `https://github.com/[OWNER]/[REPO]/actions`
2. Etsi workflowt:
   - "ITF Rankings Scraper"
   - "Match History Scraper"
3. Tarkista:
   - Onko workflowt ajettu?
   - Mikä on status (success/failure)?
   - Milloin viimeksi ajettu?

### Vaihtoehto 3: Manual Trigger (Test)

1. Mene GitHub → Actions
2. Valitse workflow (esim. "ITF Rankings Scraper")
3. Klikkaa "Run workflow" (oikealla ylhäällä)
4. Valitse branch: `main`
5. Klikkaa "Run workflow"

---

## Miksi Workflowt Eivät Voi Olla Ajaneet?

### 1. Workflowt Luotu Liian Myöhään

**Ongelma:**
- Workflows luotu 2025-11-23
- Cron-ajot alkavat vasta seuraavana päivänä
- Jos luotu 23.11, ensimmäinen ajo olisi 24.11 klo 08:00/09:00 EET

**Ratkaisu:**
- Odota seuraavaa päivää
- Tai käytä "Run workflow" -nappia testaamaan heti

### 2. GitHub Actions Ei Ole Aktivoitu

**Tarkista:**
- Repository Settings → Actions → General
- Varmista että "Allow all actions and reusable workflows" on päällä

### 3. Secrets Puuttuvat

**Tarkista:**
- Repository Settings → Secrets and variables → Actions
- Varmista että seuraavat secrets on asetettu:
  - `NOTION_API_KEY`
  - `NOTION_TOKEN` (optional, fallback)
  - `PLAYER_CARDS_DB_ID`

### 4. Workflow Syntax Virhe

**Tarkista:**
- GitHub → Actions → Workflows
- Jos workflow näkyy punaisena, on syntax-virhe
- Korjaa workflow-tiedosto

---

## Tarkista Onko Workflowt Ajettu

### Tarkista Notion Player Cards

**ITF Rankings:**
1. Avaa Notion Player Cards database
2. Tarkista muutama pelaaja
3. Onko "ITF Rank" -kenttä päivitetty?

**Match History:**
1. Avaa Notion Player Cards database
2. Tarkista muutama pelaaja
3. Onko "Win Rate" tai "Recent Form" päivitetty?

### Tarkista GitHub Actions Logs

1. Mene GitHub → Actions
2. Valitse workflow run
3. Tarkista logs:
   - Onko Playwright asennettu?
   - Onko Notion API yhteys toiminut?
   - Onko scrapersit ajettu?

---

## Debugging

### Jos Workflowt Eivät Aja Automaattisesti

1. **Tarkista cron-syntax:**
   ```yaml
   schedule:
     - cron: '0 6 * * *'  # 06:00 UTC = 08:00 EET
   ```

2. **Tarkista timezone:**
   - GitHub Actions käyttää UTC
   - EET = UTC + 2 (talvi) / UTC + 3 (kesä)

3. **Testaa manual trigger:**
   - "Run workflow" -nappi testaa että workflow toimii
   - Jos manual trigger toimii, cron toimii myös

### Jos Workflowt Epäonnistuvat

1. **Tarkista logs:**
   - GitHub → Actions → Failed run → Logs
   - Etsi virheviestit

2. **Yleiset ongelmat:**
   - Playwright browser installation failed
   - Notion API key invalid
   - Database ID incorrect
   - Timeout errors

3. **Korjaus:**
   - Tarkista GitHub Secrets
   - Tarkista että Playwright browsers on asennettu
   - Tarkista timeout-asetukset

---

## Seuraavat Askeleet

1. ✅ **Tarkista workflow status** (GitHub CLI tai Web UI)
2. ✅ **Testaa manual trigger** (varmista että workflowt toimivat)
3. ✅ **Odota seuraavaa päivää** (cron-ajot alkavat automaattisesti)
4. ✅ **Tarkista Notion Player Cards** (varmista että data päivittyy)

---

## Linkit

- **GitHub Actions:** `https://github.com/[OWNER]/[REPO]/actions`
- **Workflow Documentation:** `WORKFLOW_TESTING.md`
- **Test Results:** `SCRAPER_TEST_RESULTS.md`

