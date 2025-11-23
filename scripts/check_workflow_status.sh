#!/bin/bash
# Check GitHub Actions workflow status
# Usage: ./scripts/check_workflow_status.sh

echo "🔍 Checking GitHub Actions Workflow Status"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get repository info
REPO_OWNER=$(git remote get-url origin | sed -E 's/.*github.com[:/]([^/]+)\/([^/]+)\.git/\1/')
REPO_NAME=$(git remote get-url origin | sed -E 's/.*github.com[:/]([^/]+)\/([^/]+)\.git/\2/' | sed 's/\.git$//')

echo "Repository: $REPO_OWNER/$REPO_NAME"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI (gh) not installed${NC}"
    echo ""
    echo "Install: brew install gh"
    echo "Or check manually: https://github.com/$REPO_OWNER/$REPO_NAME/actions"
    echo ""
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated with GitHub CLI${NC}"
    echo ""
    echo "Authenticate: gh auth login"
    echo "Or check manually: https://github.com/$REPO_OWNER/$REPO_NAME/actions"
    echo ""
    exit 1
fi

echo "📊 Recent Workflow Runs:"
echo ""

# ITF Rankings Scraper
echo -e "${YELLOW}ITF Rankings Scraper:${NC}"
ITF_RUNS=$(gh run list --workflow=itf-rankings-scraper.yml --limit 5 --json status,conclusion,createdAt,displayTitle 2>/dev/null)
if [ -z "$ITF_RUNS" ]; then
    echo -e "  ${RED}❌ No runs found${NC}"
else
    echo "$ITF_RUNS" | jq -r '.[] | "  \(.status) | \(.conclusion // "in_progress") | \(.createdAt) | \(.displayTitle)"' 2>/dev/null || echo "  (Parse error - check manually)"
fi
echo ""

# Match History Scraper
echo -e "${YELLOW}Match History Scraper:${NC}"
MATCH_RUNS=$(gh run list --workflow=match-history-scraper.yml --limit 5 --json status,conclusion,createdAt,displayTitle 2>/dev/null)
if [ -z "$MATCH_RUNS" ]; then
    echo -e "  ${RED}❌ No runs found${NC}"
else
    echo "$MATCH_RUNS" | jq -r '.[] | "  \(.status) | \(.conclusion // "in_progress") | \(.createdAt) | \(.displayTitle)"' 2>/dev/null || echo "  (Parse error - check manually)"
fi
echo ""

echo "🔗 View in browser:"
echo "  https://github.com/$REPO_OWNER/$REPO_NAME/actions"
echo ""

echo "📅 Scheduled times:"
echo "  ITF Rankings: Daily at 08:00 EET (06:00 UTC)"
echo "  Match History: Daily at 09:00 EET (07:00 UTC)"
echo ""

