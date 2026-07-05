from core.config import settings
from core.logger import logger

logger.info("Testing configuration...")

print(f"App Name: {settings.app_name}")
print(f"Version : {settings.version}")
print(f"Model   : {settings.groq_model}")

logger.success("Configuration loaded successfully!")