# 🎾 TENNIS RELATIONAL DATABASE - TÄYDELLINEN OPI

## 📊 RELAATIOMALLI

### **4 PERUSTAULUA:**

1. **👤 Players** - Pelaajatiedot
2. **🏆 Tournaments** - Turnaustiedot
3. **📅 Events** - Tapahtumat/kierrokset
4. **🎾 Matches** - Ottelutiedot

### **11 TILASTOTAULUA:**

1. **📊 Player Stats** - Pelaajien perustilastot
2. **🏟️ Surface Stats** - Kenttäspesifiset tilastot
3. **🎯 Serve Stats** - Syöttötilastot
4. **🔄 Return Stats** - Vastaanottotilastot
5. **⭐ Quality Stats** - Pelinlaadut
6. **⚔️ H2H Stats** - Head-to-head tilastot
7. **📈 Ratings** - ELO ja muut luokitukset
8. **💰 Odds** - Kertoimet
9. **💎 ROI Analysis** - ROI-analyysi
10. **🌤️ Environment** - Ympäristötekijät
11. **🏥 Health** - Terveys- ja vammatiedot

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
- Match (Relation) - Useimmissa tilastotauluissa

### **Statistics → Players**
- Player (Relation) - Useimmissa tilastotauluissa

---

## 🚀 AUTOMAATTINEN LUONTI

### **Vaihtoehto 1: Yksi Surface Stats -taulu (Suositeltu)**

```bash
python create_tennis_relational_db.py \
  --token YOUR_TOKEN \
  --page-id YOUR_PAGE_ID \
  --surface-option 1
```

**Etut:**
- ✅ Yksinkertaisempi ylläpito
- ✅ Helpompi suodatus
- ✅ Vähemmän tauluja

### **Vaihtoehto 2: Kolme erillistä Surface Stats -taulua**

```bash
python create_tennis_relational_db.py \
  --token YOUR_TOKEN \
  --page-id YOUR_PAGE_ID \
  --surface-option 2
```

**Etut:**
- ✅ Eri suodattimet kullekin kenttätyypille
- ✅ Selkeämpi rakenne

---

## 📋 KAIKKI KENTÄT

### **👤 Players (15 kenttää)**
- Name, ATP/WTA, Ranking, Ranking Points
- Career High Ranking, Age, Country
- Prize Money (Career/Season)
- Wins/Losses (Career/Season)
- Win % (Career/Season)
- Current Streak, Last Updated

### **🏆 Tournaments (11 kenttää)**
- Name, Type, Surface, Location, Country
- Start Date, End Date, Prize Money, Points
- Players Count, Defending Champion

### **📅 Events (7 kenttää)**
- Name, Tournament, Round, Date, Status
- Surface, Venue

### **🎾 Matches (12 kenttää)**
- Match, Player 1, Player 2, Event, Tournament
- Date, Status, Surface, Score
- Sets Score, Games Score, Duration

### **📊 Player Stats (6 kenttää)**
- Player, Season, Matches Played
- Wins, Losses, Win %, Last Updated

### **🏟️ Surface Stats (Option 1: 12 kenttää)**
- Player, Surface
- Hard Wins/Losses/Win %
- Clay Wins/Losses/Win %
- Grass Wins/Losses/Win %
- Last Updated

### **🎯 Serve Stats (12 kenttää)**
- Player, Match, Serve %, First/Second Serve %
- First/Second Serve Points Won %
- Service Games Won %, Aces, Double Faults
- Break Points Saved %, Break Points Faced
- Last Updated

### **🔄 Return Stats (8 kenttää)**
- Player, Match, Return Games Won %
- Return Points Won %, Break Points Converted %
- Break Points Opportunities
- Return Points Won vs First/Second Serve %
- Last Updated

### **⭐ Quality Stats (8 kenttää)**
- Player, Match, Winners, Unforced Errors
- Forced Errors, Winners to Errors Ratio
- Net Points Won %, Net Points Played
- Last Updated

### **⚔️ H2H Stats (12 kenttää)**
- Player 1, Player 2, Total Matches
- Player 1/2 Wins, Player 1 Win %
- Last Meeting Date/Result
- Hard/Clay/Grass H2H, Recent Form
- Last Updated

### **📈 Ratings (7 kenttää)**
- Player, Match, ELO Rating, ELO Change
- TrueSkill Rating, Expected Win Probability %
- Statistical Edge %, Last Updated

### **💰 Odds (9 kenttää)**
- Match, Player, Odds, Best Odds
- Bookmaker, Odds Movement
- Market Margin %, Implied Probability %
- Last Updated

### **💎 ROI Analysis (15 kenttää)**
- Match, Player, True/Market Probability %
- Edge %, Expected Value %, Recommended Stake €
- Kelly %, ROI %, Confidence, Risk Score
- Result, Profit/Loss €, Last Updated

### **🌤️ Environment (10 kenttää)**
- Match, Weather, Temperature °C
- Humidity %, Wind Speed km/h
- Precipitation mm, Court Speed
- Altitude m, Time Zone, Last Updated

### **🏥 Health (9 kenttää)**
- Player, Match, Injury Status
- Injuries, Recent Injuries, Rest Days
- Fatigue Level, Match Load (7 days)
- Last Updated

---

## 📊 NÄKYMÄT JA SUODATTIMET

### **Matches-näkymät:**
- **Table View** - Date desc (oletus)
- **Calendar View** - Date
- **Board View** - Status
- **Timeline View** - Date

### **Tournaments-näkymät:**
- **Calendar View** - Start Date (oletus)
- **Table View** - Type
- **Gallery View** - Name

### **Players-näkymät:**
- **Table View** - Ranking asc (oletus)
- **Table View** - Points desc
- **Table View** - Age asc

### **H2H-näkymät:**
- **List View** - Player 1 (oletus)
- **Table View** - Total Matches desc

### **Odds & ROI-näkymät:**
- **Board View** - Confidence (oletus)
- **Table View** - ROI % desc
- **Table View** - Edge % desc

---

## ✅ YHTEENVETO

**LUODAAN AUTOMAATTISESTI:**

✅ **4 perustaulua** - Players, Tournaments, Events, Matches  
✅ **11 tilastotaulua** - Kaikki tilastot  
✅ **Relaatiot** - Taulujen väliset linkit  
✅ **100+ kenttää** - Kaikki tilastot  
✅ **Näkymät** - Valmiit suodattimet  

**🎾 Valmis käyttöön heti kun luotu! 💰**







