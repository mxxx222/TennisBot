# Notion Database Schema Setup for ITF Entries Intelligence

## Required Database
**Database ID:** `f114ed7edffc4e799a05280ca89bc63e` (NOTION_AI_PREDICTIONS_DB_ID)

## New Fields to Add

### 1. Entries Intelligence Boost
- **Type:** Number
- **Format:** Number (no percentage sign)
- **Description:** Total intelligence adjustment percentage (e.g., +5.0, -3.0)
- **How to add:**
  1. Open Notion database
  2. Click "+" to add new property
  3. Name: "Entries Intelligence Boost"
  4. Type: "Number"
  5. Format: "Number"

### 2. Intelligence Confidence
- **Type:** Number
- **Format:** Number (0-1 scale)
- **Description:** Overall confidence in intelligence data (0.0 to 1.0)
- **How to add:**
  1. Click "+" to add new property
  2. Name: "Intelligence Confidence"
  3. Type: "Number"
  4. Format: "Number"

### 3. Withdrawal Risk
- **Type:** Select
- **Options:** LOW, MEDIUM, HIGH
- **Description:** Risk level of player withdrawal
- **How to add:**
  1. Click "+" to add new property
  2. Name: "Withdrawal Risk"
  3. Type: "Select"
  4. Add options: "LOW", "MEDIUM", "HIGH"

### 4. Home Advantage
- **Type:** Checkbox
- **Description:** Whether player has home tournament advantage
- **How to add:**
  1. Click "+" to add new property
  2. Name: "Home Advantage"
  3. Type: "Checkbox"

## Verification

After adding fields, verify they appear in the database:
- All 4 fields should be visible
- Field names must match exactly (case-sensitive)
- Select field must have all 3 options

## Testing

Once fields are added, test by running:
```bash
python3 scripts/tennis_ai/save_to_notion.py
```

The script will attempt to save intelligence data. If fields are missing, you'll see errors.

