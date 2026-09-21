import logging
from logging.config import dictConfig


def configure_logging(log_level: str = "INFO") -> None:
    """Configure application-wide logging."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "level": log_level.upper(),
                "handlers": ["console"],
            },
        }
    )
    logging.getLogger("swamitra").debug("Logging configured at %s", log_level.upper())
