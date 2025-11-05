"""
Configuration Loader for Educational Betting System
Comprehensive configuration management with environment variable support

⚠️ EDUCATIONAL USE ONLY - NO REAL MONEY BETTING ⚠️
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import re

class ConfigLoader:
    """Load and manage configuration for educational betting system"""
    
    def __init__(self, config_path: str = "config/educational_betting_config.yaml"):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        
        try:
            # Check if config file exists
            if not Path(self.config_path).exists():
                self.logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
            
            # Load base configuration
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # Process environment variables
            self._process_environment_variables()
            
            # Apply environment-specific overrides
            self._apply_environment_overrides()
            
            # Validate configuration
            self._validate_config()
            
            self.logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return self._get_default_config()
    
    def _process_environment_variables(self):
        """Replace environment variable placeholders"""
        
        def replace_env_vars(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    obj[key] = replace_env_vars(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    obj[i] = replace_env_vars(item)
            elif isinstance(obj, str):
                # Replace ${VAR_NAME} with environment variable value
                obj = re.sub(r'\$\{([^}]+)\}', self._get_env_var, obj)
            return obj
        
        self.config = replace_env_vars(self.config)
    
    def _get_env_var(self, match) -> str:
        """Get environment variable value"""
        var_name = match.group(1)
        return os.getenv(var_name, f"${{{var_name}}}")  # Return placeholder if not found
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        
        environments = self.config.get('environments', {})
        if self.environment in environments:
            overrides = environments[self.environment]
            self._deep_merge(self.config, overrides)
            self.logger.info(f"Applied {self.environment} environment overrides")
    
    def _deep_merge(self, base: dict, override: dict):
        """Deep merge override configuration into base"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _validate_config(self):
        """Validate configuration requirements"""
        
        required_sections = [
            'system_mode',
            'safety', 
            'patterns',
            'storage',
            'logging'
        ]
        
        missing_sections = [section for section in required_sections 
                          if section not in self.config]
        
        if missing_sections:
            raise ValueError(f"Missing required configuration sections: {missing_sections}")
        
        # Validate educational mode is enabled
        if not self.config.get('system_mode', {}).get('educational_mode', False):
            raise ValueError("Educational mode must be enabled for safety")
        
        self.logger.info("Configuration validation passed")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file loading fails"""
        
        return {
            'system_mode': {
                'educational_mode': True,
                'enable_real_api': False,
                'mock_data_mode': True,
                'enable_notifications': False
            },
            'safety': {
                'max_daily_signals': 10,
                'min_confidence_threshold': 0.75,
                'max_odds_range': [1.10, 2.00],
                'educational_mode': True
            },
            'patterns': {
                'enabled': ['LateGameProtection', 'DefensiveStalemate', 'DominantFavorite']
            },
            'storage': {
                'educational_signals_dir': 'educational_signals',
                'data_retention_days': 30
            },
            'logging': {
                'level': 'INFO',
                'console_enabled': True,
                'file_enabled': True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'safety.max_daily_signals')"""
        
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_safety_config(self) -> Dict[str, Any]:
        """Get safety configuration section"""
        return self.get('safety', {})
    
    def get_pattern_config(self) -> Dict[str, Any]:
        """Get pattern configuration section"""
        return self.get('patterns', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration section"""
        return self.get('api', {})
    
    def is_educational_mode(self) -> bool:
        """Check if educational mode is enabled"""
        return self.get('system_mode.educational_mode', True)
    
    def get_update_interval(self) -> int:
        """Get update interval in seconds"""
        return self.get('performance.update_interval_seconds', 60)
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get('logging', {})
    
    def save_config(self, config_data: Dict[str, Any], backup: bool = True):
        """Save configuration to file"""
        
        try:
            if backup and Path(self.config_path).exists():
                backup_path = f"{self.config_path}.backup"
                Path(self.config_path).rename(backup_path)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def reload_config(self) -> Dict[str, Any]:
        """Reload configuration from file"""
        self.config = {}
        return self.load_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging"""
        
        return {
            'educational_mode': self.is_educational_mode(),
            'update_interval': self.get_update_interval(),
            'safety_enabled': bool(self.get_safety_config()),
            'patterns_enabled': len(self.get_pattern_config().get('enabled', [])),
            'environment': self.environment,
            'config_file': self.config_path
        }

def create_sample_config():
    """Create a sample configuration file for users"""
    
    sample_config = {
        'system_mode': {
            'educational_mode': True,
            'enable_real_api': False,
            'mock_data_mode': True
        },
        'safety': {
            'max_daily_signals': 10,
            'min_confidence_threshold': 0.75,
            'educational_mode': True
        },
        'patterns': {
            'enabled': ['LateGameProtection', 'DefensiveStalemate']
        }
    }
    
    # Create config directory if it doesn't exist
    Path('config').mkdir(exist_ok=True)
    
    with open('config/sample_config.yaml', 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    print("Sample configuration created: config/sample_config.yaml")

if __name__ == "__main__":
    # Example usage
    loader = ConfigLoader()
    config = loader.load_config()
    
    print("Configuration Summary:")
    summary = loader.get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Create sample config
    create_sample_config()