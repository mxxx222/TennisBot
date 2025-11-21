# 🚀 ITF Entries Intelligence - Deployment Checklist

## 📊 Current System Status

### Statistics (as of 2025-11-18)
- **Total analyzed**: 25 matches
- **High value bets**: 0
- **Recommendations**: 0 bets, 25 skips
- **ImpliedP range**: 50.0% - 50.0%
- **Above 70% threshold**: 0/25 (0.0%)
- **Pre-filtered candidates**: 100 matches
- **Average pre-filter score**: 85.0/100

### Notion Database Configuration
- **NOTION_AI_PREDICTIONS_DB_ID**: `f114ed7edffc4e799a05280ca89bc63e`
- **NOTION_TENNIS_PREMATCH_DB_ID**: `81a70fea5de140d384c77abee225436d`
- **NOTION_BETTING_TRACKER_DB_ID**: `271a20e3-a65b-80d3-8ca4-fe96abf26e91`

### Environment Variables
- ✅ OPENAI_API_KEY: Set
- ✅ NOTION_API_KEY: Set
- ✅ NOTION_TOKEN: Set
- ⚠️  NOTION_AI_PREDICTIONS_DB_ID: Using default (not in env)
- ✅ NOTION_TENNIS_PREMATCH_DB_ID: Set
- ⚠️  NOTION_BETTING_TRACKER_DB_ID: Using default (not in env)

## ✅ Pre-Deployment Checklist

### Phase A1: Integration Testing

#### Task 1: Test ITF Entries Intelligence Scraper
- [ ] Run `python3 scripts/tennis_ai/itf_entries_intelligence_scraper.py`
- [ ] Verify scraper connects to itf-entries.netlify.app
- [ ] Verify returns tournament and player entry data
- [ ] Verify motivation scoring (0-10 scale)
- [ ] Verify withdrawal risk calculation (0-1 probability)
- [ ] Verify home tournament detection
- [ ] Check output files in `data/itf_entries/` directory

#### Task 2: Test Enhanced Agent Integration
- [ ] Run `python3 scripts/tennis_ai/enhanced_tennis_agent_integration.py`
- [ ] Verify EnhancedTennisAgent initializes
- [ ] Verify `analyze_match_with_intelligence()` works
- [ ] Verify motivation boost calculation (+3-8% impliedP)
- [ ] Verify withdrawal penalty (-5% impliedP)
- [ ] Verify home advantage detection (+5% impliedP)
- [ ] Verify enhanced impliedP respects 70% threshold

#### Task 3: Create Integration Bridge Script
- [ ] Create `scripts/tennis_ai/ai_analyzer_enhanced.py`
- [ ] Integrate EnhancedTennisAgent into analyze_match()
- [ ] Test with sample matches
- [ ] Verify output format compatible with save_results()

### Phase A2: Live Deployment

#### Task 4: Update Pipeline
- [ ] Create `scripts/tennis_ai/run_tennis_ai_enhanced.sh`
- [ ] Add Step 0.5: Run ITF entries scraper
- [ ] Replace Step 2: Use ai_analyzer_enhanced.py
- [ ] Test full pipeline end-to-end

#### Task 5: Deploy Small Batch
- [ ] Process 5-10 matches with enhanced system
- [ ] Monitor intelligence adjustments
- [ ] Compare enhanced vs base recommendations
- [ ] Save enhanced picks to Notion

#### Task 6: Update Notion Schema
- [ ] Add "Entries Intelligence Boost" (number) field
- [ ] Add "Motivation Score" (number) field
- [ ] Add "Withdrawal Risk" (select: LOW/MEDIUM/HIGH) field
- [ ] Add "Home Advantage" (checkbox) field
- [ ] Update save_to_notion.py to save intelligence data

### Phase A3: Performance Validation

#### Task 7: Performance Comparison
- [ ] Create comparison script
- [ ] Compare enhanced vs base performance
- [ ] Generate metrics report

#### Task 8: Validate Intelligence Accuracy
- [ ] Track 10-15 enhanced picks
- [ ] Validate motivation correlation
- [ ] Validate withdrawal risk accuracy
- [ ] Validate home advantage impact

#### Task 9: Optimize Parameters
- [ ] Adjust motivation thresholds
- [ ] Adjust withdrawal penalties
- [ ] Fine-tune scoring algorithms

#### Task 10: Generate Report
- [ ] Create performance report
- [ ] Document ROI improvement
- [ ] Make deployment recommendation

## 🔧 Required Notion Database Fields

### Current Fields (AI Predictions Database)
- Match (title)
- Tournament (rich_text)
- Pre-filter Score (number)
- AI Recommendation (select)
- AI Confidence (number)
- Predicted Edge (number)
- Actual Result (select)
- Match Date (date)
- Reasoning (rich_text)
- Match URL (url)

### New Fields Needed (for Intelligence)
- **Entries Intelligence Boost** (number): Total adjustment percentage
- **Motivation Score** (number): Average motivation (0-10)
- **Withdrawal Risk** (select): LOW / MEDIUM / HIGH
- **Home Advantage** (checkbox): true/false
- **Intelligence Confidence** (number): 0-1 confidence score

## 📝 Notes

- Current system shows 0 bets above 70% threshold - this is expected as base system is conservative
- Intelligence enhancement should boost some matches above 70% threshold
- Need to validate intelligence signals with real data before full deployment
- Start with small batch (5-10 matches) to validate approach

