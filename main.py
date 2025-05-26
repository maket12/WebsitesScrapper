import asyncio
import atexit
from config import Config
from parsers.footlocker import FootlockerParser
from parsers.hnm import HNMParser
from parsers.iherb import IHerbParser
from parsers.asos import AsosParser
from parsers.macys import MacysParser
from utils.load_env_data import get_asocks_key, get_iherb_key
from services.logs.logging import LoggerFactory
from services.proxies import ProxyClient

main_logger = LoggerFactory(logfile="main.log", logger_name="main").get_logger()


async def init_iherb():
    try:
        api_key = get_iherb_key()
        if not api_key:
            main_logger.critical("API-ключ для IHerb не передан.")
            return

        logger = LoggerFactory(
            logfile="files/iherb/iherb.log",
            logger_name="iherb"
        )
        parser = IHerbParser(api_key=api_key, logger=logger)

        return parser
    except Exception as e:
        main_logger.error(f"Возникла ошибка при инициализации IHerb: {e}.")


async def init_asos():
    try:
        proxies_api_key = get_asocks_key()
        if not proxies_api_key:
            main_logger.critical("API-ключ для Asocks не передан.")
            return

        client = ProxyClient(
            api_key=proxies_api_key,
            randomization=False,
            only_proxy=False,
            logger=main_logger
        )
        if not await client.load():
            main_logger.critical("Не удалось загрузить прокси, выход...")
            return

        logger = LoggerFactory(
            logfile="files/asos/asos.log",
            logger_name="asos"
        )
        parser = AsosParser(proxy_client=client, logger=logger)

        return parser
    except Exception as e:
        main_logger.error(f"Возникла ошибка при инициализации Asos: {e}.")


async def init_macys():
    try:
        proxies_api_key = get_asocks_key()
        if not proxies_api_key:
            main_logger.critical("API-ключ для Asocks не передан.")
            return

        client = ProxyClient(
            api_key=proxies_api_key,
            randomization=False,
            only_proxy=False,
            logger=main_logger
        )
        if not await client.load():
            main_logger.critical("Не удалось загрузить прокси, выход...")
            return

        logger = LoggerFactory(
            logfile="files/macys/macys.log",
            logger_name="macys"
        )
        parser = MacysParser(proxy_client=client, logger=logger)

        return parser
    except Exception as e:
        main_logger.error(f"Возникла ошибка при инициализации Macys: {e}.")


async def main():
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
    async with IHerbParser(api_key=iherb_api_key, images_enabled=True, offset=66) as a:
        await a.start()


async def asos_test():
    asocks_api_key = "gWvV6ysOykJPRldJOGbaXSnas3KqFPQP"
    client = ProxyClient(api_key=asocks_api_key)
    if not await client.load():
        logger.critical("Не удалось загрузить прокси.")
        return
    a = AsosParser(proxy_client=client)
    await a.start()


async def macys_test():
    async with MacysParser() as a:
        await a.start()


async def footlocker_test():
    await main()


if __name__ == "__main__":
    asyncio.run(iherb_test())
