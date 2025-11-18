#!/usr/bin/env python3
"""
🔐 GIT-SECRET SETUP FOR TENNIS BOT
=================================

Automated setup script for git-secret to manage sensitive files
like Telegram bot tokens, API keys, and other secrets.

This script:
- Creates GPG key if needed
- Initializes git-secret
- Sets up secret files
- Provides management commands

Author: TennisBot Advanced Analytics
"""

import subprocess
import os
import sys
from pathlib import Path
import json
import getpass

class GitSecretSetup:
    """Setup and manage git-secret for the tennis bot project"""
    
    def __init__(self):
        self.project_dir = Path('/Users/herbspotturku/sportsbot/TennisBot')
        self.email = None
        self.name = None
        self.gpg_key_id = None
        
    def check_requirements(self):
        """Check if required tools are installed"""
        print("🔍 Checking requirements...")
        
        # Check git-secret
        try:
            result = subprocess.run(['git', 'secret', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ git-secret: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ git-secret not found. Install with: brew install git-secret")
            return False
        
        # Check GPG
        try:
            result = subprocess.run(['gpg', '--version'], 
                                  capture_output=True, text=True, check=True)
            print("✅ GPG installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ GPG not found. Install with: brew install gnupg")
            return False
        
        # Check git
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, check=True)
            print("✅ Git installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git not found")
            return False
        
        return True
    
    def get_user_info(self):
        """Get user information for GPG key"""
        print("\n🔑 GPG Key Setup")
        print("=" * 50)
        
        # Get git config info first
        try:
            result = subprocess.run(['git', 'config', 'user.name'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.name = result.stdout.strip()
                print(f"📝 Found git name: {self.name}")
        except:
            pass
        
        try:
            result = subprocess.run(['git', 'config', 'user.email'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.email = result.stdout.strip()
                print(f"📧 Found git email: {self.email}")
        except:
            pass
        
        # Ask user to confirm or provide info
        if not self.name:
            self.name = input("👤 Enter your name: ").strip()
        
        if not self.email:
            self.email = input("📧 Enter your email: ").strip()
        
        print(f"\n✅ Using: {self.name} <{self.email}>")
    
    def check_existing_gpg_key(self):
        """Check if GPG key already exists"""
        try:
            result = subprocess.run(['gpg', '--list-secret-keys', '--keyid-format', 'LONG'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                print("🔑 Found existing GPG keys:")
                print(result.stdout)
                
                # Try to extract key ID
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'sec' in line and 'rsa' in line:
                        # Extract key ID from line like: sec   rsa3072/ABC123DEF456 2023-01-01
                        parts = line.split('/')
                        if len(parts) > 1:
                            key_id = parts[1].split()[0]
                            self.gpg_key_id = key_id
                            print(f"✅ Using existing key: {key_id}")
                            return True
            
            return False
            
        except subprocess.CalledProcessError:
            return False
    
    def create_gpg_key(self):
        """Create a new GPG key"""
        print("\n🔐 Creating GPG key...")
        
        # Create GPG key configuration
        gpg_config = f"""
Key-Type: RSA
Key-Length: 3072
Subkey-Type: RSA
Subkey-Length: 3072
Name-Real: {self.name}
Name-Email: {self.email}
Expire-Date: 2y
Passphrase: 
%commit
%echo done
"""
        
        # Write config to temp file
        config_file = self.project_dir / 'gpg_key_config.tmp'
        with open(config_file, 'w') as f:
            f.write(gpg_config)
        
        try:
            print("⏳ Generating GPG key (this may take a moment)...")
            result = subprocess.run(['gpg', '--batch', '--generate-key', str(config_file)], 
                                  capture_output=True, text=True, timeout=120)
            
            # Clean up temp file
            config_file.unlink()
            
            if result.returncode == 0:
                print("✅ GPG key created successfully!")
                
                # Get the key ID
                result = subprocess.run(['gpg', '--list-secret-keys', '--keyid-format', 'LONG'], 
                                      capture_output=True, text=True)
                
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'sec' in line and 'rsa' in line:
                        parts = line.split('/')
                        if len(parts) > 1:
                            key_id = parts[1].split()[0]
                            self.gpg_key_id = key_id
                            print(f"🔑 Key ID: {key_id}")
                            break
                
                return True
            else:
                print(f"❌ Failed to create GPG key: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ GPG key generation timed out")
            config_file.unlink()
            return False
        except Exception as e:
            print(f"❌ Error creating GPG key: {e}")
            if config_file.exists():
                config_file.unlink()
            return False
    
    def initialize_git_secret(self):
        """Initialize git-secret in the repository"""
        print("\n🔒 Initializing git-secret...")
        
        os.chdir(self.project_dir)
        
        try:
            # Initialize git-secret
            result = subprocess.run(['git', 'secret', 'init'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ git-secret initialized")
            else:
                print(f"⚠️ git-secret init: {result.stderr}")
            
            # Add user to git-secret
            if self.gpg_key_id:
                result = subprocess.run(['git', 'secret', 'tell', self.email], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Added {self.email} to git-secret")
                else:
                    print(f"⚠️ Error adding user: {result.stderr}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error initializing git-secret: {e}")
            return False
    
    def create_secret_files(self):
        """Create template secret files"""
        print("\n📝 Creating secret files...")
        
        # Create telegram secrets file
        telegram_secrets = {
            "TELEGRAM_BOT_TOKEN": "your_telegram_bot_token_here",
            "TELEGRAM_CHAT_ID": "your_chat_id_here",
            "OPENAI_API_KEY": "your_openai_api_key_here",
            "BETTING_API_KEY": "your_betting_api_key_here",
            "DATABASE_URL": "your_database_url_here"
        }
        
        secrets_file = self.project_dir / 'telegram_secrets.env'
        
        # Only create if doesn't exist
        if not secrets_file.exists():
            with open(secrets_file, 'w') as f:
                f.write("# Telegram Bot Secrets\n")
                f.write("# Add your actual tokens here\n\n")
                for key, value in telegram_secrets.items():
                    f.write(f"{key}={value}\n")
            
            print(f"✅ Created {secrets_file}")
        else:
            print(f"⚠️ {secrets_file} already exists")
        
        # Add to git-secret
        try:
            result = subprocess.run(['git', 'secret', 'add', 'telegram_secrets.env'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Added telegram_secrets.env to git-secret")
            else:
                print(f"⚠️ Error adding to git-secret: {result.stderr}")
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Error adding file to git-secret: {e}")
        
        # Create .gitignore entry
        gitignore_file = self.project_dir / '.gitignore'
        gitignore_content = "\n# Secret files (decrypted)\ntelegram_secrets.env\n*.env\n"
        
        if gitignore_file.exists():
            with open(gitignore_file, 'r') as f:
                existing_content = f.read()
            
            if 'telegram_secrets.env' not in existing_content:
                with open(gitignore_file, 'a') as f:
                    f.write(gitignore_content)
                print("✅ Updated .gitignore")
        else:
            with open(gitignore_file, 'w') as f:
                f.write(gitignore_content)
            print("✅ Created .gitignore")
    
    def encrypt_secrets(self):
        """Encrypt the secret files"""
        print("\n🔒 Encrypting secrets...")
        
        try:
            result = subprocess.run(['git', 'secret', 'hide'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Secrets encrypted successfully!")
                print("📁 Encrypted files:")
                
                # List encrypted files
                result = subprocess.run(['git', 'secret', 'list'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            print(f"   🔐 {line.strip()}")
            else:
                print(f"❌ Error encrypting secrets: {result.stderr}")
                return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error encrypting secrets: {e}")
            return False
    
    def create_management_script(self):
        """Update the git-secret management script"""
        print("\n📜 Creating management script...")
        
        script_content = f'''#!/bin/bash
# Git-Secret Management for Tennis Bot
# Generated automatically by setup_git_secrets.py

echo "🔐 Tennis Bot Git-Secret Manager"
echo "================================"

case "$1" in
    "reveal"|"r")
        echo "🔓 Revealing secrets..."
        git secret reveal
        if [ $? -eq 0 ]; then
            echo "✅ Secrets decrypted successfully"
            echo "📁 Available files:"
            ls -la *.env 2>/dev/null || echo "   No .env files found"
        else
            echo "❌ Failed to decrypt secrets"
        fi
        ;;
    "hide"|"h")
        echo "🔒 Hiding secrets..."
        git secret hide
        if [ $? -eq 0 ]; then
            echo "✅ Secrets encrypted successfully"
        else
            echo "❌ Failed to encrypt secrets"
        fi
        ;;
    "list"|"l")
        echo "📋 Encrypted files:"
        git secret list
        ;;
    "status"|"s")
        echo "📊 Git-secret status:"
        echo "  GPG Key: {self.gpg_key_id or 'Not found'}"
        echo "  Email: {self.email or 'Not set'}"
        echo "  Encrypted files:"
        git secret list | sed 's/^/    /'
        ;;
    "add")
        if [ -z "$2" ]; then
            echo "Usage: $0 add <filename>"
            exit 1
        fi
        echo "➕ Adding $2 to git-secret..."
        git secret add "$2"
        echo "🔒 Encrypting..."
        git secret hide
        ;;
    "edit")
        echo "✏️ Editing secrets..."
        git secret reveal
        ${os.getenv('EDITOR', 'nano')} telegram_secrets.env
        git secret hide
        echo "✅ Secrets updated and encrypted"
        ;;
    "telegram")
        echo "🤖 Setting up Telegram bot token..."
        git secret reveal
        echo "Enter your Telegram bot token:"
        read -s TOKEN
        sed -i.bak "s/TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=$TOKEN/" telegram_secrets.env
        git secret hide
        echo "✅ Telegram token updated"
        ;;
    *)
        echo "Usage: $0 {{reveal|hide|list|status|add|edit|telegram}}"
        echo ""
        echo "Commands:"
        echo "  reveal/r    - Decrypt secrets"
        echo "  hide/h      - Encrypt secrets"
        echo "  list/l      - List encrypted files"
        echo "  status/s    - Show git-secret status"
        echo "  add <file>  - Add file to git-secret"
        echo "  edit        - Edit secrets file"
        echo "  telegram    - Set Telegram bot token"
        echo ""
        echo "Examples:"
        echo "  $0 reveal              # Decrypt secrets"
        echo "  $0 telegram            # Set bot token"
        echo "  $0 add config.json     # Add new secret file"
        ;;
esac
'''
        
        script_file = self.project_dir / 'git-secret-tools.sh'
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # Make executable
        script_file.chmod(0o755)
        
        print(f"✅ Created {script_file}")
        print("📝 Usage: ./git-secret-tools.sh reveal")
    
    def show_usage_instructions(self):
        """Show usage instructions"""
        print("\n" + "="*60)
        print("🎉 GIT-SECRET SETUP COMPLETE!")
        print("="*60)
        
        print("\n📋 What was created:")
        print("   🔑 GPG key for encryption")
        print("   🔒 git-secret initialized")
        print("   📝 telegram_secrets.env template")
        print("   🔐 Encrypted secret files")
        print("   📜 Management script: git-secret-tools.sh")
        
        print("\n🚀 Next Steps:")
        print("1. Edit your secrets:")
        print("   ./git-secret-tools.sh edit")
        print("")
        print("2. Set your Telegram bot token:")
        print("   ./git-secret-tools.sh telegram")
        print("")
        print("3. Reveal secrets when needed:")
        print("   ./git-secret-tools.sh reveal")
        print("")
        print("4. Hide secrets after editing:")
        print("   ./git-secret-tools.sh hide")
        
        print("\n🔐 Security Notes:")
        print("   ✅ Encrypted files (.secret) are safe to commit")
        print("   ❌ Never commit decrypted .env files")
        print("   🔑 Keep your GPG key secure")
        print("   📝 Share GPG public key with team members")
        
        print(f"\n🔑 Your GPG Key ID: {self.gpg_key_id}")
        print(f"📧 Email: {self.email}")
        
        print("\n💡 Common Commands:")
        print("   ./git-secret-tools.sh status    # Check status")
        print("   ./git-secret-tools.sh list      # List encrypted files")
        print("   ./git-secret-tools.sh reveal    # Decrypt secrets")
        print("   ./git-secret-tools.sh hide      # Encrypt secrets")

def main():
    """Main setup function"""
    print("🔐 GIT-SECRET SETUP FOR TENNIS BOT")
    print("=" * 50)
    print("This script will set up git-secret to securely manage")
    print("your Telegram bot tokens and other sensitive data.")
    print("=" * 50)
    
    setup = GitSecretSetup()
    
    # Check requirements
    if not setup.check_requirements():
        print("\n❌ Requirements not met. Please install missing tools.")
        return False
    
    # Get user information
    setup.get_user_info()
    
    # Check for existing GPG key or create new one
    if not setup.check_existing_gpg_key():
        if not setup.create_gpg_key():
            print("\n❌ Failed to create GPG key")
            return False
    
    # Initialize git-secret
    if not setup.initialize_git_secret():
        print("\n❌ Failed to initialize git-secret")
        return False
    
    # Create secret files
    setup.create_secret_files()
    
    # Encrypt secrets
    if not setup.encrypt_secrets():
        print("\n❌ Failed to encrypt secrets")
        return False
    
    # Create management script
    setup.create_management_script()
    
    # Show usage instructions
    setup.show_usage_instructions()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Setup completed successfully!")
        else:
            print("\n❌ Setup failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
