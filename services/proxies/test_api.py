import asyncio

from curl_cffi import AsyncSession

API_KEY = ""
API_GET_PORTS = "https://api.asocks.com/v2/proxy/ports?apiKey={}"
API_REFRESH_PORT = "https://api.asocks.com/v2/proxy/refresh/{}?apiKey={}"

async def get_proxies():
  async with AsyncSession() as session:
    response = await session.get(API_GET_PORTS.format(API_KEY))
    if response.status_code == 200:
      response_json = response.json()
      if not response_json["success"]:
        print(f"Error: {response_json['message']}")
        return None
      
      proxies = response_json["message"]["proxies"]
      proxies = list(filter(lambda x: x["status"] == 1, proxies))
      return proxies
    else:
      print(f"Error: {response.status_code} - {response.text}")
      return None

async def refresh_proxy(proxy_id):
  async with AsyncSession() as session:
    response = await session.get(API_REFRESH_PORT.format(proxy_id, API_KEY))
    if response.status_code == 200:
      response_json = response.json()
      if not response_json["success"]:
        print(f"Error: {response_json['message']}")
        return False
      
      return True
    else:
      print(f"Error: {response.status_code} - {response.text}")
      return False

async def main():
  proxies = await get_proxies()
  if not proxies:
    print("No proxies found.")
    return
  print(f"Found {len(proxies)} proxies:")
  for proxy in proxies:
    print(f"ID: {proxy['id']} - {proxy['name']} = {proxy['template']}")
  
  proxy = proxies[-1]
  print(f"Using proxy {proxy['id']} - {proxy['name']}")
  async with AsyncSession() as session:
    response = await session.get("https://ipinfo.io/ip", proxy=proxy["template"])
    print(f"IP with proxy: {response.text}")
    print(f"Refreshing proxy {proxy['id']}...")
    success = await refresh_proxy(proxy["id"])
    if success:
      print(f"Proxy {proxy['id']} refreshed successfully.")
    else:
      print(f"Failed to refresh proxy {proxy['id']}.")
  
  # !!! recreate the session to use the new proxy
  async with AsyncSession() as session:
    print("Waiting for 1 seconds to refresh the proxy...")
    await asyncio.sleep(1)  # Wait for the proxy to refresh
    
    response = await session.get("https://ipinfo.io/ip", proxy=proxy["template"])
    print(f"IP with refreshed proxy: {response.text}")
  

if __name__ == "__main__":
  asyncio.run(main())
