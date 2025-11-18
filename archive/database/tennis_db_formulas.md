# 🧮 TENNIS DATABASE FORMULAS - TARKAT MÄÄREET

## 📊 ROI & KELLY CRITERION -KAAVAT

### **1. IMPLIED PROBABILITY (Markkinoiden todennäköisyys)**

```
Implied Probability = 1 / Odds

Esimerkki:
- Odds = 2.00 → Implied Probability = 1 / 2.00 = 0.50 (50%)
- Odds = 1.85 → Implied Probability = 1 / 1.85 = 0.541 (54.1%)
- Odds = 2.10 → Implied Probability = 1 / 2.10 = 0.476 (47.6%)
```

**Notion Formula:**
```javascript
1 / prop("Odds")
```

---

### **2. MARKET MARGIN (Markkinamarginaali)**

```
Market Margin = (1 / Odds_Player1 + 1 / Odds_Player2) - 1

Esimerkki:
- Odds Player 1 = 1.85
- Odds Player 2 = 2.10
- Market Margin = (1/1.85 + 1/2.10) - 1 = (0.541 + 0.476) - 1 = 0.017 (1.7%)
```

**Notion Formula:**
```javascript
(1 / prop("Odds Player 1") + 1 / prop("Odds Player 2")) - 1
```

---

### **3. TRUE PROBABILITY (Todellinen todennäköisyys)**

```
True Probability = ELO-based probability + H2H adjustment + Form adjustment + Surface adjustment

ELO Probability:
P(Player1 wins) = 1 / (1 + 10^((ELO_Player2 - ELO_Player1) / 400))

H2H Adjustment:
H2H_Weight = 0.15
H2H_Adjustment = (H2H_Win_Rate - 0.5) * H2H_Weight

Form Adjustment:
Form_Weight = 0.10
Form_Adjustment = (Recent_Win_Rate - 0.5) * Form_Weight

Surface Adjustment:
Surface_Weight = 0.20
Surface_Adjustment = (Surface_Win_Rate - Overall_Win_Rate) * Surface_Weight

True Probability = ELO_Probability + H2H_Adjustment + Form_Adjustment + Surface_Adjustment
```

**Notion Formula (simplified):**
```javascript
// ELO Probability
1 / (1 + pow(10, (prop("ELO Rating Player 2") - prop("ELO Rating Player 1")) / 400))
```

---

### **4. EDGE (Etu)**

```
Edge = True Probability - Market Probability

Esimerkki:
- True Probability = 0.65 (65%)
- Market Probability = 0.541 (54.1%)
- Edge = 0.65 - 0.541 = 0.109 (10.9%)
```

**Notion Formula:**
```javascript
prop("True Probability %") - prop("Market Probability %")
```

---

### **5. EXPECTED VALUE (EV) (Odotusarvo)**

```
Expected Value = (True Probability × Odds) - 1

Esimerkki:
- True Probability = 0.65
- Odds = 1.85
- EV = (0.65 × 1.85) - 1 = 1.2025 - 1 = 0.2025 (20.25%)
```

**Notion Formula:**
```javascript
(prop("True Probability %") * prop("Odds")) - 1
```

---

### **6. KELLY CRITERION (Optimaalinen panos)**

```
Kelly Percentage = (True Probability × Odds - 1) / (Odds - 1)

Conservative Kelly (25% fraction):
Recommended Stake = Bankroll × Kelly Percentage × 0.25

Esimerkki:
- True Probability = 0.65
- Odds = 1.85
- Bankroll = €1000
- Kelly % = (0.65 × 1.85 - 1) / (1.85 - 1) = 0.2025 / 0.85 = 0.238 (23.8%)
- Recommended Stake = €1000 × 0.238 × 0.25 = €59.50
```

**Notion Formula:**
```javascript
// Kelly Percentage
((prop("True Probability %") * prop("Odds")) - 1) / (prop("Odds") - 1)

// Recommended Stake (with 25% fraction)
prop("Bankroll") * prop("Kelly %") * 0.25
```

---

### **7. ROI (Return on Investment)**

```
ROI = Expected Value × Confidence Factor

Confidence Factor:
- High Confidence: 1.0
- Medium Confidence: 0.75
- Low Confidence: 0.50

Esimerkki:
- Expected Value = 0.2025 (20.25%)
- Confidence = High (1.0)
- ROI = 0.2025 × 1.0 = 0.2025 (20.25%)
```

**Notion Formula:**
```javascript
prop("Expected Value %") * if(prop("Confidence") == "High", 1.0, if(prop("Confidence") == "Medium", 0.75, 0.50))
```

---

### **8. RISK SCORE (Riskiscore)**

```
Risk Score = (1 - True Probability) × (1 / Odds) × Edge

Normalized to 0-1 scale:
Risk Score = Risk Score / Max_Possible_Risk

Esimerkki:
- True Probability = 0.65
- Odds = 1.85
- Edge = 0.109
- Risk Score = (1 - 0.65) × (1 / 1.85) × 0.109 = 0.35 × 0.541 × 0.109 = 0.021
```

**Notion Formula:**
```javascript
(1 - prop("True Probability %")) * (1 / prop("Odds")) * prop("Edge %")
```

---

### **9. PROFIT/LOSS (Voitto/Tappio)**

```
Profit/Loss = (Result × Stake × Odds) - Stake

Where:
- Result = 1 if Win, 0 if Loss
- Stake = Recommended Stake
- Odds = Odds at bet time

Esimerkki:
- Result = Win (1)
- Stake = €59.50
- Odds = 1.85
- Profit/Loss = (1 × €59.50 × 1.85) - €59.50 = €110.08 - €59.50 = €50.58
```

**Notion Formula:**
```javascript
if(prop("Result") == "Win", (prop("Recommended Stake €") * prop("Odds")) - prop("Recommended Stake €"), -prop("Recommended Stake €"))
```

---

### **10. WIN RATE (Voittoprosentti)**

```
Win Rate = (Wins / Total Trades) × 100

Esimerkki:
- Wins = 7
- Total Trades = 10
- Win Rate = (7 / 10) × 100 = 70%
```

**Notion Formula:**
```javascript
(prop("Wins") / prop("Total Trades")) * 100
```

---

### **11. SHARPE RATIO**

```
Sharpe Ratio = (Average ROI / Standard Deviation of ROI) × sqrt(Number of Trades)

Esimerkki:
- Average ROI = 0.15 (15%)
- Standard Deviation = 0.25 (25%)
- Number of Trades = 30
- Sharpe Ratio = (0.15 / 0.25) × sqrt(30) = 0.6 × 5.48 = 3.29
```

**Notion Formula:**
```javascript
(prop("Average ROI %") / prop("Std Dev ROI %")) * sqrt(prop("Total Trades"))
```

---

### **12. PROFIT FACTOR**

```
Profit Factor = Total Wins / Total Losses

Esimerkki:
- Total Wins = €500
- Total Losses = €300
- Profit Factor = €500 / €300 = 1.67
```

**Notion Formula:**
```javascript
prop("Total Wins €") / prop("Total Losses €")
```

---

### **13. MAX DRAWDOWN (Suurin tappio)**

```
Max Drawdown = Max((Peak Value - Current Value) / Peak Value)

Esimerkki:
- Peak Value = €1000
- Current Value = €750
- Max Drawdown = (€1000 - €750) / €1000 = 0.25 (25%)
```

**Notion Formula:**
```javascript
(prop("Peak Value €") - prop("Current Value €")) / prop("Peak Value €")
```

---

## 📊 SURFACE STATS -KAAVAT

### **Surface Win Rate**

```
Surface Win Rate = Surface Wins / (Surface Wins + Surface Losses)

Esimerkki:
- Hard Wins = 450
- Hard Losses = 85
- Hard Win Rate = 450 / (450 + 85) = 450 / 535 = 0.841 (84.1%)
```

**Notion Formula:**
```javascript
prop("Hard Wins") / (prop("Hard Wins") + prop("Hard Losses"))
```

---

## 📊 SERVE/RETURN STATS -KAAVAT

### **Service Games Won %**

```
Service Games Won % = Service Games Won / Service Games Played

Esimerkki:
- Service Games Won = 88
- Service Games Played = 100
- Service Games Won % = 88 / 100 = 0.88 (88%)
```

**Notion Formula:**
```javascript
prop("Service Games Won") / prop("Service Games Played")
```

### **Break Points Converted %**

```
Break Points Converted % = Break Points Converted / Break Points Opportunities

Esimerkki:
- Break Points Converted = 5
- Break Points Opportunities = 11
- Break Points Converted % = 5 / 11 = 0.455 (45.5%)
```

**Notion Formula:**
```javascript
prop("Break Points Converted") / prop("Break Points Opportunities")
```

---

## 📊 QUALITY STATS -KAAVAT

### **Winners to Errors Ratio**

```
Winners to Errors Ratio = Winners / (Unforced Errors + Forced Errors)

Esimerkki:
- Winners = 35
- Unforced Errors = 18
- Forced Errors = 12
- Ratio = 35 / (18 + 12) = 35 / 30 = 1.17
```

**Notion Formula:**
```javascript
prop("Winners") / (prop("Unforced Errors") + prop("Forced Errors"))
```

---

## ✅ NOTION IMPLEMENTATION

### **Kaavat Notionissa:**

1. **Lisää Formula-kenttä** tauluun
2. **Kopioi kaava** yllä olevista
3. **Korvaa prop("Field Name")** oikeilla kenttänimillä
4. **Testaa kaava** esimerkkidatalla

### **Esimerkki Notion Formula:**

```javascript
// Edge Calculation
prop("True Probability %") - prop("Market Probability %")

// Expected Value
(prop("True Probability %") * prop("Odds")) - 1

// Kelly Percentage
((prop("True Probability %") * prop("Odds")) - 1) / (prop("Odds") - 1)

// Recommended Stake (25% Kelly)
prop("Bankroll") * prop("Kelly %") * 0.25

// ROI
prop("Expected Value %") * if(prop("Confidence") == "High", 1.0, if(prop("Confidence") == "Medium", 0.75, 0.50))
```

---

## 🎯 YHTEENVETO

**KAIKKI KAAVAT VALMIINA:**

✅ **Implied Probability** - Markkinoiden todennäköisyys  
✅ **Market Margin** - Markkinamarginaali  
✅ **True Probability** - Todellinen todennäköisyys (ELO + adjustments)  
✅ **Edge** - Etu  
✅ **Expected Value** - Odotusarvo  
✅ **Kelly Criterion** - Optimaalinen panos  
✅ **ROI** - Return on Investment  
✅ **Risk Score** - Riskiscore  
✅ **Profit/Loss** - Voitto/Tappio  
✅ **Win Rate** - Voittoprosentti  
✅ **Sharpe Ratio** - Risk-adjusted return  
✅ **Profit Factor** - Voitto/tappio-suhde  
✅ **Max Drawdown** - Suurin tappio  

**🧮 Kaikki kaavat valmiina Notion-käyttöön! 💰**







