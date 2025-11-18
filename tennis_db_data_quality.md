# ✅ TENNIS DATABASE DATA QUALITY - CHECKLIST

## 📋 VALIDOINTINÄKYMÄT JA CHECKLIST

### **1. PUUTTUVAT KENTÄT**

#### **Players Table**
```
✅ Name - REQUIRED
✅ ATP/WTA - REQUIRED
✅ Ranking - REQUIRED
✅ Country - REQUIRED
⚠️ Age - OPTIONAL but recommended
⚠️ Prize Money - OPTIONAL
```

**Notion Filter:**
```
Name is empty OR ATP/WTA is empty OR Ranking is empty OR Country is empty
```

---

#### **Matches Table**
```
✅ Match - REQUIRED
✅ Player 1 - REQUIRED (Relation)
✅ Player 2 - REQUIRED (Relation)
✅ Date - REQUIRED
✅ Status - REQUIRED
⚠️ Score - OPTIONAL (required if Status = Finished)
⚠️ Surface - OPTIONAL but recommended
```

**Notion Filter:**
```
Match is empty OR Player 1 is empty OR Player 2 is empty OR Date is empty OR Status is empty
```

---

#### **ROI Analysis Table**
```
✅ Match - REQUIRED (Relation)
✅ Player - REQUIRED
✅ True Probability % - REQUIRED
✅ Market Probability % - REQUIRED
✅ Edge % - REQUIRED
✅ Recommended Stake € - REQUIRED
⚠️ Result - OPTIONAL (required after match)
⚠️ Profit/Loss € - OPTIONAL (required if Result != Pending)
```

**Notion Filter:**
```
Match is empty OR Player is empty OR True Probability % is empty OR Market Probability % is empty OR Edge % is empty OR Recommended Stake € is empty
```

---

### **2. ORVOT RELAATIOT**

#### **Matches without Players**
```
Filter: Player 1 is empty OR Player 2 is empty
Action: Link to Players table
```

#### **Matches without Events**
```
Filter: Event is empty
Action: Link to Events table or create Event
```

#### **Matches without Tournaments**
```
Filter: Tournament is empty
Action: Link to Tournaments table or create Tournament
```

#### **Statistics without Matches**
```
Filter: Match is empty
Tables: Serve Stats, Return Stats, Quality Stats, Ratings, Odds, ROI Analysis, Environment
Action: Link to Matches table
```

#### **Statistics without Players**
```
Filter: Player is empty
Tables: Player Stats, Surface Stats, Serve Stats, Return Stats, Quality Stats, H2H Stats, Ratings, Health
Action: Link to Players table
```

---

### **3. DATAN JOHDONMUKAISUUS**

#### **Score Validation**
```
Rule: If Status = "Finished", Score must not be empty
Filter: Status is "Finished" AND Score is empty
```

#### **Date Validation**
```
Rule: Match Date must be >= Tournament Start Date AND <= Tournament End Date
Filter: Date < Tournament Start Date OR Date > Tournament End Date
```

#### **Probability Validation**
```
Rule: True Probability + Market Probability should be close to 1.0 (accounting for margin)
Filter: (True Probability % + Market Probability %) < 0.90 OR > 1.10
```

#### **Edge Validation**
```
Rule: Edge = True Probability - Market Probability
Filter: Edge % != (True Probability % - Market Probability %)
```

#### **ROI Validation**
```
Rule: ROI should be positive if Edge > 0
Filter: Edge % > 0 AND ROI % <= 0
```

---

### **4. NUMERISET RAJAT**

#### **Ranking Validation**
```
Rule: Ranking must be between 1 and 10000
Filter: Ranking < 1 OR Ranking > 10000
```

#### **Age Validation**
```
Rule: Age must be between 14 and 50
Filter: Age < 14 OR Age > 50
```

#### **Win % Validation**
```
Rule: Win % must be between 0 and 1
Filter: Win % < 0 OR Win % > 1
```

#### **Odds Validation**
```
Rule: Odds must be >= 1.01
Filter: Odds < 1.01
```

#### **Stake Validation**
```
Rule: Recommended Stake must be > 0
Filter: Recommended Stake € <= 0
```

---

### **5. RELAATIOIDEN EHEYS**

#### **H2H Stats Validation**
```
Rule: Player 1 and Player 2 must be different
Filter: Player 1 = Player 2
```

#### **H2H Stats Validation**
```
Rule: Total Matches = Player 1 Wins + Player 2 Wins
Filter: Total Matches != (Player 1 Wins + Player 2 Wins)
```

#### **Surface Stats Validation**
```
Rule: Surface must match Match Surface
Filter: Surface != Match Surface
```

---

### **6. AJALLISET VALIDOINNIT**

#### **Last Updated Validation**
```
Rule: Last Updated should be recent (within 7 days for active data)
Filter: Last Updated < (Today - 7 days)
```

#### **Match Date Validation**
```
Rule: Match Date should not be in the future (unless Status = Scheduled)
Filter: Date > Today AND Status != "Scheduled"
```

---

### **7. DATA QUALITY SCORE**

#### **Completeness Score**
```
Score = (Filled Required Fields / Total Required Fields) × 100

High Quality: >= 90%
Medium Quality: 70-89%
Low Quality: < 70%
```

**Notion Formula:**
```javascript
// Count filled required fields
if(prop("Name") != "", 1, 0) + 
if(prop("ATP/WTA") != "", 1, 0) + 
if(prop("Ranking") != "", 1, 0) + 
if(prop("Country") != "", 1, 0)
```

---

### **8. VALIDOINTINÄKYMÄT NOTIONISSA**

#### **View 1: Missing Required Fields**
```
Filter: Name is empty OR ATP/WTA is empty OR Ranking is empty
Sort: Last Updated (Oldest first)
```

#### **View 2: Orphan Relations**
```
Filter: Player 1 is empty OR Player 2 is empty OR Event is empty
Sort: Date (Oldest first)
```

#### **View 3: Data Inconsistencies**
```
Filter: Edge % != (True Probability % - Market Probability %) OR 
        Status is "Finished" AND Score is empty OR
        Date > Today AND Status != "Scheduled"
Sort: Date (Oldest first)
```

#### **View 4: Low Quality Data**
```
Filter: Data Quality Score < 70
Sort: Data Quality Score (Ascending)
```

#### **View 5: Stale Data**
```
Filter: Last Updated < (Today - 7 days)
Sort: Last Updated (Oldest first)
```

---

### **9. AUTOMAATTINEN VALIDOINTI**

#### **Python Validation Script**
```python
def validate_tennis_db(notion_client, database_id):
    """Validoi tennis-tietokanta"""
    
    issues = []
    
    # 1. Puuttuvat kentät
    missing_fields = notion_client.databases.query(
        database_id=database_id,
        filter={
            "or": [
                {"property": "Name", "title": {"is_empty": True}},
                {"property": "Ranking", "number": {"is_empty": True}}
            ]
        }
    )
    
    if missing_fields['results']:
        issues.append(f"Missing fields: {len(missing_fields['results'])} records")
    
    # 2. Orvot relaatiot
    orphan_relations = notion_client.databases.query(
        database_id=database_id,
        filter={
            "or": [
                {"property": "Player 1", "relation": {"is_empty": True}},
                {"property": "Player 2", "relation": {"is_empty": True}}
            ]
        }
    )
    
    if orphan_relations['results']:
        issues.append(f"Orphan relations: {len(orphan_relations['results'])} records")
    
    # 3. Datan johdonmukaisuus
    inconsistencies = notion_client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Status", "select": {"equals": "Finished"}},
                {"property": "Score", "rich_text": {"is_empty": True}}
            ]
        }
    )
    
    if inconsistencies['results']:
        issues.append(f"Inconsistencies: {len(inconsistencies['results'])} records")
    
    return issues
```

---

### **10. DATA QUALITY DASHBOARD**

#### **Summary Metrics**
```
✅ Total Records: COUNT(All)
✅ Complete Records: COUNT(Data Quality Score >= 90)
✅ Incomplete Records: COUNT(Data Quality Score < 90)
✅ Orphan Relations: COUNT(Player 1 is empty OR Player 2 is empty)
✅ Stale Data: COUNT(Last Updated < Today - 7 days)
✅ Validation Errors: COUNT(All validation filters)
```

---

## ✅ YHTEENVETO

**VALIDOINTINÄKYMÄT:**

✅ **Missing Required Fields** - Puuttuvat pakolliset kentät  
✅ **Orphan Relations** - Orvot relaatiot  
✅ **Data Inconsistencies** - Datan johdonmukaisuusongelmat  
✅ **Low Quality Data** - Matala laatu  
✅ **Stale Data** - Vanhentunut data  
✅ **Numeriset rajat** - Validointi  
✅ **Ajalliset validointit** - Päivämäärävalidointi  
✅ **Data Quality Score** - Laatupisteet  

**✅ Kaikki validointinäkymät valmiina Notioniin! 📊**







