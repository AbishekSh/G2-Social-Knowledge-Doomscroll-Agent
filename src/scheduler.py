import logging
import time
from typing import Callable

from .config import settings

logger = logging.getLogger(__name__)


def run_loop(task: Callable[[], None]) -> None:
    logger.info("Starting loop mode with %s second interval.", settings.poll_interval_seconds)
    while True:
        task()
        logger.info("Sleeping for %s seconds.", settings.poll_interval_seconds)
        time.sleep(settings.poll_interval_seconds)
