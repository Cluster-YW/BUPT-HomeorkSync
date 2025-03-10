from loguru import logger
import sys

logger.add("runtime.log", rotation="100 MB", level="TRACE")
logger.add("runtime.log", rotation="100 MB", level="WARNING")
logger.add("runtime.log", rotation="100 MB", level="ERROR")