import asyncio
import logging

from curl_cffi import AsyncSession

from config import Config
from parsers.hnm import HNMParser
import atexit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s",
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler()
    ]
)


async def parse():
    client = AsyncSession(impersonate="chrome")
    logger = logging.getLogger("parser")
    logger.setLevel(logging.INFO)
    config = Config(is_full_parse=False, reset_state=False)
    hnm = HNMParser(client, logger, config)

    def on_exit():
        logger.info("Saving everything...")
        hnm.save_all()

    atexit.register(on_exit)

    scrap_tasks = [hnm.parse()]

    await asyncio.gather(*scrap_tasks)


if __name__ == "__main__":
    asyncio.run(parse())
