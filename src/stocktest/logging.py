"""Logging configuration using structlog."""

import logging
import os
import sys

import structlog


def configure_logging() -> None:
    """Configure structured logging with TTY detection and LOG_LEVEL support.

    Configures structlog to output:
    - Pretty colored console output when running in a TTY
    - JSON output when running in non-TTY (e.g., piped, redirected, or in CI)

    Log level is controlled via LOG_LEVEL environment variable.
    Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Default: INFO
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()

    try:
        log_level = getattr(logging, log_level_str)
    except AttributeError:
        log_level = logging.INFO
        print(
            f"Warning: Invalid LOG_LEVEL '{log_level_str}', defaulting to INFO",
            file=sys.stderr,
        )

    is_tty = sys.stderr.isatty()

    if is_tty:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
