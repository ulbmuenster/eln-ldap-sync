from loguru import logger
import sys

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

# Add handler for CRITICAL level logs to stderr
logger.add(
    sys.stderr,
    level="CRITICAL",
    format="<red>{time} | {level}</red>: {message}",
    filter=lambda record: record["level"].name == "CRITICAL",
)

__all__ = ["logger"]
