#!/bin/bash
# Script to update GitHub token in Cursor secrets.json

echo "🔐 GitHub Token Updater for Cursor MCP"
echo "========================================"
echo ""

# Find secrets.json
SECRETS_FILE="$HOME/.cursor/secrets.json"

if [ ! -f "$SECRETS_FILE" ]; then
    echo "❌ secrets.json not found at $SECRETS_FILE"
    echo "   Creating new file..."
    mkdir -p "$HOME/.cursor"
    echo '{"GITHUB_TOKEN": ""}' > "$SECRETS_FILE"
fi

echo "📋 Current token location: $SECRETS_FILE"
echo ""
echo "📝 Instructions:"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token' → 'Generate new token (classic)'"
echo "3. Name: 'Cursor MCP GitHub'"
echo "4. Select scopes:"
echo "   ✅ repo (Full control)"
echo "   ✅ workflow (Update GitHub Action workflows)"
echo "5. Generate and copy the token"
echo ""
read -p "Paste your new GitHub token here: " NEW_TOKEN

if [ -z "$NEW_TOKEN" ]; then
    echo "❌ No token provided"
    exit 1
fi

# Update token in secrets.json
if command -v jq &> /dev/null; then
    # Use jq if available
    jq ".GITHUB_TOKEN = \"$NEW_TOKEN\"" "$SECRETS_FILE" > "$SECRETS_FILE.tmp" && mv "$SECRETS_FILE.tmp" "$SECRETS_FILE"
    echo "✅ Token updated using jq"
else
    # Fallback to sed
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/\"GITHUB_TOKEN\": \".*\"/\"GITHUB_TOKEN\": \"$NEW_TOKEN\"/" "$SECRETS_FILE"
    else
        # Linux
        sed -i "s/\"GITHUB_TOKEN\": \".*\"/\"GITHUB_TOKEN\": \"$NEW_TOKEN\"/" "$SECRETS_FILE"
    fi
    echo "✅ Token updated using sed"
fi

echo ""
echo "🔄 Restart Cursor for changes to take effect"
echo "   Or reload MCP servers in Cursor settings"

