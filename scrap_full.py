import parsers.iherb as iherb
import asyncio

async def scrap_full():
  await iherb.scrap_full()


if __name__ == "__main__":
  asyncio.run(scrap_full())
