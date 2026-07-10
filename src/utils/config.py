"""
Configuration management for the Zambia Digital Hygiene Assessment Tool
"""

import os
from pathlib import Path
from typing import Dict, Any
from urllib.parse import quote_plus
import yaml


def load_env_file(env_file: str = '.env') -> None:
    """Load environment variables from .env file"""
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


# Load .env file on import (look for it in the project root)
_env_file = Path(__file__).parent.parent.parent / '.env'
if _env_file.exists():
    load_env_file(str(_env_file))


class Config:
    """Application configuration management"""

    def __init__(self):
        self._config = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from environment variables"""
        return {
            'app': {
                'name': 'Zambia Digital Hygiene Assessment Tool',
                'version': '1.0.0',
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                # Empty = let logging_config pick a per-user writable path.
                # A relative default like 'logs/app.log' breaks the frozen
                # .exe when launched from a read-only working directory.
                'log_file': os.getenv('LOG_FILE', ''),
                'debug': os.getenv('DEBUG', 'false').lower() == 'true'
            },
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '3306')),
                'name': os.getenv('DB_NAME', 'digital_hygiene'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20'))
            },
            'web': {
                'host': os.getenv('WEB_HOST', '127.0.0.1'),
                'port': int(os.getenv('WEB_PORT', '5000')),
                'debug': os.getenv('DEBUG', 'false').lower() == 'true',
                'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
            },
            'reports': {
                'output_dir': 'reports',
                'formats': ['json', 'csv', 'html', 'pdf'],
                'templates_dir': 'templates'
            },
            'assessment': {
                'timeout': 300,  # 5 minutes
                'max_retries': 3,
                'total_controls': 15,
                'total_possible_score': 120,
                'automated_controls': ['C01', 'C02', 'C03', 'C04', 'C05'],
                'manual_controls': ['C06', 'C07', 'C08', 'C09', 'C10',
                                    'C11', 'C12', 'C13', 'C14', 'C15'],
                'frameworks': ['NIST CSF v1.1', 'CIS Controls v8',
                               'ISO 27001:2022', 'UK Cyber Essentials'],
                'certification_tiers': {
                    'GOLD': {'min_pct': 80, 'max_critical': 0, 'validity_months': 12},
                    'SILVER': {'min_pct': 60, 'max_critical': 1, 'validity_months': 12},
                    'BRONZE': {'min_pct': 40, 'max_critical': 2, 'validity_months': 6},
                },
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

    def get_database_url(self) -> str:
        """Generate database connection URL.

        Priority:
        1. ``DATABASE_URL`` environment variable (explicit override).
        2. MySQL when the driver is installed AND authentication succeeds.
        3. SQLite fallback for local dev / testing.
        """
        # 1. Explicit override via env var (Render / Railway / Heroku inject this)
        explicit = os.environ.get('DATABASE_URL', '').strip()
        if explicit:
            # Render provides postgres:// — SQLAlchemy 2.x requires postgresql+psycopg2://
            if explicit.startswith('postgres://'):
                explicit = 'postgresql+psycopg2://' + explicit[len('postgres://'):]
            elif explicit.startswith('postgresql://'):
                explicit = 'postgresql+psycopg2://' + explicit[len('postgresql://'):]
            return explicit

        db_config = self.database
        host = db_config.get('host') or os.getenv('DB_HOST', 'localhost')
        port = db_config.get('port') or int(os.getenv('DB_PORT', '3306'))
        user = db_config.get('user') or os.getenv('DB_USER', '')
        password = db_config.get('password') or os.getenv('DB_PASSWORD', '')
        name = db_config.get('name') or os.getenv('DB_NAME', 'digital_hygiene')

        # 2. Try MySQL — only if the driver is present AND auth succeeds
        try:
            import mysql.connector
            mysql_available = True
        except ImportError:
            mysql_available = False

        if mysql_available and user:
            # Verify both TCP reachability AND successful authentication before
            # returning a MySQL URL.  A TCP probe alone is not enough — the
            # server may be running but the credentials could be wrong, which
            # causes the app to crash on first DB access.
            try:
                test_conn = mysql.connector.connect(
                    host=host,
                    port=int(port),
                    user=user,
                    password=password or '',
                    database=name,
                    connection_timeout=3,
                )
                test_conn.close()
                # Auth succeeded — build and return the SQLAlchemy URL
                if password:
                    return (f'mysql+mysqlconnector://{user}:'
                            f'{quote_plus(password)}@{host}:{port}/{name}')
                return f'mysql+mysqlconnector://{user}@{host}:{port}/{name}'
            except Exception:
                pass  # fall through to SQLite

        # 3. SQLite fallback
        db_dir = Path(__file__).parent.parent.parent / 'instance'
        db_dir.mkdir(parents=True, exist_ok=True)
        sqlite_path = db_dir / 'digital_hygiene.db'
        return f'sqlite:///{sqlite_path}'


# Global config instance
config = Config()
