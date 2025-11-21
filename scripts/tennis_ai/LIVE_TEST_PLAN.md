# 🚀 ITF Entries Intelligence - Live Test Plan

## Objective
Validate enhanced system works correctly in production with real match data.

## Pre-Test Checklist

### ✅ System Status
- [x] ITF Entries Scraper: Tested
- [x] Enhanced Agent Integration: Tested  
- [x] Integration Bridge: Created
- [x] Enhanced Pipeline: Created
- [x] Notion Schema: Updated with intelligence fields
- [x] save_to_notion.py: Updated to save intelligence data

### ⚠️ Pre-Test Requirements
- [ ] Verify Notion database has intelligence fields
- [ ] Check current match data in Notion
- [ ] Ensure OPENAI_API_KEY is set
- [ ] Ensure NOTION_API_KEY is set

## Test Execution

### Step 1: Run ITF Entries Intelligence Update
```bash
python3 scripts/tennis_ai/itf_entries_intelligence_scraper.py
```
**Expected:** Scraper runs, saves data to `data/itf_entries/`

### Step 2: Pre-filter Matches
```bash
python3 scripts/tennis_ai/prefilter_w15_matches.py
```
**Expected:** Generates `data/tennis_ai/ai_candidates.json` with upcoming matches

### Step 3: Run Enhanced Analysis (Small Batch)
```bash
# Create small test batch first (5-10 matches)
python3 scripts/tennis_ai/ai_analyzer_enhanced.py data/tennis_ai/ai_candidates_test_batch.json
```
**Expected:** 
- Analyzes matches with GPT-4
- Enhances with entries intelligence
- Generates `ai_analysis_results.json` with intelligence data

### Step 4: Verify Intelligence Data
```bash
python3 -c "
import json
with open('data/tennis_ai/ai_analysis_results.json') as f:
    data = json.load(f)
    
intel_analyses = [a for a in data['all_analyses'] if a.get('intelligence_enabled')]
print(f'Intelligence enhanced: {len(intel_analyses)}/{len(data[\"all_analyses\"])}')

if intel_analyses:
    sample = intel_analyses[0]
    intel = sample.get('entries_intelligence', {})
    print(f'Sample intelligence:')
    print(f'  Boost: {intel.get(\"total_adjustment\", \"N/A\")}')
    print(f'  Risk: {intel.get(\"withdrawal_risk\", \"N/A\")}')
    print(f'  Home: {intel.get(\"home_advantage\", False)}')
"
```

### Step 5: Save to Notion
```bash
python3 scripts/tennis_ai/save_to_notion.py
```
**Expected:**
- Saves predictions to Notion
- Includes intelligence fields
- No errors about missing fields

### Step 6: Verify Notion Data
- Open Notion database
- Check that new predictions have intelligence fields populated
- Verify data looks correct

## Success Criteria

✅ **All steps complete without errors**
✅ **Intelligence data generated for all matches**
✅ **Notion integration saves intelligence fields**
✅ **At least 1-2 matches get intelligence boost above 70% threshold**

## Monitoring (Week 1)

Track these metrics for enhanced picks:

1. **Intelligence Accuracy**
   - Motivation score correlation with wins
   - Withdrawal risk accuracy
   - Home advantage impact

2. **ROI Performance**
   - Enhanced picks win rate
   - ROI vs baseline system
   - Intelligence boost effectiveness

3. **System Reliability**
   - Scraper success rate
   - Intelligence data availability
   - Notion save success rate

## Expected Results

- **Intelligence data:** Available for 80%+ of matches
- **Intelligence boosts:** 2-5% average adjustment
- **Enhanced picks:** 5-10 matches above 70% threshold
- **ROI improvement:** +5-10% vs baseline (initial week)

## Troubleshooting

### Issue: No intelligence data generated
**Solution:** Check ITF scraper output, verify entries data available

### Issue: Notion save fails
**Solution:** Verify intelligence fields exist in Notion schema

### Issue: All matches get 0% boost
**Solution:** Normal if no entry data available - scraper may need real data source

## Next Steps After Validation

Once validated:
1. Scale to full batch (25-50 matches)
2. Schedule daily automation
3. Clone to Football OU2.5
4. Expand to other data sources

