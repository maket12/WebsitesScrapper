import asyncio
import atexit
from config import Config, AUTOSAVE_INTERVAL
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
        ).get_logger()
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
        ).get_logger()
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
        ).get_logger()
        parser = MacysParser(proxy_client=client, page_limit=2, logger=logger)

        return parser
    except Exception as e:
        main_logger.error(f"Возникла ошибка при инициализации Macys: {e}.")


async def init_hnm():
    try:
        proxies_api_key = get_asocks_key()
        if not proxies_api_key:
            main_logger.critical("API-ключ для Asocks не передан.")
            return

        client = ProxyClient(
            api_key=proxies_api_key,
            randomization=True,
            only_proxy=False,
            logger=main_logger
        )
        if not await client.load():
            main_logger.critical("Не удалось загрузить прокси, выход...")
            return

        logger = LoggerFactory(
            logfile="files/hnm/hnm.log",
            logger_name="hnm"
        ).get_logger()
        config = Config(is_full_parse=True, reset_state=False)
        parser = HNMParser(client=client, config=config, logger=logger)

        return parser
    except Exception as e:
        main_logger.error(f"Возникла ошибка при инициализации H&M: {e}.")

async def init_footlocker():
    try:
        proxies_api_key = get_asocks_key()
        if not proxies_api_key:
            main_logger.critical("API-ключ для Asocks не передан.")
            return

        client = ProxyClient(
            api_key=proxies_api_key,
            randomization=True,
            only_proxy=False,
            logger=main_logger
        )
        if not await client.load():
            main_logger.critical("Не удалось загрузить прокси, выход...")
            return

        logger = LoggerFactory(
            logfile="files/footlocker/footlocker.log",
            logger_name="footlocker"
        ).get_logger()
        config = Config(is_full_parse=True, reset_state=False)
        parser = FootlockerParser(client=client, config=config, logger=logger)

        return parser
    except Exception as e:
        main_logger.error(f"Возникла ошибка при инициализации Footlocker: {e}.")


async def main():
    macys = await init_macys()
    await macys.start()
    # hnm = await init_hnm()
    # if not hnm:
    #     return
    # footlocker = await init_footlocker()
    # if not footlocker:
    #     return
    parsers = [macys]

    async def autosave_task():
        while True:
            try:
                await asyncio.sleep(AUTOSAVE_INTERVAL)
                main_logger.info("Автосохранение...")
                for parser in parsers:
                    parser.save_all()
            except asyncio.CancelledError:
                return
            except Exception as e:
                main_logger.error(f"Ошибка при автосохранении: {e}")
    
    def on_exit():
        main_logger.info("Сохраняю данные...")
        for parser in parsers:
            parser.save_all()

    atexit.register(on_exit)
    
    autosave_task = asyncio.create_task(autosave_task())
    
    try:
        tasks = [parser.start() for parser in parsers]
        await asyncio.gather(*tasks)
    finally:
        autosave_task.cancel()
        try:
            await autosave_task
        except asyncio.CancelledError:
            pass


# async def iherb_test():
#     iherb_api_key = os.getenv("IHerbAPIToken")
#     async with IHerbParser(api_key=iherb_api_key, images_enabled=True, offset=66) as a:
#         await a.start()


# async def asos_test():
#     asocks_api_key = "gWvV6ysOykJPRldJOGbaXSnas3KqFPQP"
#     client = ProxyClient(api_key=asocks_api_key)
#     if not await client.load():
#         logger.critical("Не удалось загрузить прокси.")
#         return
#     a = AsosParser(proxy_client=client)
#     await a.start()


async def macys_test():
    async with MacysParser() as a:
        await a.start()


async def footlocker_test():
    await main()


if __name__ == "__main__":
    asyncio.run(main())
