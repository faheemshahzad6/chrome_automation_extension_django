import logging
import sys
from datetime import datetime
import os
import glob
from pathlib import Path
import json
from typing import List, Dict, Any


def get_latest_log_file() -> str:
    """Get the most recent network log file"""
    log_dir = Path("network_logs")
    files = glob.glob(str(log_dir / "network_log_*.jsonl"))
    if not files:
        return None
    return max(files, key=os.path.getctime)


def clean_old_logs(keep_latest: bool = True) -> int:
    """Delete old log files, optionally keeping the latest one"""
    log_dir = Path("network_logs")
    files = glob.glob(str(log_dir / "network_log_*.jsonl"))
    if not files:
        return 0

    if keep_latest:
        latest = max(files, key=os.path.getctime)
        files.remove(latest)

    for file in files:
        try:
            os.remove(file)
        except:
            pass

    return len(files)


def read_log_file(file_path: str) -> List[Dict[str, Any]]:
    """Read and parse a JSONL log file"""
    logs = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except:
                continue
    return logs


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """Set up a logger with both file and console handlers"""

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Format for the logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log file is specified)
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Create file handler
        file_handler = logging.FileHandler(
            log_dir / f"{log_file}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class AutomationLogger:
    """Singleton logger class for automation tasks"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutomationLogger, cls).__new__(cls)
            cls._logger = setup_logger('automation', 'automation')
        return cls._instance

    @classmethod
    def debug(cls, message: str, *args, **kwargs):
        cls._logger.debug(message, *args, **kwargs)

    @classmethod
    def info(cls, message: str, *args, **kwargs):
        cls._logger.info(message, *args, **kwargs)

    @classmethod
    def warning(cls, message: str, *args, **kwargs):
        cls._logger.warning(message, *args, **kwargs)

    @classmethod
    def error(cls, message: str, *args, **kwargs):
        cls._logger.error(message, *args, **kwargs)

    @classmethod
    def critical(cls, message: str, *args, **kwargs):
        cls._logger.critical(message, *args, **kwargs)


# Create global logger instance
logger = AutomationLogger()