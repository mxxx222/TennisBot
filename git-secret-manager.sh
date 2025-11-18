#!/bin/bash
# 🔐 GIT-SECRET MANAGER FOR TENNIS BOT
# ====================================
# Enhanced git-secret management script with better error handling

set -e  # Exit on error

PROJECT_DIR="/Users/herbspotturku/sportsbot/TennisBot"
SECRETS_FILE="telegram_secrets.env"

echo "🔐 Tennis Bot Git-Secret Manager"
echo "================================"

# Function to check if git-secret is initialized
check_git_secret() {
    if [ ! -d ".gitsecret" ]; then
        echo "❌ git-secret not initialized. Run: git secret init"
        exit 1
    fi
}

# Function to reveal secrets
reveal_secrets() {
    echo "🔓 Revealing secrets..."
    
    if git secret reveal -f 2>/dev/null; then
        echo "✅ Secrets decrypted successfully"
        if [ -f "$SECRETS_FILE" ]; then
            echo "📁 Available: $SECRETS_FILE"
            echo "📝 To load in shell: source $SECRETS_FILE"
        fi
    else
        echo "⚠️ Attempting alternative decryption..."
        # Try direct GPG decryption
        if [ -f "${SECRETS_FILE}.secret" ]; then
            gpg --quiet --batch --yes --decrypt "${SECRETS_FILE}.secret" > "$SECRETS_FILE" 2>/dev/null || {
                echo "❌ Failed to decrypt secrets"
                echo "💡 Try: gpg --decrypt ${SECRETS_FILE}.secret > $SECRETS_FILE"
                exit 1
            }
            echo "✅ Secrets decrypted with direct GPG"
        else
            echo "❌ No encrypted secrets file found"
            exit 1
        fi
    fi
}

# Function to hide secrets
hide_secrets() {
    echo "🔒 Hiding secrets..."
    
    if [ ! -f "$SECRETS_FILE" ]; then
        echo "❌ No secrets file found: $SECRETS_FILE"
        exit 1
    fi
    
    if git secret hide 2>/dev/null; then
        echo "✅ Secrets encrypted successfully"
        echo "🗑️ Removing decrypted file..."
        rm -f "$SECRETS_FILE"
    else
        echo "⚠️ git secret hide failed, trying direct GPG encryption..."
        # Get GPG key ID
        KEY_ID=$(gpg --list-secret-keys --keyid-format LONG | grep "sec" | head -1 | awk -F'/' '{print $2}' | awk '{print $1}')
        if [ -n "$KEY_ID" ]; then
            gpg --trust-model always --encrypt -r "$KEY_ID" --armor --output "${SECRETS_FILE}.secret" "$SECRETS_FILE"
            echo "✅ Secrets encrypted with direct GPG"
            rm -f "$SECRETS_FILE"
        else
            echo "❌ No GPG key found for encryption"
            exit 1
        fi
    fi
}

# Function to edit secrets
edit_secrets() {
    echo "✏️ Editing secrets..."
    reveal_secrets
    
    # Use preferred editor
    EDITOR=${EDITOR:-nano}
    $EDITOR "$SECRETS_FILE"
    
    echo "🔒 Re-encrypting secrets..."
    hide_secrets
    echo "✅ Secrets updated and encrypted"
}

# Function to set Telegram token
set_telegram_token() {
    echo "🤖 Setting Telegram bot token..."
    reveal_secrets
    
    echo "Enter your Telegram bot token (from @BotFather):"
    read -s TOKEN
    
    if [ -n "$TOKEN" ]; then
        # Update the token in the file
        if grep -q "TELEGRAM_BOT_TOKEN=" "$SECRETS_FILE"; then
            sed -i.bak "s/TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=$TOKEN/" "$SECRETS_FILE"
        else
            echo "TELEGRAM_BOT_TOKEN=$TOKEN" >> "$SECRETS_FILE"
        fi
        
        hide_secrets
        echo "✅ Telegram token updated and encrypted"
    else
        echo "❌ No token provided"
        hide_secrets
    fi
}

# Function to show status
show_status() {
    echo "📊 Git-secret status:"
    
    # Check if initialized
    if [ -d ".gitsecret" ]; then
        echo "  ✅ git-secret initialized"
    else
        echo "  ❌ git-secret not initialized"
        return
    fi
    
    # Show GPG key
    KEY_INFO=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep "sec" | head -1 || echo "No key found")
    echo "  🔑 GPG Key: $KEY_INFO"
    
    # Show users
    if [ -f ".gitsecret/keys/pubring.kbx" ]; then
        echo "  👥 Authorized users:"
        gpg --homedir .gitsecret/keys --list-keys --keyid-format LONG 2>/dev/null | grep "uid" | sed 's/uid.*] /    /' || echo "    None found"
    fi
    
    # Show encrypted files
    echo "  📁 Encrypted files:"
    if git secret list >/dev/null 2>&1; then
        git secret list | sed 's/^/    /'
    else
        ls -la *.secret 2>/dev/null | awk '{print "    " $9}' || echo "    None found"
    fi
    
    # Show decrypted files
    echo "  🔓 Decrypted files:"
    ls -la *.env 2>/dev/null | awk '{print "    " $9}' || echo "    None found"
}

# Function to setup git-secret
setup_git_secret() {
    echo "🔧 Setting up git-secret..."
    
    # Initialize if needed
    if [ ! -d ".gitsecret" ]; then
        git secret init
        echo "✅ git-secret initialized"
    fi
    
    # Check for GPG key
    if ! gpg --list-secret-keys >/dev/null 2>&1; then
        echo "🔑 Creating GPG key..."
        # Get git user info
        GIT_NAME=$(git config user.name || echo "Tennis Bot User")
        GIT_EMAIL=$(git config user.email || echo "user@example.com")
        
        gpg --batch --passphrase '' --quick-gen-key "$GIT_NAME <$GIT_EMAIL>" rsa3072
        echo "✅ GPG key created"
    fi
    
    # Add user to git-secret
    GIT_EMAIL=$(git config user.email)
    if [ -n "$GIT_EMAIL" ]; then
        git secret tell "$GIT_EMAIL" 2>/dev/null || echo "⚠️ User already added or error adding user"
    fi
    
    # Create secrets file if it doesn't exist
    if [ ! -f "$SECRETS_FILE" ] && [ ! -f "${SECRETS_FILE}.secret" ]; then
        echo "📝 Creating secrets template..."
        cat > "$SECRETS_FILE" << 'EOF'
# 🤖 TELEGRAM BOT SECRETS
# =======================
# Add your actual tokens here

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# OpenAI API (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Other APIs (optional)
BETTING_API_KEY=your_betting_api_key_here
ODDS_API_KEY=your_odds_api_key_here
EOF
        
        git secret add "$SECRETS_FILE"
        hide_secrets
        echo "✅ Secrets template created and encrypted"
    fi
    
    echo "✅ git-secret setup complete!"
}

# Main command handling
case "$1" in
    "reveal"|"r")
        check_git_secret
        reveal_secrets
        ;;
    "hide"|"h")
        check_git_secret
        hide_secrets
        ;;
    "list"|"l")
        echo "📋 Encrypted files:"
        if git secret list >/dev/null 2>&1; then
            git secret list
        else
            ls -la *.secret 2>/dev/null || echo "No encrypted files found"
        fi
        ;;
    "status"|"s")
        show_status
        ;;
    "edit"|"e")
        check_git_secret
        edit_secrets
        ;;
    "telegram"|"t")
        check_git_secret
        set_telegram_token
        ;;
    "setup")
        setup_git_secret
        ;;
    "load")
        check_git_secret
        reveal_secrets
        echo "🔄 Loading secrets into environment..."
        if [ -f "$SECRETS_FILE" ]; then
            echo "Run: source $SECRETS_FILE"
            echo "Or: export \$(cat $SECRETS_FILE | xargs)"
        fi
        ;;
    *)
        echo "Usage: $0 {reveal|hide|list|status|edit|telegram|setup|load}"
        echo ""
        echo "Commands:"
        echo "  reveal/r     - Decrypt secrets to $SECRETS_FILE"
        echo "  hide/h       - Encrypt secrets"
        echo "  list/l       - List encrypted files"
        echo "  status/s     - Show git-secret status"
        echo "  edit/e       - Edit secrets file"
        echo "  telegram/t   - Set Telegram bot token"
        echo "  setup        - Initialize git-secret"
        echo "  load         - Reveal and show how to load secrets"
        echo ""
        echo "Examples:"
        echo "  $0 setup              # First-time setup"
        echo "  $0 telegram           # Set bot token"
        echo "  $0 reveal             # Decrypt secrets"
        echo "  $0 edit               # Edit secrets"
        echo "  $0 load               # Load into environment"
        echo ""
        echo "🔐 Git-Secret Management for Tennis Bot"
        ;;
esac
