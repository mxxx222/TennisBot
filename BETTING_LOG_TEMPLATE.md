# 📝 BETTING LOG TEMPLATE - Notion Database

**Purpose:** Track all bets for validated manual betting system  
**System:** +17.81% ROI proven (98 bets, 7 months)  
**Last Updated:** 18.11.2025

---

## 🗄️ NOTION DATABASE STRUCTURE

### Database Name: "Tennis Betting Log"

### Properties (Columns)

#### 1. Date & Time
- **Type:** Date
- **Format:** Date + Time
- **Required:** ✅ Yes
- **Example:** 2025-11-18 14:30

#### 2. Tournament
- **Type:** Text
- **Required:** ✅ Yes
- **Example:** "ITF W15 Antalya"
- **Notes:** Full tournament name

#### 3. Player 1
- **Type:** Text
- **Required:** ✅ Yes
- **Example:** "Maria Garcia"
- **Notes:** Player name

#### 4. Player 2
- **Type:** Text
- **Required:** ✅ Yes
- **Example:** "Anna Smith"
- **Notes:** Opponent name

#### 5. Selected Player
- **Type:** Select (Player 1 / Player 2)
- **Required:** ✅ Yes
- **Example:** "Player 1"
- **Notes:** Which player you bet on

#### 6. Odds
- **Type:** Number
- **Format:** 2 decimal places
- **Required:** ✅ Yes
- **Example:** 1.75
- **Notes:** Must be 1.51-2.00

#### 7. Stake
- **Type:** Number
- **Format:** Currency ($)
- **Required:** ✅ Yes
- **Example:** 10.00
- **Notes:** Current scaling: $10-20

#### 8. Bet Type
- **Type:** Select
- **Options:** SINGLE, COMBO (never use)
- **Required:** ✅ Yes
- **Default:** SINGLE
- **Notes:** Always SINGLE

#### 9. Result
- **Type:** Select
- **Options:** Win, Loss, Pending, Void
- **Required:** ✅ Yes
- **Example:** "Win"
- **Notes:** Update after match

#### 10. Profit/Loss
- **Type:** Formula
- **Formula:** 
  ```
  if(prop("Result") == "Win", 
     (prop("Odds") - 1) * prop("Stake"), 
     -prop("Stake"))
  ```
- **Format:** Currency ($)
- **Example:** +7.50 (win) or -10.00 (loss)

#### 11. ROI
- **Type:** Formula
- **Formula:**
  ```
  if(prop("Stake") > 0,
     (prop("Profit/Loss") / prop("Stake")) * 100,
     0)
  ```
- **Format:** Percentage
- **Example:** +75.00% (win) or -100.00% (loss)

#### 12. Player 1 Ranking
- **Type:** Number
- **Required:** ⚠️ Optional
- **Example:** 245
- **Notes:** WTA ranking if available

#### 13. Player 2 Ranking
- **Type:** Number
- **Required:** ⚠️ Optional
- **Example:** 312
- **Notes:** WTA ranking if available

#### 14. Tournament Level
- **Type:** Select
- **Options:** ITF W15, ITF W25, ITF W60, ITF W80, ITF W100, ATP Challenger
- **Required:** ✅ Yes
- **Example:** "ITF W15"

#### 15. Surface
- **Type:** Select
- **Options:** Hard, Clay, Grass
- **Required:** ⚠️ Optional
- **Example:** "Hard"

#### 16. Bookmaker
- **Type:** Select
- **Options:** Bet365, Pinnacle, Betfair, 1xBet, Other
- **Required:** ✅ Yes
- **Example:** "Bet365"

#### 17. Notes
- **Type:** Text
- **Required:** ❌ No
- **Example:** "Good value, player in form"
- **Notes:** Any additional observations

#### 18. Week
- **Type:** Formula
- **Formula:**
  ```
  formatDate(prop("Date & Time"), "WW")
  ```
- **Format:** Text
- **Example:** "Week 47"
- **Notes:** For weekly reviews

#### 19. Month
- **Type:** Formula
- **Formula:**
  ```
  formatDate(prop("Date & Time"), "MMMM YYYY")
  ```
- **Format:** Text
- **Example:** "November 2025"
- **Notes:** For monthly reviews

---

## 📊 VIEWS (FILTERS)

### 1. All Bets (Default)
- **Sort:** Date & Time (Newest first)
- **Filter:** None
- **Purpose:** Complete log

### 2. This Week
- **Sort:** Date & Time (Newest first)
- **Filter:** Week = This Week
- **Purpose:** Weekly review

### 3. This Month
- **Sort:** Date & Time (Newest first)
- **Filter:** Month = This Month
- **Purpose:** Monthly review

### 4. Wins Only
- **Sort:** Date & Time (Newest first)
- **Filter:** Result = Win
- **Purpose:** Analyze winning bets

### 5. Losses Only
- **Sort:** Date & Time (Newest first)
- **Filter:** Result = Loss
- **Purpose:** Analyze losing bets

### 6. Pending
- **Sort:** Date & Time (Oldest first)
- **Filter:** Result = Pending
- **Purpose:** Track open bets

### 7. By Stake Level
- **Group:** Stake
- **Sort:** Date & Time (Newest first)
- **Purpose:** Track scaling progress

---

## 📈 CALCULATED PROPERTIES

### Weekly Summary View

**Create separate database:** "Weekly Summary"

**Properties:**
- Week (Text)
- Total Bets (Number)
- Wins (Number)
- Losses (Number)
- Win Rate (Formula: Wins / Total Bets * 100)
- Total Stakes (Sum of Stakes)
- Total Profit (Sum of Profit/Loss)
- ROI (Formula: Total Profit / Total Stakes * 100)

### Monthly Summary View

**Create separate database:** "Monthly Summary"

**Properties:**
- Month (Text)
- Total Bets (Number)
- Wins (Number)
- Losses (Number)
- Win Rate (Formula)
- Total Stakes (Sum)
- Total Profit (Sum)
- ROI (Formula)
- Average Stake (Formula: Total Stakes / Total Bets)

---

## 📝 ENTRY TEMPLATE

### When Placing Bet

**Fill in immediately:**
1. Date & Time ✅
2. Tournament ✅
3. Player 1 ✅
4. Player 2 ✅
5. Selected Player ✅
6. Odds ✅
7. Stake ✅
8. Bet Type ✅ (always SINGLE)
9. Result: "Pending"
10. Tournament Level ✅
11. Bookmaker ✅
12. Notes (optional)

**Update after match:**
1. Result (Win/Loss)
2. Notes (if needed)

**Profit/Loss and ROI calculate automatically**

---

## ✅ VALIDATION CHECKLIST

### Before Placing Bet

- [ ] Odds between 1.51-2.00?
- [ ] ITF Women tournament?
- [ ] SINGLE bet (not combo)?
- [ ] Stake appropriate for phase?
- [ ] Criteria met?

### After Placing Bet

- [ ] Logged to Notion immediately?
- [ ] All fields filled?
- [ ] Result set to "Pending"?

### After Match

- [ ] Result updated?
- [ ] Profit/Loss calculated correctly?
- [ ] Notes added if needed?

---

## 📊 EXAMPLE ENTRY

### Entry Example

**Date & Time:** 2025-11-18 14:30  
**Tournament:** ITF W15 Antalya  
**Player 1:** Maria Garcia  
**Player 2:** Anna Smith  
**Selected Player:** Player 1 (Maria Garcia)  
**Odds:** 1.75  
**Stake:** $10.00  
**Bet Type:** SINGLE  
**Result:** Pending → Win  
**Profit/Loss:** +$7.50  
**ROI:** +75.00%  
**Player 1 Ranking:** 245  
**Player 2 Ranking:** 312  
**Tournament Level:** ITF W15  
**Surface:** Hard  
**Bookmaker:** Bet365  
**Notes:** "Good value, player in form, ranking advantage"  
**Week:** Week 47  
**Month:** November 2025

---

## 🔄 WEEKLY REVIEW PROCESS

### Every Sunday

1. **Open "This Week" view**
2. **Calculate:**
   - Total bets
   - Wins/Losses
   - Win rate
   - Total stakes
   - Total profit
   - ROI

3. **Review:**
   - Did you follow criteria?
   - Any emotional bets?
   - Performance vs. baseline
   - Adjustments needed?

4. **Update Weekly Summary database**

---

## 📅 MONTHLY REVIEW PROCESS

### End of Month

1. **Open "This Month" view**
2. **Calculate:**
   - Monthly totals
   - Monthly ROI
   - Monthly profit
   - Average stake
   - Consistency

3. **Review:**
   - Monthly performance
   - Scaling progress
   - Criteria effectiveness
   - Market changes

4. **Update Monthly Summary database**

5. **Decide:**
   - Continue scaling?
   - Adjust stakes?
   - Review criteria?
   - Consider automation?

---

## 💡 TIPS

### Consistency

- Log immediately after placing bet
- Don't wait to update results
- Review weekly without fail
- Track everything meticulously

### Analysis

- Review wins to see what works
- Review losses to see what doesn't
- Look for patterns
- Adjust criteria if needed

### Discipline

- Follow criteria strictly
- No emotional betting
- Log every bet
- Review regularly

---

## 🚨 RED FLAGS

### Missing Data

- ❌ Bet not logged
- ❌ Missing required fields
- ❌ Result not updated
- ❌ Incomplete entries

### Criteria Violations

- ❌ Odds outside 1.51-2.00
- ❌ Combo bets
- ❌ Non-ITF tournaments
- ❌ Emotional betting

### Performance Issues

- ❌ ROI dropping
- ❌ Win rate declining
- ❌ Multiple losses
- ❌ Inconsistent results

---

## ✅ SUCCESS METRICS

### Good Logging

- ✅ All bets logged
- ✅ All fields filled
- ✅ Results updated promptly
- ✅ Weekly reviews done
- ✅ Monthly reviews done

### Good Performance

- ✅ ROI > +15%
- ✅ Win rate > 45%
- ✅ Consistent results
- ✅ Criteria followed
- ✅ No emotional betting

---

*Template created: 18.11.2025*  
*System: Validated +17.81% ROI*  
*Next review: Weekly*

