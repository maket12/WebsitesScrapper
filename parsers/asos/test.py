import asyncio
from curl_cffi import AsyncSession


async def test():
    url = ("https://www.asos.com/collusion/collusion-boxy-short-sleeve-t-shirt-in-white/prd/205495165#colourWayId"
           "-205495166")

    async with AsyncSession(impersonate="chrome") as client:
        resp = await client.get(url)
        with open("out.html", "w", encoding='utf-8') as file:
            file.write(resp.text)


asyncio.run(test())
