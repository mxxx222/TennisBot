# 🔑 NOTION API TOKEN - HAKEMISOHJE

## 📋 VAIHE 1: KIRJAUDU NOTIONIIN

1. Mene: https://www.notion.so/my-integrations
2. Kirjaudu sisään Notion-tilillesi
3. Jos et ole vielä kirjautunut, käytä jotain näistä:
   - Google-tili
   - Apple-tili
   - Microsoft-tili
   - Sähköposti

## 📋 VAIHE 2: LUO UUSI INTEGRATION

1. Kun olet kirjautunut, näet "My integrations" -sivun
2. Klikkaa **"+ New integration"** -painiketta
3. Täytä lomake:
   - **Name**: `TennisBot ROI System` (tai mikä tahansa nimi)
   - **Logo**: (valinnainen) Voit lisätä logon
   - **Associated workspace**: Valitse työtilasi
   - **Type**: Valitse "Internal" (jos vain oma käyttö)

4. Klikkaa **"Submit"**

## 📋 VAIHE 3: KOPIOI API TOKEN

1. Kun integration on luotu, näet sen sivulla
2. Klikkaa juuri luomaasi integrationia
3. Etsi **"Internal Integration Token"** tai **"API Key"** -kenttä
4. Klikkaa **"Show"** tai **"Reveal"** nähdäksesi tokenin
5. **Kopioi token** (se näyttää suunnilleen: `secret_abc123xyz...`)

## 📋 VAIHE 4: TALLENNA TOKEN

### **Vaihtoehto 1: Environment Variable**

```bash
export NOTION_TOKEN='secret_abc123xyz...'
```

### **Vaihtoehto 2: .env-tiedosto**

Luo `.env`-tiedosto projektin juureen:

```bash
NOTION_TOKEN=secret_abc123xyz...
```

### **Vaihtoehto 3: Python-koodissa**

```python
from src.notion_mcp_integration import NotionMCPIntegration

integration = NotionMCPIntegration()
integration.initialize_notion_client("secret_abc123xyz...")
```

## 📋 VAIHE 5: ANNA OIKEUDET INTEGRATIONILLE

1. Mene Notioniin
2. Avaa sivu johon haluat lisätä tietokannat
3. Klikkaa **"..."** (kolme pistettä) oikealla yläkulmassa
4. Valitse **"Connections"** tai **"Add connections"**
5. Valitse juuri luomasi integration
6. Nyt integration voi luoda tietokantoja tälle sivulle

## ✅ VALMIS!

Kun olet saanut tokenin ja antanut oikeudet, voit käyttää:

```python
from src.notion_mcp_integration import NotionMCPIntegration

integration = NotionMCPIntegration()
integration.initialize_notion_client("your_token_here")

# Luo tietokannat
parent_page_id = "your_notion_page_id"
databases = integration.create_roi_database_structure(parent_page_id)
```

## 🔒 TURVALLISUUS

⚠️ **ÄLÄ JAA TOKENIA JULKISESTI!**
- Älä commitoi tokenia Git-repositorioon
- Käytä `.gitignore`-tiedostoa
- Käytä environment variableja

## 📞 ONGELMATILANTEET

### **"Unauthorized" -virhe**
- Tarkista että token on oikein
- Varmista että olet antanut oikeudet integrationille

### **"Page not found" -virhe**
- Tarkista että parent_page_id on oikein
- Varmista että integrationilla on oikeudet sivulle

### **"Rate limit exceeded"**
- Odota hetki ja yritä uudelleen
- Notion API:lla on rate limiting

---

**🔑 Token haettu? Seuraavaksi: `python setup_notion_mcp.py`**

