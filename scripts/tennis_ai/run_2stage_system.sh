#!/bin/bash
# 2-Stage Tennis System Runner
# Runs Stage 1 (scan) and Stage 2 (AI analysis) sequentially

set -e  # Exit on error

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Log directory
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# Log files
STAGE1_LOG="$LOG_DIR/stage1_$(date +%Y%m%d_%H%M%S).log"
STAGE2_LOG="$LOG_DIR/stage2_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 Starting 2-Stage Tennis System"
echo "   Project: $PROJECT_ROOT"
echo "   Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "="*60

# Change to project root
cd "$PROJECT_ROOT"

# Stage 1: Scan ITF matches
echo ""
echo "📋 Stage 1: Scanning ITF matches..."
echo "   Log: $STAGE1_LOG"
python3 "$SCRIPT_DIR/stage1_scanner.py" 2>&1 | tee "$STAGE1_LOG"

STAGE1_EXIT=${PIPESTATUS[0]}

if [ $STAGE1_EXIT -eq 0 ]; then
    echo "✅ Stage 1 completed successfully"
else
    echo "❌ Stage 1 failed (exit code: $STAGE1_EXIT)"
    echo "   Check log: $STAGE1_LOG"
    exit 1
fi

# Wait a bit between stages
sleep 2

# Stage 2: AI Analysis
echo ""
echo "🤖 Stage 2: OpenAI Deep Analysis..."
echo "   Log: $STAGE2_LOG"
python3 "$SCRIPT_DIR/stage2_ai_analyzer.py" 2>&1 | tee "$STAGE2_LOG"

STAGE2_EXIT=${PIPESTATUS[0]}

if [ $STAGE2_EXIT -eq 0 ]; then
    echo "✅ Stage 2 completed successfully"
else
    echo "❌ Stage 2 failed (exit code: $STAGE2_EXIT)"
    echo "   Check log: $STAGE2_LOG"
    exit 1
fi

echo ""
echo "="*60
echo "✅ 2-Stage System completed successfully"
echo "   Stage 1 log: $STAGE1_LOG"
echo "   Stage 2 log: $STAGE2_LOG"
echo ""
echo "📊 Next: Review promoted bets in Notion Bets DB"

