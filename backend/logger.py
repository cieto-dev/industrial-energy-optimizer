import logging
import uuid


# Create application logger
logger = logging.getLogger("industrial_energy_optimizer")

logger.setLevel(logging.INFO)


# Prevent duplicate handlers
if not logger.handlers:
    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)


def generate_request_id() -> str:
    """
    Generate a unique ID for each API request.
    """
    return str(uuid.uuid4())


def log_info(message: str):
    """Log an informational message."""
    logger.info(message)


def log_warning(message: str):
    """Log a warning message."""
    logger.warning(message)


def log_error(message: str):
    """Log an error message."""
    logger.error(message)