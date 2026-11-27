import re
import logging
import sys
from app.core.config import settings

# Patterns for redacting credentials and SQL parameters
REDACT_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|secret|password|bearer\s+|token)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', re.IGNORECASE), r'\1=***REDACTED***'),
    (re.compile(r'\[SQL:\s*.*?\]', re.DOTALL), '[SQL: ***REDACTED***]'),
    (re.compile(r'\[parameters:\s*.*?\]', re.DOTALL), '[parameters: ***REDACTED***]'),
]


class SensitiveDataFilter(logging.Filter):
    """Logging filter to mask secrets, credentials, and sensitive SQL parameters."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, repl in REDACT_PATTERNS:
                msg = pattern.sub(repl, msg)
            record.msg = msg
        return True


def setup_logging() -> logging.Logger:
    """Configure standardized application logging with privacy filters."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = [handler]

    # Silence verbose internal SQL engine logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("agentforge")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
