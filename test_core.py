from app.core.config import get_settings
from app.core.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

settings = get_settings()

logger.info("Settings loaded successfully")
logger.info("Model: %s", settings.gemini_model)
logger.info("Max revisions: %s", settings.max_revisions)
logger.info("API key loaded: %s", bool(settings.google_api_key))
logger.debug("This debug line is hidden when LOG_LEVEL=INFO")
logger.warning("This is how a warning looks")