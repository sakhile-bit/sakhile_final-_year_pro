"""
Logging configuration for the Zambia Digital Hygiene Assessment Tool
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
from .config import config


def _default_log_file() -> str:
    """Per-user writable log path (same folder as the local database).

    The app may run from a read-only location (installed .exe, network
    share), so logs must never be written relative to the working dir.
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    return str(base / "ZambiaDigitalHygiene" / "logs" / "app.log")


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Set up logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console: Whether to log to console

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("zambia_digital_hygiene")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler — never let an unwritable log location kill the app;
    # fall back to console-only logging instead.
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            logger.warning("log file %s not writable — console only",
                           log_file)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module

    Args:
        name: Module name

    Returns:
        Logger instance
    """
    return logging.getLogger(f"zambia_digital_hygiene.{name}")


# Initialize global logger
logger = setup_logging(
    log_level=config.app.get('log_level', 'INFO'),
    log_file=config.app.get('log_file') or _default_log_file()
)
