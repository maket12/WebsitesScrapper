import asyncio
import logging

from curl_cffi import AsyncSession

from config import Config
from parsers.hnm import HNMParser
import atexit

logging.basicConfig(filename="log.txt", level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")

async def parse():
  client = AsyncSession()
  logger = logging.getLogger("parser")
  config = Config(is_full_parse=False, reset_state=False)
  hnm = HNMParser(client, logger, config)
  
  scrap_tasks = []
  scrap_tasks.append(hnm.parse())
  
  await asyncio.gather(*scrap_tasks)
  
  def on_exit():
    logger.info("Saving everything...")
    hnm.save_all()
  
  atexit.register(on_exit)


if __name__ == "__main__":
  asyncio.run(parse())
