import parsers.iherb as iherb
import asyncio

async def scrap_essential():
  await iherb.scrap_essential()


if __name__ == "__main__":
  asyncio.run(scrap_essential())
