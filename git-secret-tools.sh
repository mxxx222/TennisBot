#!/bin/bash
# Git-Secret Tools for Educational Betting System
# This script provides convenient commands for managing encrypted secrets

echo "🔐 Git-Secret Tools for Educational Betting System"
echo "================================================"

case "$1" in
    "reveal"|"r")
        echo "🔓 Revealing secrets..."
        gpg --no-tty --quiet --decrypt telegram_secrets.env.secret > telegram_secrets.env
        echo "✅ Secrets decrypted to telegram_secrets.env"
        ;;
    "hide"|"h")
        echo "🔒 Hiding secrets..."
        git secret hide
        echo "✅ Secrets encrypted"
        ;;
    "list"|"l")
        echo "📋 Current secrets files:"
        git secret list
        ;;
    "status"|"s")
        echo "📊 Git-secret status:"
        echo "  - Available users: $(git secret tell 2>/dev/null | wc -l)"
        echo "  - Encrypted files:"
        git secret list | sed 's/^/    /'
        ;;
    "gpg-keys")
        echo "🔑 Available GPG keys:"
        gpg --list-secret-keys --keyid-format LONG | grep -A2 "^sec"
        ;;
    *)
        echo "Usage: $0 {reveal|hide|list|status|gpg-keys}"
        echo ""
        echo "Commands:"
        echo "  reveal/r    - Decrypt secrets to telegram_secrets.env"
        echo "  hide/h      - Encrypt secrets"
        echo "  list/l      - List encrypted files"
        echo "  status/s    - Show git-secret status"
        echo "  gpg-keys    - Show available GPG keys"
        echo ""
        echo "Example: $0 reveal"
        ;;
esac