#!/usr/bin/env python3
"""
🔐 SIMPLE SECRETS MANAGER FOR TENNIS BOT
========================================

A simple, working solution for managing Telegram bot secrets
without the complexity of git-secret.

This approach:
- Uses environment variables
- Creates encrypted backup files
- Provides easy management commands
- Works reliably without GPG issues

Author: TennisBot Advanced Analytics
"""

import os
import sys
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
import getpass

class SimpleSecretsManager:
    """Simple secrets manager using environment variables and encryption"""
    
    def __init__(self):
        self.project_dir = Path('/Users/herbspotturku/sportsbot/TennisBot')
        self.secrets_file = self.project_dir / 'telegram_secrets.env'
        self.encrypted_file = self.project_dir / 'secrets.encrypted'
        self.key_file = self.project_dir / '.secret_key'
        
        # Ensure key exists
        self._ensure_key()
    
    def _ensure_key(self):
        """Ensure encryption key exists"""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            print("🔑 Created new encryption key")
    
    def _get_key(self):
        """Get encryption key"""
        with open(self.key_file, 'rb') as f:
            return f.read()
    
    def create_secrets_template(self):
        """Create secrets template file"""
        template = """# 🤖 TELEGRAM BOT SECRETS
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

# Database (optional)
DATABASE_URL=your_database_url_here
"""
        
        if not self.secrets_file.exists():
            with open(self.secrets_file, 'w') as f:
                f.write(template)
            print(f"✅ Created secrets template: {self.secrets_file}")
        else:
            print(f"⚠️ Secrets file already exists: {self.secrets_file}")
    
    def encrypt_secrets(self):
        """Encrypt the secrets file"""
        if not self.secrets_file.exists():
            print("❌ No secrets file found. Create one first.")
            return False
        
        try:
            # Read secrets
            with open(self.secrets_file, 'r') as f:
                content = f.read()
            
            # Encrypt
            key = self._get_key()
            fernet = Fernet(key)
            encrypted_content = fernet.encrypt(content.encode())
            
            # Save encrypted file
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_content)
            
            print(f"✅ Secrets encrypted to: {self.encrypted_file}")
            
            # Remove original (optional)
            response = input("🗑️ Remove decrypted file? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                self.secrets_file.unlink()
                print("🗑️ Decrypted file removed")
            
            return True
            
        except Exception as e:
            print(f"❌ Error encrypting secrets: {e}")
            return False
    
    def decrypt_secrets(self):
        """Decrypt the secrets file"""
        if not self.encrypted_file.exists():
            print("❌ No encrypted secrets file found")
            return False
        
        try:
            # Read encrypted content
            with open(self.encrypted_file, 'rb') as f:
                encrypted_content = f.read()
            
            # Decrypt
            key = self._get_key()
            fernet = Fernet(key)
            decrypted_content = fernet.decrypt(encrypted_content)
            
            # Save decrypted file
            with open(self.secrets_file, 'w') as f:
                f.write(decrypted_content.decode())
            
            print(f"✅ Secrets decrypted to: {self.secrets_file}")
            print(f"📝 To load: source {self.secrets_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error decrypting secrets: {e}")
            return False
    
    def set_telegram_token(self):
        """Set Telegram bot token"""
        # Decrypt first
        if not self.secrets_file.exists():
            if self.encrypted_file.exists():
                self.decrypt_secrets()
            else:
                self.create_secrets_template()
        
        print("🤖 Setting Telegram bot token...")
        token = getpass.getpass("Enter your bot token (hidden): ").strip()
        
        if not token:
            print("❌ No token provided")
            return False
        
        try:
            # Read current content
            with open(self.secrets_file, 'r') as f:
                content = f.read()
            
            # Update token
            lines = content.split('\n')
            updated = False
            
            for i, line in enumerate(lines):
                if line.startswith('TELEGRAM_BOT_TOKEN='):
                    lines[i] = f'TELEGRAM_BOT_TOKEN={token}'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'TELEGRAM_BOT_TOKEN={token}')
            
            # Write back
            with open(self.secrets_file, 'w') as f:
                f.write('\n'.join(lines))
            
            print("✅ Telegram token updated")
            
            # Re-encrypt
            self.encrypt_secrets()
            return True
            
        except Exception as e:
            print(f"❌ Error setting token: {e}")
            return False
    
    def load_secrets_to_env(self):
        """Load secrets into environment variables"""
        if not self.secrets_file.exists():
            if self.encrypted_file.exists():
                self.decrypt_secrets()
            else:
                print("❌ No secrets file found")
                return False
        
        try:
            with open(self.secrets_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            
            print("✅ Secrets loaded into environment")
            print("🤖 Available variables:")
            
            secret_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'OPENAI_API_KEY']
            for var in secret_vars:
                value = os.getenv(var, 'Not set')
                if value != 'Not set' and value != f'your_{var.lower()}_here':
                    print(f"   {var}: {value[:10]}..." if len(value) > 10 else f"   {var}: {value}")
                else:
                    print(f"   {var}: Not set")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading secrets: {e}")
            return False
    
    def show_status(self):
        """Show current status"""
        print("📊 Simple Secrets Manager Status")
        print("=" * 40)
        
        # Check files
        print(f"📁 Secrets file: {'✅' if self.secrets_file.exists() else '❌'} {self.secrets_file}")
        print(f"🔐 Encrypted file: {'✅' if self.encrypted_file.exists() else '❌'} {self.encrypted_file}")
        print(f"🔑 Key file: {'✅' if self.key_file.exists() else '❌'} {self.key_file}")
        
        # Check environment
        print(f"\n🌍 Environment variables:")
        secret_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'OPENAI_API_KEY']
        for var in secret_vars:
            value = os.getenv(var)
            if value and value != f'your_{var.lower()}_here':
                print(f"   {var}: ✅ Set")
            else:
                print(f"   {var}: ❌ Not set")
    
    def edit_secrets(self):
        """Edit secrets file"""
        # Decrypt first
        if not self.secrets_file.exists():
            if self.encrypted_file.exists():
                self.decrypt_secrets()
            else:
                self.create_secrets_template()
        
        # Open editor
        editor = os.getenv('EDITOR', 'nano')
        os.system(f'{editor} {self.secrets_file}')
        
        # Re-encrypt
        print("🔒 Re-encrypting secrets...")
        self.encrypt_secrets()

def main():
    """Main function"""
    print("🔐 SIMPLE SECRETS MANAGER FOR TENNIS BOT")
    print("=" * 50)
    
    manager = SimpleSecretsManager()
    
    if len(sys.argv) < 2:
        print("Usage: python simple_secrets.py {create|encrypt|decrypt|telegram|load|status|edit}")
        print("")
        print("Commands:")
        print("  create    - Create secrets template")
        print("  encrypt   - Encrypt secrets file")
        print("  decrypt   - Decrypt secrets file")
        print("  telegram  - Set Telegram bot token")
        print("  load      - Load secrets into environment")
        print("  status    - Show current status")
        print("  edit      - Edit secrets file")
        print("")
        print("Examples:")
        print("  python simple_secrets.py create")
        print("  python simple_secrets.py telegram")
        print("  python simple_secrets.py load")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        manager.create_secrets_template()
    elif command == 'encrypt':
        manager.encrypt_secrets()
    elif command == 'decrypt':
        manager.decrypt_secrets()
    elif command == 'telegram':
        manager.set_telegram_token()
    elif command == 'load':
        manager.load_secrets_to_env()
    elif command == 'status':
        manager.show_status()
    elif command == 'edit':
        manager.edit_secrets()
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
