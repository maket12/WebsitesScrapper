import asyncio
import random
from logging import Logger

from curl_cffi import AsyncSession

from config import ASOCKS_API_KEY, PROXY_REFRESH_INTERVAL

API_GET_PORTS = "https://api.asocks.com/v2/proxy/ports?apiKey={}"
API_REFRESH_PORT = "https://api.asocks.com/v2/proxy/refresh/{}?apiKey={}"


class EmptyResponse:
  status_code = -1
  text = ""


class ProxyClient:
  def __init__(self, logger: Logger):
    self.logger = logger.getChild("ProxyClient")
    self.client = AsyncSession()
    self.proxies = []  # {id: int, proxy: str}
    self.refresh_worker = None

  def get_random_proxy(self):
    return random.choice(self.proxies)

  async def load(self):
    self.logger.info("Loading proxies...")
    self.proxies = await self.get_proxies()
    if not self.proxies:
      self.logger.error("No proxies found.")
      return False

    self.logger.info(f"Loaded {len(self.proxies)} proxies:")
    for proxy in self.proxies:
      self.logger.info(f"ID: {proxy['id']} - {proxy['name']} = {proxy['template']}")

    self.refresh_worker = asyncio.create_task(self.proxy_refresh_worker())
    return True

  async def shutdown(self):
    self.client.close()
    self.refresh_worker.cancel()
    try:
      await self.refresh_worker
    except asyncio.CancelledError:
      pass

  async def get_proxies(self):
    response = await self.client.get(API_GET_PORTS.format(ASOCKS_API_KEY))
    if response.status_code == 200:
      response_json = response.json()
      if not response_json["success"]:
        self.logger.error(f"Error: {response_json['message']}")
        return None

      proxies = response_json["message"]["proxies"]
      proxies = list(filter(lambda x: x["status"] == 1, proxies))
      return proxies
    else:
      self.logger.error(f"Error: {response.status_code} - {response.text}")
      return None

  async def proxy_refresh_worker(self):
    while True:
      try:
        proxy = self.get_random_proxy()
        await self.refresh_proxy(proxy)
        await asyncio.sleep(PROXY_REFRESH_INTERVAL)
      except asyncio.CancelledError:
        break
      except Exception as e:
        self.logger.error(f"Error in proxy refresh worker: {e}")

  async def refresh_proxy(self, proxy):
    proxy_id = proxy["id"]
    proxy_name = proxy["name"]
    response = await self.client.get(API_REFRESH_PORT.format(proxy_id, ASOCKS_API_KEY))
    if response.status_code == 200:
      response_json = response.json()
      if not response_json["success"]:
        self.logger.error(
          f"Error when refreshing proxy {proxy_name}({proxy_id}): {response_json['message']}"
        )
      else:
        self.logger.info(f"Proxy {proxy_name}({proxy_id}) refreshed.")
    else:
      self.logger.error(
        f"Error when refreshing proxy {proxy_name}({proxy_id}): {response.status_code} - {response.text}"
      )

  async def get(self, url, **kwargs):
    try:
      proxy = self.get_random_proxy()["template"]
      async with AsyncSession(impersonate="chrome") as session:
        response = await session.get(url, proxy=proxy, **kwargs)
      return response
    except Exception as e:
      self.logger.error(f"GET request failed: {e}")
      return EmptyResponse()

  async def post(self, url, **kwargs):
    try:
      proxy = self.get_random_proxy()["template"]
      async with AsyncSession(impersonate="chrome") as session:
        response = await session.post(url, proxy=proxy, **kwargs)
      return response
    except Exception as e:
      self.logger.error(f"POST request failed: {e}")
      return EmptyResponse()

  async def put(self, url, **kwargs):
    try:
      proxy = self.get_random_proxy()["template"]
      async with AsyncSession(impersonate="chrome") as session:
        response = await session.put(url, proxy=proxy, **kwargs)
      return response
    except Exception as e:
      self.logger.error(f"PUT request failed: {e}")
      return EmptyResponse()

  async def delete(self, url, **kwargs):
    try:
      proxy = self.get_random_proxy()["template"]
      async with AsyncSession(impersonate="chrome") as session:
        response = await session.delete(url, proxy=proxy, **kwargs)
      return response
    except Exception as e:
      self.logger.error(f"DELETE request failed: {e}")
      return EmptyResponse()
