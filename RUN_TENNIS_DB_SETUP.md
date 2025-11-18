# 🚀 RUN TENNIS RELATIONAL DATABASE SETUP

## ⚡ NOPEA KÄYTTÖÖNOTTO

### **VAIHE 1: Hae Token ja Page ID**

```bash
# 1. Token: https://www.notion.so/my-integrations
#    - Klikkaa integration → Kopioi "Internal Integration Token"

# 2. Page ID: Notion-sivun URL:sta
#    - URL: notion.so/[workspace]/[page-id]
#    - Kopioi vain [page-id] osa (32 merkkiä)
```

---

### **VAIHE 2: Suorita Luonti**

```bash
python create_tennis_relational_db.py \
  --token YOUR_TOKEN \
  --page-id YOUR_PAGE_ID \
  --surface-option 1
```

**Odotettu tulos:**
```
🎾 Tennis Relational Database Creator initialized

🏗️ Creating Tennis Relational Database Structure...
============================================================

📊 Creating Base Tables...
   ✅ Players: abc123...
   ✅ Tournaments: def456...
   ✅ Events: ghi789...
   ✅ Matches: jkl012...

📈 Creating Statistics Tables...
   ✅ Player Stats: mno345...
   ✅ Surface Stats: pqr678...
   ✅ Serve Stats: stu901...
   ... (kaikki 11 taulua)

✅ Created 15 databases
💾 Config saved to config/tennis_relational_db.json
```

---

### **VAIHE 3: Validoi Luonti**

```bash
python validate_tennis_db.py \
  --token YOUR_TOKEN \
  --config config/tennis_relational_db.json
```

**Odotettu tulos:**
```
✅ ALL VALIDATIONS PASSED!
   Databases Found: 15/15
   Databases Valid: 15
   Relations Valid: 20+
   Total Issues: 0
```

---

### **VAIHE 4: Smoke Test (5 min)**

#### **1. Players - Lisää 2 pelaajaa**

Notionissa:
- Avaa "👤 Players" -tietokanta
- Lisää uusi rivi:
  - Name: "Novak Djokovic"
  - ATP/WTA: "ATP"
  - Ranking: 1
  - Country: "Serbia"
- Lisää toinen:
  - Name: "Carlos Alcaraz"
  - ATP/WTA: "ATP"
  - Ranking: 2
  - Country: "Spain"

**Tarkista:** Pelaajat näkyvät Matches-taulussa relaationa

---

#### **2. Tournaments - Lisää turnaus + Event**

Notionissa:
- Avaa "🏆 Tournaments" -tietokanta
- Lisää uusi rivi:
  - Name: "Wimbledon 2025"
  - Type: "Grand Slam"
  - Surface: "Grass"
  - Start Date: 2025-06-23
  - End Date: 2025-07-06

- Avaa "📅 Events" -tietokanta
- Lisää uusi rivi:
  - Name: "Wimbledon 2025 - Men's Singles"
  - Tournament: [Linkki Wimbledon 2025]
  - Round: "Final"
  - Date: 2025-07-06

**Tarkista:** Event näkyy Matches-taulussa relaationa

---

#### **3. Matches - Täytä Score ja Status**

Notionissa:
- Avaa "🎾 Matches" -tietokanta
- Lisää uusi rivi:
  - Match: "Djokovic vs Alcaraz"
  - Player 1: [Linkki Novak Djokovic]
  - Player 2: [Linkki Carlos Alcaraz]
  - Event: [Linkki Wimbledon 2025 - Men's Singles]
  - Tournament: [Linkki Wimbledon 2025]
  - Date: 2025-07-06
  - Status: "Finished"
  - Score: "6-4, 6-2"
  - Surface: "Grass"

**Tarkista:** Data Quality -näkymässä "Score Validation" on puhdas

---

#### **4. Odds + ROI - Syötä kertoimet**

Notionissa:
- Avaa "💰 Odds" -tietokanta
- Lisää 2 riviä:
  - Match: [Linkki Djokovic vs Alcaraz]
  - Player: "Player 1"
  - Odds: 1.85
  - Bookmaker: "Bet365"
  
  - Match: [Linkki Djokovic vs Alcaraz]
  - Player: "Player 2"
  - Odds: 2.10
  - Bookmaker: "Bet365"

- Avaa "💎 ROI Analysis" -tietokanta
- Lisää rivi:
  - Match: [Linkki Djokovic vs Alcaraz]
  - Player: "Player 1"
  - True Probability %: 0.65
  - Market Probability %: 0.541
  - Odds: 1.85
  - Recommended Stake €: 25.50

**Tarkista:** Kaavat tuottavat:
- Edge % = 0.65 - 0.541 = 0.109 (10.9%)
- Expected Value % = (0.65 × 1.85) - 1 = 0.2025 (20.25%)
- Kelly % = (0.65 × 1.85 - 1) / (1.85 - 1) = 0.238 (23.8%)
- ROI % = 0.2025 × 1.0 = 0.2025 (20.25%)

---

#### **5. H2H - Lisää Head-to-Head**

Notionissa:
- Avaa "⚔️ H2H Stats" -tietokanta
- Lisää rivi:
  - Player 1: [Linkki Novak Djokovic]
  - Player 2: [Linkki Carlos Alcaraz]
  - Total Matches: 5
  - Player 1 Wins: 3
  - Player 2 Wins: 2
  - Player 1 Win %: 0.60
  - Last Meeting Date: 2024-07-14
  - Last Meeting Result: "Djokovic 6-3, 6-4"

**Tarkista:** H2H List -näkymässä rivi näkyy oikein

---

## ✅ VALIDOINTI CHECKLIST

### **Tarkista että:**

- ✅ Kaikki 15 taulua on luotu
- ✅ Relaatiot toimivat (Player 1/2, Event, Tournament)
- ✅ Kaavat toimivat (Edge, EV, Kelly, ROI)
- ✅ Data Quality -näkymät löytävät ongelmat
- ✅ CSV-importti toimii
- ✅ Päivämäärät ISO-8601 -muodossa
- ✅ Prosentit numeroina (ei "%"-merkkiä)

---

## 📞 TROUBLESHOOTING

### **"Unauthorized" -virhe**
```bash
# Tarkista token
echo $NOTION_TOKEN

# Tarkista että integration on linkitetty sivulle
# Notion → Sivu → "..." → Connections → Lisää integration
```

### **"Page not found" -virhe**
```bash
# Tarkista page ID
# URL: notion.so/[workspace]/[page-id]
# Kopioi vain [page-id] osa
```

### **Relaatiot eivät toimi**
```bash
# Varmista että käytit samoja nimiä CSV-tuonnissa
# Linkitä relaatiot manuaalisesti Notionissa
```

### **Kaavat eivät toimi**
```bash
# Tarkista että kenttänimet ovat oikein
# Varmista että kaava-syntaksi on oikein
# Katso: tennis_db_formulas.md
```

---

## 🎯 SEURAAVAT ASKELEET

1. ✅ **Suorita luonti** - `python create_tennis_relational_db.py`
2. ✅ **Validoi** - `python validate_tennis_db.py`
3. ✅ **Smoke test** - Testaa kaikki 5 vaihetta
4. ✅ **Täytä CSV-pohjat** - Bulk-importti
5. ✅ **Lisää kaavat** - Formula-kentät
6. ✅ **Luo validointinäkymät** - Data Quality

**🚀 Valmis käyttöön!**






