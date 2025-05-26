import asyncio
import random
from curl_cffi import AsyncSession
from services.logs.logging import LoggerFactory


class EmptyResponse:
    status_code = -1
    text = ""


class ProxyClient:
    def __init__(
            self, api_key: str, randomization: bool = True, only_proxy: bool = True,
            refresh_timeout: int = 20, logger=None
    ):
        self.API_GET_PORTS = "https://api.asocks.com/v2/proxy/ports?apiKey={}"
        self.API_REFRESH_PORT = "https://api.asocks.com/v2/proxy/refresh/{}?apiKey={}"

        self.api_key = api_key
        self.randomization = randomization
        self.only_proxy = only_proxy
        self.refresh_timeout = refresh_timeout

        self.client = AsyncSession()

        self.proxies = []  # {id: int, proxy: str}
        self.current_proxy_ind = 0
        self.refresh_worker = None

        if logger is not None:
            self.logger = logger
        else:
            self.logger = LoggerFactory(logfile="proxies.log", logger_name="proxies").get_logger()

    def get_random_proxy(self):
        return random.choice(self.proxies)

    def iter_proxy(self):
        if self.current_proxy_ind + 1 == len(self.proxies):
            self.current_proxy_ind = 0
            return True
        else:
            self.current_proxy_ind += 1
            return False

    async def load(self):
        self.logger.info("Подгружаем доступные прокси...")
        self.proxies = await self.get_proxies()
        if not self.proxies:
            self.logger.critical("Прокси не найдены.")
            return False

        self.logger.info(f"Погружено {len(self.proxies)} прокси:")
        for proxy in self.proxies:
            self.logger.info(f"ID: {proxy['id']} - {proxy['name']} = {proxy['template']}")

        if not self.only_proxy:
            self.proxies.insert(0, None)

        self.refresh_worker = asyncio.create_task(self.proxy_refresh_worker())
        return True

    async def shutdown(self):
        await self.client.close()
        if not self.refresh_worker:
            return

        self.refresh_worker.cancel()
        try:
            await self.refresh_worker
        except asyncio.CancelledError:
            pass

    async def get_proxies(self):
        response = await self.client.get(self.API_GET_PORTS.format(self.api_key))
        if response.status_code == 200:
            response_json = response.json()
            if not response_json["success"]:
                self.logger.error(f"Ошибка: {response_json['message']}")
                return None

            proxies = response_json["message"]["proxies"]
            proxies = list(filter(lambda x: x["status"] == 1, proxies))
            for proxy in proxies:
                proxy["template"] = proxy["template"].replace("http://", "socks5://")
            return proxies
        else:
            self.logger.error(f"Ошибка: {response.status_code} - {response.text}")
            return None

    async def proxy_refresh_worker(self):
        while True:
            try:
                proxy = self.get_random_proxy()
                await self.refresh_proxy(proxy)
                await asyncio.sleep(self.refresh_timeout)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка при обновлении прокси: {e}")
                await asyncio.sleep(self.refresh_timeout)

    async def refresh_proxy(self, proxy):
        proxy_id = proxy["id"]
        proxy_name = proxy["name"]
        response = await self.client.get(self.API_REFRESH_PORT.format(proxy_id, self.api_key))
        if response.status_code == 200:
            response_json = response.json()
            if not response_json["success"]:
                self.logger.error(
                    f"Ошибка во время обновления прокси {proxy_name}({proxy_id}): {response_json['message']}"
                )
            else:
                self.logger.info(f"Прокси {proxy_name}({proxy_id}) обновлён.")
        else:
            self.logger.error(
                f"Ошибка во время обновления прокси {proxy_name}({proxy_id}): {response.status_code} - {response.text}"
            )

    async def get(self, url, **kwargs):
        try:
            if self.randomization:
                proxy = self.get_random_proxy()["template"]
            else:
                if self.proxies:
                    proxy = self.proxies[self.current_proxy_ind]
                else:
                    proxy = None
            async with AsyncSession(impersonate="chrome") as session:
                response = await session.get(url, proxy=proxy, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"GET запрос провалился: {e}")
            return EmptyResponse()

    async def post(self, url, **kwargs):
        try:
            if self.randomization:
                proxy = self.get_random_proxy()["template"]
            else:
                if self.proxies:
                    proxy = self.proxies[self.current_proxy_ind]
                else:
                    proxy = None
            async with AsyncSession(impersonate="chrome") as session:
                response = await session.post(url, proxy=proxy, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"POST запрос провалился: {e}")
            return EmptyResponse()

    async def put(self, url, **kwargs):
        try:
            if self.randomization:
                proxy = self.get_random_proxy()["template"]
            else:
                if self.proxies:
                    proxy = self.proxies[self.current_proxy_ind]
                else:
                    proxy = None
            async with AsyncSession(impersonate="chrome") as session:
                response = await session.put(url, proxy=proxy, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"PUT запрос провалился: {e}")
            return EmptyResponse()

    async def delete(self, url, **kwargs):
        try:
            if self.randomization:
                proxy = self.get_random_proxy()["template"]
            else:
                if self.proxies:
                    proxy = self.proxies[self.current_proxy_ind]
                else:
                    proxy = None
            async with AsyncSession(impersonate="chrome") as session:
                response = await session.delete(url, proxy=proxy, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"DELETE запрос провалился: {e}")
            return EmptyResponse()
