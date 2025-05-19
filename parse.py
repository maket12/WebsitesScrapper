import asyncio
import atexit
import os
from dotenv import load_dotenv
from config import Config
from parsers.footlocker import FootlockerParser
from parsers.hnm import HNMParser
from parsers.iherb import IHerbParser
from parsers.asos import AsosParser
from services.logs.logging import logger
from services.proxies import ProxyClient

load_dotenv()


async def parse():
    asocks_api_key = os.getenv("ASOCKS_API_KEY")
    if not asocks_api_key:
        logger.critical("ASOCKS_API_KEY not found in environment variables.")
        return
    client = ProxyClient(asocks_api_key, logger)
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

    scrap_tasks = [footlocker.parse()]

    await asyncio.gather(*scrap_tasks)
    await client.shutdown()


async def iherb_test():
    iherb_api_key = os.getenv("IHerbAPIToken")
    async with IHerbParser(api_key=iherb_api_key, images_enabled=True, brands_limit=2) as a:
        await a.start()


async def asos_test():
    async with AsosParser() as a:
        await a.start()


if __name__ == "__main__":
    asyncio.run(asos_test())
