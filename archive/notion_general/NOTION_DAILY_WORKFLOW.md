# 📅 NOTION ROI SYSTEM - PÄIVITTÄINEN WORKFLOW

**Tavoite:** Maksimoi ROI päivittäisellä systemaattisella prosessilla

---

## ⏰ AAMU (06:00-08:00) - Analyysi & Suunnittelu

### 1. Tarkista Seuraavat Ottelut (15 min)

**Dashboard:** `Dashboard - Seuraavat vedot`

1. **Avaa Notion** → `Jalkapallo ROI System`
2. **Avaa:** `Dashboard - Seuraavat vedot`
3. **Tarkista:**
   - Onko pending-vetoja tänään?
   - Mitkä ottelut alkavat seuraavan 24h sisällä?
   - Onko kerroinmuutoksia?

### 2. Analysoi Uudet Ottelut (30-45 min)

**Database:** `Jalkapallo - Ottelut` → `Jalkapallo - Analytiikka`

**Prosessi jokaiselle ottelulle:**

1. **Avaa:** `Jalkapallo - Ottelut`
2. **Suodata:** Status = `Scheduled`, Date & Time = Seuraavat 7 päivää
3. **Jokaiselle ottelulle:**

**Vaihe A: Kerää Data**
- xG-arviot (SofaScore, Understat, FBref)
- H2H-historia (viimeiset 5 kohtaamista)
- Nykyinen muoto (viimeiset 5 ottelua)
- Loukkaantumiset (Transfermarkt, joukkueiden sivut)

**Vaihe B: Täytä Analytiikka**

Avaa `Jalkapallo - Analytiikka` → Luo uusi entry:

| Kenttä | Mistä haetaan | Esimerkki |
|--------|---------------|-----------|
| **Ottelu** | Linkitä otteluun | Manchester City vs Liverpool |
| **H2H voitto %** | Laske historiasta | 45% (3/5 voittoa kotona) |
| **Form Edge %** | Vertaa muotoa | +12% (City: W-W-W-D-W vs Liverpool: W-W-L-W-W) |
| **Injury Impact** | Arvioi loukkaantumiset | 0 (ei key players loukkaantuneena) |
| **Oma probability %** | Oma arvio | 58% |
| **Markkina probability %** | Lasketaan kertoimista | 52% (1/1.92 = 52%) |
| **Paras bet-tyyppi** | Valitse | OU2.5 |
| **Perustelut** | Kirjoita | xG-ero merkittävä (+33%), molemmilla vahva hyökkäys |

**Vaihe C: Tarkista Automaattiset Laskelmat**

Notion laskee automaattisesti:
- ✅ xG Koti, xG Vieras (haetaan Ottelusta)
- ✅ xG Edge % (koti-etu)
- ✅ Composite Edge % (yhdistetty edge)
- ✅ Edge % (market vs own probability)
- ✅ Min kerroin (tarve)
- ✅ Value-lippu (✅ PLAY / ⏸️ WAIT / ❌ SKIP)

**Vaihe D: Päätös**

Jos **Value-lippu = ✅ PLAY** ja **Edge % > 4%**:
- → Siirry luomaan veto (ks. kohta 3)

Jos **Value-lippu = ⏸️ WAIT**:
- → Seuraa kerroinmuutoksia päivällä

Jos **Value-lippu = ❌ SKIP**:
- → Älä pelaa, ei edgeä

### 3. Luo Vedot (15-30 min)

**Database:** `Jalkapallo - Vedot (Pre-Match)`

**Prosessi jokaiselle PLAY-analyysille:**

1. **Avaa:** `Jalkapallo - Vedot (Pre-Match)`
2. **Luo uusi entry:**

| Kenttä | Arvo | Mistä |
|--------|------|-------|
| **Analytiikka** | Linkitä analyysiin | Manchester City vs Liverpool |
| **Strategia** | Valitse strategia | Form Edge OU2.5 |
| **Veto-tyyppi** | Kopioi analyysistä | OU2.5 |
| **Oma probability %** | Kopioi analyysistä | 58% |
| **Kerroin (desimal)** | Hae bookmakerista | 1.92 |
| **Bankroll nykyinen** | Päivitä viikottain | 5000€ |

**Notion laskee automaattisesti:**
- ✅ Edge % ≈ +15%
- ✅ Kelly % ≈ 7.8%
- ✅ Scaled Kelly % ≈ 3.9%
- ✅ **Panos (€) ≈ 195€** ← TÄMÄ ON SUOSITUS!
- ✅ Potentiaalinen voitto ≈ 179€

3. **Tarkista Kelly-suositus:**
   - Jos Panos näyttää liian suurelta → Vähennä Scaled Kelly % (esim. 25% tai 50%)
   - Jos Panos näyttää liian pieneltä → Lisää Scaled Kelly % (esim. 75%)

4. **Sijoita veto:**
   - Avaa bookmaker (Pinnacle, Bet365, jne.)
   - Sijoita veto suositellulla panoksella
   - Kopioi bet slip URL
   - Päivitä Notionissa:
     - `Sijoitettu?` = ✅
     - `Kirjauspalvelu` = Pinnacle
     - `Bet slip URL` = [liitä linkki]
     - `Kellonaika sijoitettu` = [nykyinen aika]

### 4. Aamun Yhteenveto (5 min)

**Dashboard:** `Dashboard - Seuraavat vedot`

- Tarkista: Montako vetoa sijoitettu?
- Tarkista: Kokonaisriski (SUM Panos €)?
- Tarkista: Potentiaalinen voitto (SUM Potentiaalinen voitto €)?

**Esimerkki:**
- 3 vetoa sijoitettu
- Kokonaisriski: 450€
- Potentiaalinen voitto: 520€
- Keskimääräinen kerroin: 2.15

✅ **Aamu valmis!** Ottelut analysoitu, vedot sijoitettu.

---

## 🌞 PÄIVÄ (12:00-14:00) - Seuranta & Optimointi

### 1. Kerroinmuutosten Seuranta (15 min)

**Tavoite:** Löytää parempia kertoimia tai layer bets

**Prosessi:**

1. **Avaa:** `Dashboard - Seuraavat vedot`
2. **Jokaiselle pending-vedolle:**
   - Tarkista nykyinen kerroin bookmakerissa
   - Vertaa alkuperäiseen kertoimeen

**Jos kerroin on PARANTUNUT (+5% tai enemmän):**
- **Esim:** Alkuperäinen 1.92 → Nykyinen 2.05
- **Toimenpide:** Sijoita LAYER BET
  - 50% alkuperäisestä panoksesta
  - Samalla vedolla, paremmalla kertoimella
  - Luo uusi entry Vedot-databaseen

**Jos kerroin on HUONONTUNUT (-5% tai enemmän):**
- **Esim:** Alkuperäinen 1.92 → Nykyinen 1.80
- **Toimenpide:** HOLD (älä tee mitään)
  - Alkuperäinen edge on edelleen hyvä
  - Älä sijoita lisää

### 2. Live-Otteluiden Seuranta (30 min)

**Database:** `Jalkapallo - Ottelut` (Status = Live)

**Prosessi:**

1. **Suodata:** Status = `Live`
2. **Seuraa live-tilannetta:**
   - SofaScore live-tracker
   - Onko yllätyksiä?
   - Onko live-vetoja?

**Live-veto-kriteerit:**
- Oma live-analyysi antaa Edge > 6%
- Ottelu on alle 60 min pelattu
- Ei suuria loukkaantumisia kesken ottelun

**Jos live-veto:**
- Luo uusi entry `Jalkapallo - Vedot (Pre-Match)` (tai luo erillinen Live-database)
- Merkitse: Veto-tyyppi = [Live-veto]
- Sijoita nopeasti (kertoimet muuttuvat!)

### 3. Uudet Ottelut (15 min)

**Tavoite:** Tarkista onko uusia otteluita ilmestynyt

**Prosessi:**

1. **Aja Python-skripti:**
   ```bash
   python highest_roi_system.py
   ```
2. **Skripti hakee automaattisesti:**
   - Uudet ottelut seuraavalle 7 päivälle
   - Synkronoi Notioniin
   - Laskee xG-arviot

3. **Tarkista Notionissa:**
   - Onko uusia otteluita ilmestynyt?
   - Analysoi ne (ks. Aamu-prosessi)

✅ **Päivä valmis!** Kertoimet seurattu, live-tilanteet tarkistettu.

---

## 🌙 ILTA (20:00-21:00) - Tulokset & Raportointi

### 1. Päivitä Ottelutulokset (15 min)

**Database:** `Jalkapallo - Ottelut`

**Prosessi:**

1. **Suodata:** Status = `Live` tai ottelut jotka päättyivät tänään
2. **Jokaiselle ottelulle:**
   - Hae lopputulos (SofaScore, Flashscore)
   - Päivitä:
     - `Status` = `Finished`
     - `Koti maalit` = [tulos]
     - `Vieras maalit` = [tulos]

**Esimerkki:**
- Manchester City vs Liverpool
- Status: Finished
- Koti maalit: 3
- Vieras maalit: 2

### 2. Päivitä Vetojen Tulokset (15 min)

**Database:** `Jalkapallo - Vedot (Pre-Match)`

**Prosessi:**

1. **Avaa:** `Dashboard - Seuraavat vedot`
2. **Jokaiselle vedolle jonka ottelu on päättynyt:**
   - Tarkista: Voittiko veto?
   - Päivitä:
     - `Tulos` = `Won` / `Lost` / `Void`

**Notion laskee automaattisesti:**
- ✅ Toteutunut voitto/tappio (€)
- ✅ ROI %

**Esimerkki:**
- Veto: Manchester City OU2.5 @ 1.92
- Tulos: 3-2 (5 maalia) → **Won**
- Panos: 195€
- Toteutunut voitto: +179€
- ROI: +91.8%

### 3. Tarkista Päivän ROI (10 min)

**Dashboard:** `Dashboard - ROI Yhteenveto`

**Prosessi:**

1. **Avaa:** `Dashboard - ROI Yhteenveto`
2. **Tarkista yhteenveto:**
   - Montako vetoa päättyi tänään?
   - Montako voittoa vs. häviöitä?
   - Päivän ROI %?
   - Päivän voitto/tappio (€)?

**Esimerkki:**
- 3 vetoa päättyi
- 2 voittoa, 1 häviö
- Win Rate: 66.7%
- Päivän ROI: +45%
- Päivän voitto: +280€

### 4. Strategioiden Tarkistus (10 min)

**Dashboard:** `Dashboard - Strategiat Performance`

**Prosessi:**

1. **Avaa:** `Dashboard - Strategiat Performance`
2. **Tarkista jokainen strategia:**
   - Win Rate %?
   - Kokonais ROI %?
   - Alert-status?

**Jos Alert = "⚠️ Palauta, WR alle 48%":**
- → Tutki miksi strategia ei toimi
- → Päivitä kriteerejä
- → Harkitse Status = `Paused`

**Jos Alert = "❌ Poistetaan, negatiivinen ROI":**
- → Status = `Retired`
- → Älä käytä enää

**Jos Alert = "✅ OK":**
- → Jatka käyttöä
- → Harkitse panoksen nostoa (Kelly % → 75%)

### 5. Illan Yhteenveto (5 min)

**Kirjoita päiväkirjaan:**

```
📅 PÄIVÄN YHTEENVETO - [Päivämäärä]

🎯 VEDOT:
- Sijoitettu: 3 vetoa
- Päättynyt: 3 vetoa
- Voitot: 2 / Häviöt: 1
- Win Rate: 66.7%

💰 TALOUS:
- Kokonaisriski: 450€
- Päivän voitto: +280€
- Päivän ROI: +45%

📊 STRATEGIAT:
- Form Edge OU2.5: 2 voittoa / 0 häviöitä (ROI +92%)
- H2H Value 1X2: 0 voittoa / 1 häviö (ROI -100%)

🔍 OPPIMINEN:
- Form Edge OU2.5 toimii erinomaisesti
- H2H Value 1X2 tarvitsee tarkistusta (liian korkeat kertoimet?)

📝 HUOMIOT:
- Manchester City - Liverpool oli erinomainen veto (Edge +15%, ROI +91%)
- Barcelona - Real Madrid häviö, mutta edge oli oikea (bad beat)
```

✅ **Ilta valmis!** Tulokset päivitetty, ROI tarkistettu.

---

## 📅 VIIKONLOPPU (Sunnuntai 18:00) - Viikkoanalyysi

### 1. Viikon Yhteenveto (30 min)

**Dashboard:** `Dashboard - ROI Yhteenveto`

**Prosessi:**

1. **Suodata:** Päivämäärä sijoitettu = Tämä viikko
2. **Laske:**
   - Viikon vedot yhteensä
   - Viikon voitot / häviöt
   - Viikon Win Rate %
   - Viikon ROI %
   - Viikon voitto/tappio (€)

**Esimerkki:**
```
📊 VIIKON YHTEENVETO - Viikko 50 (2025)

🎯 VEDOT:
- Yhteensä: 18 vetoa
- Voitot: 11 / Häviöt: 7
- Win Rate: 61.1%

💰 TALOUS:
- Kokonaisriski: 2,850€
- Viikon voitto: +485€
- Viikon ROI: +17%

📈 PARHAAT VEDOT:
1. Bayern München OU2.5 @ 2.10 → ROI +110%
2. Manchester City 1X2 @ 1.85 → ROI +85%
3. Barcelona BTTS @ 1.95 → ROI +95%

📉 HUONOIMMAT VEDOT:
1. PSG 1X2 @ 1.60 → ROI -100% (häviö)
2. Liverpool AH @ 1.90 → ROI -100% (häviö)
```

### 2. Strategioiden Analyysi (30 min)

**Dashboard:** `Dashboard - Strategiat Performance`

**Prosessi:**

1. **Avaa:** `Dashboard - Strategiat Performance`
2. **Jokaiselle strategialle:**

**Esimerkki: Form Edge OU2.5**
```
📊 STRATEGIA: Form Edge OU2.5

📈 PERFORMANCE:
- Vedot yhteensä: 8
- Voitot: 6 / Häviöt: 2
- Win Rate: 75%
- Kokonais ROI: +42%
- Kerroin avg: 1.95

✅ ANALYYSI:
- Strategia toimii erinomaisesti
- Win Rate yli 70% → jatka käyttöä
- Harkitse panoksen nostoa (Kelly 50% → 75%)

🔍 OPPIMINEN:
- Parhaat vedot: Huippujoukkueet kotona (xG > 2.5)
- Huonoimmat vedot: Tasaiset ottelut (xG diff < 0.3)
```

**Esimerkki: H2H Value 1X2**
```
📊 STRATEGIA: H2H Value 1X2

📈 PERFORMANCE:
- Vedot yhteensä: 5
- Voitot: 2 / Häviöt: 3
- Win Rate: 40%
- Kokonais ROI: -15%
- Kerroin avg: 2.45

⚠️ ANALYYSI:
- Strategia ei toimi (Win Rate < 48%)
- Alert: "⚠️ Palauta, WR alle 48%"
- Toimenpide: Status = Paused

🔍 OPPIMINEN:
- Liian korkeat kertoimet (avg 2.45)
- H2H-data ei riittävä (tarvitaan enemmän historiaa)
- Korjaus: Max kerroin 2.20 → 2.00
```

### 3. Bankroll-Päivitys (10 min)

**Prosessi:**

1. **Laske uusi bankroll:**
   - Alkuperäinen bankroll: 5,000€
   - Viikon voitto: +485€
   - **Uusi bankroll: 5,485€**

2. **Päivitä KAIKKI pending-vedot:**
   - Avaa: `Jalkapallo - Vedot (Pre-Match)`
   - Suodata: Tulos = `Pending`
   - Päivitä jokaisessa: `Bankroll nykyinen` = 5,485€
   - **Panos (€) päivittyy automaattisesti!**

### 4. Viikon Oppiminen (20 min)

**Kirjoita viikkoraportti:**

```markdown
# 📊 VIIKKORAPORTTI - Viikko 50 (2025)

## 🎯 TAVOITTEET
- ✅ Viikko-ROI > 10% (saavutettu: +17%)
- ✅ Win Rate > 55% (saavutettu: 61%)
- ✅ Vähintään 15 vetoa (saavutettu: 18)

## 💰 TALOUS
- Alkuperäinen bankroll: 5,000€
- Viikon voitto: +485€
- Uusi bankroll: 5,485€
- ROI: +17%

## 📈 PARHAAT STRATEGIAT
1. Form Edge OU2.5 (ROI +42%, WR 75%)
2. Statistical BTTS (ROI +28%, WR 67%)

## 📉 HUONOIMMAT STRATEGIAT
1. H2H Value 1X2 (ROI -15%, WR 40%) → PAUSED

## 🔍 OPPIMINEN
- Form Edge OU2.5 toimii parhaiten huippujoukkueilla
- BTTS-vedot toimivat hyvin kun molempien xG > 1.8
- 1X2-vedot vaativat enemmän dataa (H2H ei riitä)

## 📝 TOIMENPITEET ENSI VIIKOLLE
1. Nosta Form Edge OU2.5 Kelly % → 75%
2. Pause H2H Value 1X2, korjaa kriteerit
3. Testaa uutta strategiaa: "xG Differential AH"
4. Lisää bankroll 5,485€ → 6,000€ (talletus)
```

✅ **Viikonloppu valmis!** Viikko analysoitu, strategiat optimoitu.

---

## 🚀 KUUKAUSITTAINEN DEEP DIVE (Kuukauden loppu)

### 1. Kuukauden Yhteenveto (60 min)

**Prosessi:**

1. **Laske kuukauden metriikat:**
   - Vedot yhteensä
   - Win Rate %
   - Kuukauden ROI %
   - Sharpe ratio (Excel/Python)
   - Max drawdown %

2. **Strategioiden ranking:**
   - Järjestä strategiat ROI %:n mukaan
   - Poista negatiiviset (Status = Retired)
   - Nosta parhaat (Kelly % → 75-100%)

3. **Bankroll-optimointi:**
   - Laske optimaalinen Kelly-skaalaus
   - Testaa 25% vs 50% vs 75%
   - Valitse paras (Sharpe ratio maksimoi)

### 2. A/B-Testaus (30 min)

**Testaa uusia strategioita:**

1. Luo 2-3 uutta strategiaa
2. Status = `Testing`
3. Käytä pienempää Kelly % (25%)
4. Kerää dataa 2-4 viikkoa
5. Jos ROI > 10% ja WR > 55% → Status = `Active`

### 3. Dokumentointi (30 min)

**Päivitä dokumentaatio:**
- `NOTION_ROI_SYSTEM_GUIDE.md` (jos muutoksia)
- `NOTION_DAILY_WORKFLOW.md` (jos prosessi muuttuu)
- Lisää uusia strategioita

✅ **Kuukausi valmis!** Järjestelmä optimoitu, uudet strategiat testattu.

---

## 📊 KEY METRICS - Mitä Seurata

### Päivittäin
- ✅ Päivän ROI %
- ✅ Päivän voitto/tappio (€)
- ✅ Pending-vedot

### Viikoittain
- ✅ Viikon ROI %
- ✅ Win Rate %
- ✅ Strategioiden performance
- ✅ Bankroll-päivitys

### Kuukausittain
- ✅ Kuukauden ROI %
- ✅ Sharpe ratio
- ✅ Max drawdown %
- ✅ Kelly-optimointi

---

## 🎯 SUCCESS CRITERIA

**Hyvä viikko:**
- ROI > 10%
- Win Rate > 55%
- Ei suuria drawdowneja (< 10%)

**Erinomainen viikko:**
- ROI > 15%
- Win Rate > 60%
- Kaikki strategiat positiivisia

**Huono viikko:**
- ROI < 0%
- Win Rate < 50%
- → Pause kaikki strategiat, analysoi

---

## 🚨 TROUBLESHOOTING

### "Strategia ei toimi (WR < 48%)"
**Ratkaisu:**
1. Status = `Paused`
2. Analysoi häviöt: Mikä meni pieleen?
3. Päivitä kriteerit
4. Testaa uudelleen pienemmällä Kelly %

### "Liian suuri drawdown (> 20%)"
**Ratkaisu:**
1. Vähennä Kelly % (50% → 25%)
2. Pause huonoimmat strategiat
3. Keskity parhaimpiin strategioihin
4. Odota recovery

### "Bankroll loppuu"
**Ratkaisu:**
1. **STOP!** Älä pelaa enää
2. Analysoi kaikki vedot
3. Mikä meni pieleen?
4. Aloita alusta pienemmällä bankrollilla
5. Käytä 25% Kelly %

---

## 🎓 PRO TIPS

1. **Kelly-skaalaus:**
   - Aloita 25% Kellyllä (konservatiivinen)
   - Kun Win Rate > 60% → nosta 50%
   - Kun Win Rate > 65% → nosta 75%

2. **Strategioiden diversifiointi:**
   - Älä käytä vain yhtä strategiaa
   - Vähintään 3-5 eri strategiaa
   - Eri bet-tyypit (1X2, OU2.5, BTTS)

3. **Bookmaker-valinta:**
   - Pinnacle = parhaat kertoimet
   - Bet365 = hyvä live-betting
   - 1xBet = laaja valikoima

4. **Dokumentointi:**
   - Kirjoita AINA perustelut
   - Analysoi häviöt (mikä meni pieleen?)
   - Opi virheistä

5. **Tauot:**
   - Älä pelaa joka päivä
   - Ota taukoja (1-2 päivää/viikko)
   - Vältä tilt-peliä

---

## ✅ CHECKLIST - Päivittäinen

```
AAMU:
[ ] Tarkista seuraavat ottelut
[ ] Analysoi uudet ottelut (xG, H2H, Form)
[ ] Täytä Analytiikka-database
[ ] Luo vedot (jos Edge > 4%)
[ ] Sijoita vedot bookmakeriin

PÄIVÄ:
[ ] Seuraa kerroinmuutoksia
[ ] Tarkista live-ottelut
[ ] Aja Python-skripti (uudet ottelut)

ILTA:
[ ] Päivitä ottelutulokset
[ ] Päivitä vetojen tulokset
[ ] Tarkista päivän ROI
[ ] Tarkista strategioiden Alert
[ ] Kirjoita päiväkirja

VIIKONLOPPU:
[ ] Laske viikon ROI
[ ] Analysoi strategiat
[ ] Päivitä bankroll
[ ] Kirjoita viikkoraportti
```

---

**🚀 Onnea systemaattiseen vedonlyöntiin! 💰**

