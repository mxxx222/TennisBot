# 🚀 QUICK START - TENNIS RELATIONAL DATABASE

## ⚡ NOPEA KÄYTTÖÖNOTTO (5 MINUUTTIA)

### **VAIHE 1: Valmistaudu**

```bash
# 1. Asenna riippuvuudet
pip install notion-client

# 2. Hae token ja page ID
# Token: https://www.notion.so/my-integrations
# Page ID: Notion-sivun URL:sta
```

---

### **VAIHE 2: Suorita Luonti**

```bash
# Suorita skripti Option 1:lla (yksi Surface Stats -taulu)
python create_tennis_relational_db.py \
  --token YOUR_TOKEN \
  --page-id YOUR_PAGE_ID \
  --surface-option 1
```

**Tämä luo automaattisesti:**
- ✅ 4 perustaulua (Players, Tournaments, Events, Matches)
- ✅ 11 tilastotaulua (kaikki tilastot)
- ✅ Relaatiot taulujen välille
- ✅ 100+ kenttää

---

### **VAIHE 3: Täytä CSV-pohjat**

```bash
# CSV-pohjat ovat valmiina
ls data/csv_templates/

# Täytä templatet datallasi
# Pidä ID-arvot yhdenmukaisina relaatiokentille
```

**Tärkeää:**
- Pidä Player-nimet yhdenmukaisina kaikissa tauluissa
- Käytä samoja Tournament-nimiä
- Match-nimet täsmäävät Events-tauluun

---

### **VAIHE 4: Tuo CSV Notioniin**

1. **Avaa Notion-tietokanta**
2. **Klikkaa "..." → "Import"**
3. **Valitse CSV-tiedosto**
4. **Varmista että kentät mäppäävät oikein**
5. **Klikkaa "Import"**

**Järjestys:**
1. Players (ensin)
2. Tournaments
3. Events
4. Matches
5. Loput tilastotaulut

---

### **VAIHE 5: Lisää Kaavat**

1. **Avaa** `tennis_db_formulas.md`
2. **Kopioi kaava** (esim. Edge)
3. **Notionissa:** Lisää Formula-kenttä
4. **Liitä kaava** ja korvaa `prop("Field Name")` oikeilla kenttänimillä

**Tärkeimmät kaavat:**
- Edge = True Probability - Market Probability
- Expected Value = (True Probability × Odds) - 1
- Kelly % = (True Probability × Odds - 1) / (Odds - 1)
- ROI = Expected Value × Confidence Factor

---

### **VAIHE 6: Luo Data Quality -näkymät**

1. **Avaa** `tennis_db_data_quality.md`
2. **Luo uusi näkymä** Notioniin
3. **Lisää filterit** dokumentin mukaan
4. **Tallenna näkymä**

**Tärkeimmät näkymät:**
- Missing Required Fields
- Orphan Relations
- Data Inconsistencies
- Low Quality Data

---

## 📊 MITÄ LUODAAN

### **Perustaulut (4):**
1. 👤 **Players** - 15 kenttää
2. 🏆 **Tournaments** - 11 kenttää
3. 📅 **Events** - 7 kenttää
4. 🎾 **Matches** - 12 kenttää

### **Tilastotaulut (11):**
5. 📊 **Player Stats** - 6 kenttää
6. 🏟️ **Surface Stats** - 12 kenttää (Option 1: Unified)
7. 🎯 **Serve Stats** - 12 kenttää
8. 🔄 **Return Stats** - 8 kenttää
9. ⭐ **Quality Stats** - 8 kenttää
10. ⚔️ **H2H Stats** - 12 kenttää
11. 📈 **Ratings** - 7 kenttää
12. 💰 **Odds** - 9 kenttää
13. 💎 **ROI Analysis** - 15 kenttää
14. 🌤️ **Environment** - 10 kenttää
15. 🏥 **Health** - 9 kenttää

**YHTEENSÄ: 15 taulua, 100+ kenttää**

---

## 🔗 RELAATIOT

### **Matches → Players**
- Player 1 (Relation)
- Player 2 (Relation)

### **Matches → Events**
- Event (Relation)

### **Matches → Tournaments**
- Tournament (Relation)

### **Statistics → Matches**
- Match (Relation)

### **Statistics → Players**
- Player (Relation)

---

## ✅ VALMIS!

Kun olet suorittanut kaikki vaiheet:

1. ✅ Tietokannat luotu Notioniin
2. ✅ CSV-data tuotu
3. ✅ Kaavat lisätty
4. ✅ Data Quality -näkymät luotu

**🎾 Tennis-relaatiomalli on valmis käyttöön! 💰**

---

## 📞 TROUBLESHOOTING

### **"Unauthorized" -virhe**
- ✅ Tarkista että token on oikein
- ✅ Varmista että integration on linkitetty sivulle

### **"Page not found" -virhe**
- ✅ Tarkista että page ID on oikein
- ✅ Varmista että integrationilla on oikeudet sivulle

### **Relaatiot eivät toimi**
- ✅ Varmista että CSV-tuonnissa käytit samoja nimiä
- ✅ Linkitä relaatiot manuaalisesti Notionissa

### **Kaavat eivät toimi**
- ✅ Tarkista että kenttänimet ovat oikein
- ✅ Varmista että kaava-syntaksi on oikein

---

## 🎯 SEURAAVAT ASKELEET

1. **Suorita luonti:** `python create_tennis_relational_db.py --token YOUR_TOKEN --page-id YOUR_PAGE_ID --surface-option 1`
2. **Täytä CSV-pohjat** datallasi
3. **Tuo CSV Notioniin**
4. **Lisää kaavat** Formula-kenttiin
5. **Luo Data Quality -näkymät**

**🚀 Valmis käyttöön!**







