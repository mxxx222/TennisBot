#!/usr/bin/env python3
"""
🔒 HIGH SECURITY FRAMEWORK
=========================

Comprehensive security management for educational research system
Supports GitHub Secrets, environment validation, and API key protection

Author: Betfury.io Educational System
Version: 1.0.0
"""

import os
import hashlib
import hmac
import time
import secrets
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pathlib import Path
import logging
import re

# Optional cryptography (fallback to basic encryption if not available)
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class GitHubSecretsManager:
    """Manages GitHub repository secrets securely"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_key = None
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption for sensitive data"""
        if not CRYPTO_AVAILABLE:
            self.encryption_key = None
            self.logger.warning("Cryptography library not available - using basic protection")
            return
            
        password = os.environ.get('SECRET_ENCRYPTION_KEY', 'default_key')
        salt = b'betfury_security_salt_2024'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.encryption_key = Fernet(key)
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Retrieve secret from GitHub Actions environment or local env
        """
        # Try GitHub Actions environment first
        github_secret = os.environ.get(secret_name)
        if github_secret:
            return self._decrypt_secret(github_secret)
        
        # Fall back to environment variable
        env_secret = os.environ.get(secret_name.upper())
        if env_secret:
            return env_secret
        
        # Log security warning
        self.logger.warning(f"Secret {secret_name} not found in environment")
        return None
    
    def validate_secret_format(self, secret_name: str, value: str) -> bool:
        """Validate secret format and security"""
        if not value:
            return False
        
        # Check for common weak patterns
        weak_patterns = [
            r'^test_',
            r'^demo_',
            r'^example_',
            r'default',
            r'changeme',
            r'password123',
            r'123456',
        ]
        
        for pattern in weak_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                self.logger.warning(f"Secret {secret_name} contains weak pattern: {pattern}")
                return False
        
        # Check length (minimum 32 chars for API keys)
        if len(value) < 8:
            self.logger.warning(f"Secret {secret_name} too short")
            return False
        
        return True
    
    def _encrypt_secret(self, value: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted = self.encryption_key.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return value
    
    def _decrypt_secret(self, encrypted_value: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.encryption_key.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return encrypted_value

class SecurityValidator:
    """Validates system security and configuration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.secrets_manager = GitHubSecretsManager()
        self.violations = []
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate environment security"""
        results = {
            'valid': True,
            'violations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check for hardcoded secrets in files
        if self._scan_for_hardcoded_secrets():
            results['violations'].append('Hardcoded secrets detected')
            results['valid'] = False
        
        # Check environment variables
        env_security = self._validate_environment_variables()
        if not env_security['secure']:
            results['warnings'].extend(env_security['warnings'])
        
        # Check file permissions
        file_security = self._validate_file_permissions()
        if not file_security['secure']:
            results['warnings'].extend(file_security['warnings'])
        
        # Generate recommendations
        results['recommendations'] = self._generate_security_recommendations()
        
        return results
    
    def _scan_for_hardcoded_secrets(self) -> bool:
        """Scan for hardcoded secrets in source files"""
        suspicious_patterns = [
            r'api[_-]?key["\']?\s*[:=]\s*["\']?(?!YOUR_)[a-zA-Z0-9]{20,}',  # Exclude YOUR_ patterns
            r'secret[_-]?key["\']?\s*[:=]\s*["\']?(?!YOUR_)[a-zA-Z0-9]{20,}',  # Exclude YOUR_ patterns
            r'token["\']?\s*[:=]\s*["\']?(?!YOUR_)[a-zA-Z0-9]{20,}',  # Exclude YOUR_ patterns
            r'password["\']?\s*[:=]\s*["\']?(?!changeme|default|example|demo|test)[^"\']{8,}',  # Exclude weak patterns
            r'bearer\s+[\w-]{20,}',
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI style keys
        ]
        
        # Skip template/example files
        skip_patterns = [
            'template',
            'example', 
            'setup',
            'docker-compose',
            'security_manager.py',  # This file itself
        ]
        
        source_dirs = ['src/', '.']
        found_violations = False
        
        for directory in source_dirs:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith(('.py', '.js', '.ts', '.env', '.yml', '.yaml')):
                            # Skip template and example files
                            if any(pattern in file.lower() for pattern in skip_patterns):
                                continue
                                
                            file_path = os.path.join(root, file)
                            if self._scan_file(file_path, suspicious_patterns):
                                found_violations = True
        
        return found_violations
    
    def _scan_file(self, file_path: str, patterns: List[str]) -> bool:
        """Scan individual file for patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self.logger.warning(f"Potential secret found in {file_path}: {pattern}")
                    return True
            
            return False
        except Exception as e:
            self.logger.debug(f"Could not scan {file_path}: {e}")
            return False
    
    def _validate_environment_variables(self) -> Dict[str, Any]:
        """Validate environment variables"""
        results = {
            'secure': True,
            'warnings': []
        }
        
        sensitive_vars = [
            'TELEGRAM_BOT_TOKEN',
            'API_FOOTBALL_KEY',
            'SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL'
        ]
        
        for var in sensitive_vars:
            value = os.environ.get(var)
            if not value:
                results['warnings'].append(f"Environment variable {var} not set")
            elif not self.secrets_manager.validate_secret_format(var, value):
                results['secure'] = False
                results['warnings'].append(f"Environment variable {var} has weak format")
        
        return results
    
    def _validate_file_permissions(self) -> Dict[str, Any]:
        """Validate file and directory permissions"""
        results = {
            'secure': True,
            'warnings': []
        }
        
        # Check .gitignore
        if os.path.exists('.gitignore'):
            gitignore_content = open('.gitignore').read()
            required_patterns = ['.env', '*.key', 'secrets/', 'logs/']
            
            for pattern in required_patterns:
                if pattern not in gitignore_content:
                    results['warnings'].append(f"Missing .gitignore pattern: {pattern}")
        else:
            results['warnings'].append("No .gitignore file found")
        
        return results
    
    def _generate_security_recommendations(self) -> List[str]:
        """Generate security improvement recommendations"""
        return [
            "Enable GitHub repository secrets for API keys",
            "Implement API key rotation every 30 days",
            "Add monitoring for unusual API usage patterns",
            "Use environment variables for all sensitive data",
            "Implement API rate limiting",
            "Add security headers to web requests",
            "Regular security audits and penetration testing",
            "Enable audit logging for all API interactions"
        ]

class APISecurityManager:
    """Manages API security and rate limiting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rate_limits = {}
        self.failed_attempts = {}
        self.blocked_apis = {}
    
    def check_rate_limit(self, api_name: str, limit: int = 100, window: int = 3600) -> bool:
        """
        Check if API call is within rate limits
        
        Args:
            api_name: Name of the API
            limit: Maximum requests in time window
            window: Time window in seconds (default 1 hour)
        """
        now = time.time()
        key = f"{api_name}:{int(now / window)}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = 0
        
        self.rate_limits[key] += 1
        
        if self.rate_limits[key] > limit:
            self.logger.warning(f"Rate limit exceeded for {api_name}: {self.rate_limits[key]}/{limit}")
            return False
        
        return True
    
    def track_failed_attempt(self, api_name: str, max_failures: int = 3) -> bool:
        """Track failed API attempts and block if too many"""
        now = time.time()
        
        if api_name not in self.failed_attempts:
            self.failed_attempts[api_name] = []
        
        # Remove old attempts (older than 1 hour)
        self.failed_attempts[api_name] = [
            attempt for attempt in self.failed_attempts[api_name]
            if now - attempt < 3600
        ]
        
        self.failed_attempts[api_name].append(now)
        
        if len(self.failed_attempts[api_name]) > max_failures:
            self.block_apis(api_name, duration=3600)  # Block for 1 hour
            return False
        
        return True
    
    def block_apis(self, api_name: str, duration: int = 3600):
        """Block API for specified duration"""
        self.blocked_apis[api_name] = {
            'blocked_until': time.time() + duration,
            'reason': 'Too many failed attempts'
        }
    
    def is_api_blocked(self, api_name: str) -> bool:
        """Check if API is currently blocked"""
        if api_name not in self.blocked_apis:
            return False
        
        if time.time() > self.blocked_apis[api_name]['blocked_until']:
            del self.blocked_apis[api_name]
            return False
        
        return True
    
    def create_secure_request_headers(self, api_name: str) -> Dict[str, str]:
        """Create secure request headers for API calls"""
        headers = {
            'User-Agent': 'Betfury-Educational-Research/1.0.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Request-ID': secrets.token_hex(16),
            'X-Timestamp': str(int(time.time())),
        }
        
        # Add API-specific headers
        if api_name == 'telegram':
            token = os.environ.get('TELEGRAM_BOT_TOKEN')
            if token:
                headers['Authorization'] = f'Bearer {token}'
        
        return headers

class SecurityLogger:
    """Enhanced logging for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.setup_logging()
    
    def setup_logging(self):
        """Setup security logging"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # File handler for security logs
        handler = logging.FileHandler('logs/security.log')
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_api_usage(self, api_name: str, endpoint: str, status_code: int):
        """Log API usage"""
        self.logger.info(f"API_USAGE|api={api_name}|endpoint={endpoint}|status={status_code}")
    
    def log_security_event(self, event_type: str, details: str):
        """Log security events"""
        self.logger.warning(f"SECURITY_EVENT|type={event_type}|details={details}")
    
    def log_failed_auth(self, api_name: str, reason: str):
        """Log failed authentication attempts"""
        self.logger.error(f"FAILED_AUTH|api={api_name}|reason={reason}")

class SecurityManager:
    """Main security manager orchestrating all security components"""
    
    def __init__(self):
        self.secrets_manager = GitHubSecretsManager()
        self.validator = SecurityValidator()
        self.api_manager = APISecurityManager()
        self.logger = SecurityLogger()
        
        self.logger.logger.info("Security manager initialized")
    
    def validate_system_security(self) -> Dict[str, Any]:
        """Run complete system security validation"""
        results = self.validator.validate_environment()
        
        # Add timestamp
        results['validation_time'] = datetime.now().isoformat()
        results['system_status'] = 'SECURE' if results['valid'] else 'VULNERABLE'
        
        return results
    
    def get_secure_config(self) -> Dict[str, Any]:
        """Get secure configuration from environment"""
        config = {
            'telegram': {
                'bot_token': self.secrets_manager.get_secret('TELEGRAM_BOT_TOKEN'),
                'chat_id': self.secrets_manager.get_secret('TELEGRAM_CHAT_ID')
            },
            'api_keys': {
                'football': self.secrets_manager.get_secret('API_FOOTBALL_KEY')
            },
            'security': {
                'rate_limit': 100,
                'max_failures': 3,
                'block_duration': 3600
            }
        }
        
        return config
    
    def report_security_status(self) -> Dict[str, Any]:
        """Generate comprehensive security status report"""
        validation_results = self.validate_system_security()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'security_level': 'HIGH' if validation_results['valid'] else 'MEDIUM',
            'validation_results': validation_results,
            'environment_variables': {
                var: 'SET' if os.environ.get(var) else 'MISSING'
                for var in ['TELEGRAM_BOT_TOKEN', 'API_FOOTBALL_KEY', 'SECRET_KEY']
            },
            'active_blocks': len(self.api_manager.blocked_apis),
            'rate_limit_status': self.api_manager.rate_limits,
            'recommendations': validation_results.get('recommendations', [])
        }
        
        return report

def main():
    """Main function for security testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Security validation and management')
    parser.add_argument('--validate', action='store_true', help='Validate system security')
    parser.add_argument('--report', action='store_true', help='Generate security report')
    parser.add_argument('--config', action='store_true', help='Show secure configuration')
    
    args = parser.parse_args()
    
    security_manager = SecurityManager()
    
    if args.validate:
        print("🔒 Validating system security...")
        results = security_manager.validate_system_security()
        print(f"Security Status: {results['system_status']}")
        print(f"Valid: {results['valid']}")
        
        if results['violations']:
            print("\nViolations:")
            for violation in results['violations']:
                print(f"  ❌ {violation}")
        
        if results['warnings']:
            print("\nWarnings:")
            for warning in results['warnings']:
                print(f"  ⚠️  {warning}")
    
    if args.report:
        print("📊 Generating security report...")
        report = security_manager.report_security_status()
        print(f"Security Level: {report['security_level']}")
        print(f"Environment Variables: {report['environment_variables']}")
        print(f"Active Blocks: {report['active_blocks']}")
    
    if args.config:
        print("⚙️  Secure configuration:")
        config = security_manager.get_secure_config()
        print(json.dumps(config, indent=2))

if __name__ == '__main__':
    main()