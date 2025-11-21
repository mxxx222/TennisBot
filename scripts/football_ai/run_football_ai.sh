#!/bin/bash

# Football OU2.5 AI - ROI-Optimized Pipeline
# Runs: pre-filter → AI analyzer → bet list generator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "⚽ FOOTBALL OU2.5 AI - ROI-OPTIMIZED PIPELINE"
echo "============================================="
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

if [ -z "$NOTION_FOOTBALL_PREMATCH_DB_ID" ]; then
    echo "⚠️  NOTION_FOOTBALL_PREMATCH_DB_ID not set"
    echo "   Set it in telegram_secrets.env or update in prefilter_ou25_matches.py"
fi

echo "✅ Environment OK"
echo ""

# Step 1: Pre-filter
echo "📊 STEP 1: Pre-filtering football matches (FREE)"
echo "-------------------------------------------------"
python3 "$SCRIPT_DIR/prefilter_ou25_matches.py"

echo ""
echo "✅ Pre-filter complete"
echo ""

# Step 2: AI Analysis
echo "🤖 STEP 2: AI Analysis (Costs money)"
echo "-------------------------------------"
python3 "$SCRIPT_DIR/ai_analyzer.py"

echo ""
echo "✅ AI analysis complete"
echo ""

# Step 3: Generate Report
echo "📄 STEP 3: Generating bet list"
echo "-------------------------------"
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
    if [ -z "$NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID" ]; then
        echo "⚠️  NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID not set - skipping Notion save"
        echo "   Set it in telegram_secrets.env or update in save_to_notion.py"
    else
        python3 "$SCRIPT_DIR/save_to_notion.py"
    fi
fi

echo ""
echo "================================================================================"
echo "🎉 PIPELINE COMPLETE!"
echo "================================================================================"
echo ""
echo "📁 Output files:"
echo "   - data/football_ai/ai_candidates.json (pre-filtered matches)"
echo "   - data/football_ai/ai_analysis_results.json (AI recommendations)"
echo "   - data/football_ai/bet_list.txt (ready-to-bet list)"
echo ""
if [ -n "$NOTION_TOKEN" ] || [ -n "$NOTION_API_KEY" ]; then
    if [ -n "$NOTION_FOOTBALL_AI_PREDICTIONS_DB_ID" ]; then
        echo "💾 Predictions saved to Notion database"
        echo ""
    fi
fi
echo "📋 Next: Review data/football_ai/bet_list.txt and place your bets!"
echo ""

