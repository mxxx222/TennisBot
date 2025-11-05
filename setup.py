#!/usr/bin/env python3
"""
Configuration and Environment Setup Script
==========================================

This script helps set up the educational research environment
and validates configuration.

DISCLAIMER: This is for educational/research purposes only.
"""

import os
import sys
import yaml
from pathlib import Path

def setup_environment():
    """Setup the educational research environment"""
    print("🔧 Setting up Betfury.io Educational Research Environment")
    print("⚠️  FOR EDUCATIONAL PURPOSES ONLY")
    
    # Create necessary directories
    directories = [
        "data",
        "logs", 
        "models",
        "cache"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Copy config template if config doesn't exist
    config_path = Path("config/config.yaml")
    config_template = Path("config/config_template.yaml")
    
    if not config_path.exists() and config_template.exists():
        config_template.rename(config_path)
        print("✅ Created config file from template")
        print("   📝 Please review config/config.yaml before running")
    
    # Create .env.example file
    env_example = """# Educational Research Environment Variables
# Copy this file to .env and configure as needed

# Research Settings
RESEARCH_MODE=true
EDUCATIONAL_ONLY=true
DEBUG=false

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# API Keys (Optional)
API_FOOTBALL_KEY=your_api_key_here

# Security
SECRET_KEY=change_this_in_production
ENCRYPT_SECRETS=false

# Database (Optional)
DATABASE_URL=postgresql://user:password@localhost:5432/research

# Redis (Optional)  
REDIS_URL=redis://localhost:6379/0
"""
    
    if not Path(".env.example").exists():
        Path(".env.example").write_text(env_example)
        print("✅ Created .env.example file")
        print("   📝 Copy to .env and configure as needed")
    
    print("\n🎉 Environment setup complete!")
    print("\nNext steps:")
    print("1. Review config/config.yaml")
    print("2. Copy .env.example to .env and configure")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Run in demo mode: python main.py --mode analyze --duration 5")
    
    return True

def validate_config():
    """Validate configuration file"""
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        print("❌ config.yaml not found. Please run setup first.")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = [
            'rate_limit',
            'scraping', 
            'ml_config',
            'research'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️  Missing configuration sections: {missing_sections}")
            return False
        
        print("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import aiohttp
        import selenium
        import sklearn
        import pandas
        print("✅ All required dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install with: pip install -r requirements.txt")
        return False

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Betfury Educational Research Setup")
    parser.add_argument('--setup', action='store_true', help='Setup environment')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        # Run all checks by default
        args.setup = True
        args.validate = True
        args.check_deps = True
    
    success = True
    
    if args.setup:
        if not setup_environment():
            success = False
    
    if args.validate:
        if not validate_config():
            success = False
    
    if args.check_deps:
        if not check_dependencies():
            success = False
    
    if success:
        print("\n🎉 All setup checks passed!")
        print("Ready to run educational research system.")
    else:
        print("\n⚠️  Some setup issues found. Please review above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())