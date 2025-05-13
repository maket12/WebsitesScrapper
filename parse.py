import asyncio
import atexit

from curl_cffi import AsyncSession

from config import Config
from parsers.footlocker import FootlockerParser
from parsers.hnm import HNMParser
from services.logs.logging import logger
from services.proxies import ProxyClient


async def parse():
  client = ProxyClient(logger)
  if not await client.load():
    logger.critical("Could not load proxies, exiting...")
    return
  
  config = Config(is_full_parse=True, reset_state=False)
  hnm = HNMParser(client, logger, config)
  footlocker = FootlockerParser(client, logger, config)

  def on_exit():
    logger.info("Saving everything...")
    hnm.save_all()
    footlocker.save_all()

  atexit.register(on_exit)

  # TODO - removed hnm.parse() for testing
  scrap_tasks = [footlocker.parse()]

  await asyncio.gather(*scrap_tasks)
  await client.shutdown()


if __name__ == "__main__":
  asyncio.run(parse())
