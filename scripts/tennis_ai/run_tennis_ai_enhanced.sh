#!/bin/bash

# Tennis AI - Enhanced Pipeline with ITF Entries Intelligence
# Ajaa: ITF entries scraper → pre-filter → AI analyzer (enhanced) → bet list generator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🎾 TENNIS AI - ENHANCED PIPELINE (with ITF Entries Intelligence)"
echo "================================================================"
echo ""

cd "$PROJECT_ROOT"

# Checks
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 required"; exit 1; }

# Load environment variables
if [ -f "$PROJECT_ROOT/telegram_secrets.env" ]; then
    source "$PROJECT_ROOT/telegram_secrets.env"
else
    echo "⚠️  telegram_secrets.env not found, using system environment"
fi

if [ -z "$NOTION_API_KEY" ] && [ -z "$NOTION_TOKEN" ]; then
    echo "❌ NOTION_API_KEY or NOTION_TOKEN not set"
    echo "   Load: source $PROJECT_ROOT/telegram_secrets.env"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set"
    echo "   Load: source $PROJECT_ROOT/telegram_secrets.env"
    echo "   Get key: https://platform.openai.com/api-keys"
    exit 1
fi

if [ -z "$NOTION_TENNIS_PREMATCH_DB_ID" ] && [ -z "$NOTION_PREMATCH_DB_ID" ]; then
    echo "⚠️  NOTION_TENNIS_PREMATCH_DB_ID not set, using default"
fi

echo "✅ Environment OK"
echo ""

# Step 0.5: ITF Entries Intelligence (Daily Update)
echo "🧠 STEP 0.5: ITF Entries Intelligence Update"
echo "----------------------------------------------"
python3 "$SCRIPT_DIR/itf_entries_intelligence_scraper.py"

echo ""
echo "✅ ITF entries intelligence updated"
echo ""

# Step 1: Pre-filter
echo "📊 STEP 1: Pre-filtering W15 matches (FREE)"
echo "---------------------------------------------"
python3 "$SCRIPT_DIR/prefilter_w15_matches.py"

echo ""
echo "✅ Pre-filter complete"
echo ""

# Step 1.5: Create optimized batch (optional but recommended)
echo "🎯 STEP 1.5: Creating optimized batch (top 25 matches)"
echo "------------------------------------------------------"
if [ -f "$SCRIPT_DIR/create_optimized_batch.py" ]; then
    python3 "$SCRIPT_DIR/create_optimized_batch.py"
    echo ""
    echo "✅ Optimized batch created"
    echo ""
else
    echo "⚠️  create_optimized_batch.py not found, skipping"
    echo ""
fi

# Step 2: AI Analysis (Enhanced)
echo "🤖 STEP 2: AI Analysis with Entries Intelligence (Costs money)"
echo "----------------------------------------------------------------"
export ENABLE_ENTRIES_INTELLIGENCE=true
python3 "$SCRIPT_DIR/ai_analyzer_enhanced.py"

echo ""
echo "✅ Enhanced AI analysis complete"
echo ""

# Step 3: Generate Report
echo "📄 STEP 3: Generating bet list"
echo "--------------------------------"
python3 "$SCRIPT_DIR/generate_bet_list.py"

echo ""
echo "✅ Bet list generated"
echo ""

# Step 4: Save to Notion (optional)
echo "💾 STEP 4: Saving to Notion (optional)"
echo "----------------------------------------"
if [ -z "$NOTION_TOKEN" ] && [ -z "$NOTION_API_KEY" ]; then
    echo "⚠️  NOTION_TOKEN not set - skipping Notion save"
    echo "   To enable: Add NOTION_API_KEY to telegram_secrets.env"
else
    python3 "$SCRIPT_DIR/save_to_notion.py"
fi

echo ""
echo "================================================================================"
echo "🎉 ENHANCED PIPELINE COMPLETE!"
echo "================================================================================"
echo ""
echo "📁 Output files:"
echo "   - data/itf_entries/ (ITF entries intelligence data)"
echo "   - data/tennis_ai/ai_candidates.json (pre-filtered matches)"
echo "   - data/tennis_ai/ai_analysis_results.json (AI recommendations with intelligence)"
echo "   - data/tennis_ai/bet_list.txt (ready-to-bet list)"
echo ""
if [ -n "$NOTION_TOKEN" ] || [ -n "$NOTION_API_KEY" ]; then
    echo "💾 Predictions saved to Notion database (with intelligence metadata)"
    echo ""
fi
echo "📋 Next: Review data/tennis_ai/bet_list.txt and place your bets!"
echo ""
echo "🧠 Intelligence Features:"
echo "   - Entry motivation scoring"
echo "   - Withdrawal risk detection"
echo "   - Home advantage detection"
echo "   - Enhanced impliedP calculations"
echo ""

