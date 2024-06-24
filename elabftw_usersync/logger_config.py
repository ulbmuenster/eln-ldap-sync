import sys

from loguru import logger

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    format="<yellow>{time} | {level}</yellow>: {message}",
    filter=lambda record: record["level"].name == "INFO",
)

logger.add(
    sys.stdout,
    level="SUCCESS",
    format="<green>{time} | {level}</green>: {message}",
    filter=lambda record: record["level"].name == "SUCCESS",
)

logger.add(
    sys.stdout,
    level="ERROR",
    format="<fg #FF8234>{time} | {level}</fg #FF8234>: <b>{message}</b>",
    filter=lambda record: record["level"].name == "ERROR",
)

# Add handler for CRITICAL level logs to stderr
logger.add(
    sys.stderr,
    level="CRITICAL",
    format="<red>{time} | {level}</red>: <b>{message}</b>",
    filter=lambda record: record["level"].name == "CRITICAL",
)

__all__ = ["logger"]
