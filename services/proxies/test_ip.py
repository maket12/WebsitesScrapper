from curl_cffi import AsyncSession
import asyncio

proxy_url = "http://nwzm0qqmud-corp.mobile.res-country-DE-hold-session-session-68237b664bdbd:CmXgUytwrLCFbgBI@109.236.82.42:9999"

async def test_ip():
  async with AsyncSession(impersonate="chrome") as session:
    response_no_proxy = await session.get("https://ipinfo.io/ip")
    print(f"IP without proxy: {response_no_proxy.text}")
    response_with_proxy = await session.get("https://ipinfo.io/ip", proxy=proxy_url)
    print(f"IP with proxy: {response_with_proxy.text}")


if __name__ == "__main__":
  asyncio.run(test_ip())
