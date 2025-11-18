#!/bin/bash
# Create Project Status page in Notion
# ====================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "📊 Creating Project Status page in Notion..."
echo "=============================================="

# Activate virtual environment if available
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Python script
python3 src/notion/project_status_manager.py

echo ""
echo "✅ Done!"
echo ""
echo "💡 The status page will be automatically updated by the scraper."

