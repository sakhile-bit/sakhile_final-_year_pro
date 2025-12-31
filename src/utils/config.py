"""
Configuration management for the Zambia Digital Hygiene Assessment Tool
"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml


class Config:
    """Application configuration management"""

    def __init__(self):
        self._config = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'app': {
                'name': 'Zambia Digital Hygiene Assessment Tool',
                'version': '2.0.0',
                'log_level': 'INFO',
                'log_file': 'logs/app.log',
                'debug': False
            },
            'database': {
                'host': 'localhost',
                'port': 3306,
                'name': 'digital_hygiene',
                'user': 'root',
                'password': '',
                'pool_size': 10,
                'max_overflow': 20
            },
            'web': {
                'host': 'localhost',
                'port': 5000,
                'debug': True,
                'secret_key': 'dev-secret-key-change-in-production'
            },
            'reports': {
                'output_dir': 'reports',
                'formats': ['json', 'csv', 'html', 'pdf'],
                'templates_dir': 'templates'
            },
            'assessment': {
                'timeout': 300,  # 5 minutes
                'max_retries': 3
            }
        }

    def load_from_file(self, config_file: str) -> None:
        """Load configuration from YAML file"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                self._merge_config(self._config, file_config)

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default=None):
        """Get configuration value by dot-separated key"""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def app(self):
        """Application configuration"""
        return self._config['app']

    @property
    def database(self):
        """Database configuration"""
        return self._config['database']

    @property
    def web(self):
        """Web configuration"""
        return self._config['web']

    @property
    def reports(self):
        """Reports configuration"""
        return self._config['reports']

    @property
    def assessment(self):
        """Assessment configuration"""
        return self._config['assessment']


# Global config instance
config = Config()
