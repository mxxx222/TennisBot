# 🚀 NOTION QUICK SETUP - NOPEA KÄYTTÖÖNOTTO

## ⚡ 3 VAIHEEN SETUP

### **VAIHE 1: Luo Integration**

1. **Mene:** https://www.notion.so/my-integrations
2. **Klikkaa:** "+ New integration"
3. **Täytä lomake:**
   ```
   Name: TennisBot ROI System
   Workspace: [Valitse oma työtilasi]
   Type: Internal
   Logo: [Valinnainen]
   ```
4. **Klikkaa:** "Submit"
5. **Kopioi:** "Internal Integration Token" (näyttää: `secret_abc123xyz...`)

---

### **VAIHE 2: Linkitä Sivulle**

1. **Avaa** Notion-sivu johon haluat lisätä tietokannat
2. **Klikkaa** "..." (kolme pistettä) oikealla yläkulmassa
3. **Valitse** "Connections" tai "Add connections"
4. **Etsi** "TennisBot ROI System" → **Klikkaa** "Add"
5. **Varmista** että tila on "Connected"
6. **Kopioi** sivun ID URL:sta:
   ```
   URL: notion.so/[workspace]/[page-id]
   Kopioi vain [page-id] osa (32 merkkiä)
   ```

---

### **VAIHE 3: Luo Tietokannat**

#### **Vaihtoehto A: Automaattinen (Suositeltu)**

```bash
# Suorita skripti
python create_notion_databases.py --token YOUR_TOKEN --page-id YOUR_PAGE_ID

# TAI interaktiivinen tila
python create_notion_databases.py --interactive
```

#### **Vaihtoehto B: Python-koodissa**

```python
from src.notion_mcp_integration import NotionMCPIntegration

# Initialize
integration = NotionMCPIntegration()
integration.initialize_notion_client("secret_abc123xyz...")

# Create all databases
parent_page_id = "your-page-id-here"
databases = integration.create_roi_database_structure(parent_page_id)

print(f"✅ Created {len(databases)} databases!")
```

---

## 📊 MITÄ LUODAAN

Automaattisesti luodaan **5 tietokantaa**:

1. 🎾 **Tennis Matches & ROI Analysis**
   - Match data, odds, probabilities
   - Edge, Expected Value, ROI
   - Stake recommendations

2. ⚽ **Football Matches & ROI Analysis**
   - Match data, odds (Home/Draw/Away)
   - Edge, Expected Value, ROI
   - Stake recommendations

3. 🏀 **Basketball Matches & ROI Analysis**
   - Match data, odds
   - Edge, Expected Value, ROI
   - Stake recommendations

4. 🏒 **Ice Hockey Matches & ROI Analysis**
   - Match data, odds
   - Edge, Expected Value, ROI
   - Stake recommendations

5. 💰 **ROI Analysis & Performance**
   - Daily/weekly/monthly summaries
   - Win rates, Sharpe ratio
   - Profit/Loss tracking

---

## ✅ VALMIS!

Kun tietokannat on luotu:

1. ✅ Tarkista Notion - tietokannat näkyvät sivullasi
2. ✅ Aloita datan synkronointi:
   ```python
   integration.sync_match_to_notion(match_data, 'tennis')
   integration.sync_roi_analysis(roi_data)
   ```

---

## 🔒 TURVALLISUUS

⚠️ **TÄRKEÄÄ:**
- Älä jaa tokenia julkisesti
- Älä commitoi tokenia Git-repositorioon
- Käytä `.env`-tiedostoa tai secret manageria
- Token tallennetaan `config/notion_databases.json` (lisää `.gitignore`)

---

## 📞 TROUBLESHOOTING

### **"Unauthorized" -virhe**
- ✅ Tarkista että token on oikein
- ✅ Varmista että integration on linkitetty sivulle

### **"Page not found" -virhe**
- ✅ Tarkista että page ID on oikein
- ✅ Varmista että integrationilla on oikeudet sivulle

### **"Rate limit exceeded"**
- ✅ Odota hetki ja yritä uudelleen
- ✅ Notion API:lla on rate limiting

---

## 🎯 SEURAAVAT ASKELEET

1. **Luo integration** → https://www.notion.so/my-integrations
2. **Linkitä sivuun** → Connections → Add
3. **Suorita:** `python create_notion_databases.py --interactive`
4. **Valmis!** → Tietokannat näkyvät Notionissa

**🚀 Aloita datan synkronointi ja nauti ROI-seurannasta! 💰**






