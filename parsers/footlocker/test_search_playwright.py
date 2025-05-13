import asyncio

from playwright.async_api import async_playwright


async def extract_data(page):
  data = await page.evaluate("""
    () => {
    const state = window.footlocker.globalstore.getState();
    return {
      products: state.search.products,
      pagination: state.search.pagination,
      details_selected: state.details.selected
    };
    }
  """)
  products = data["products"]
  pagination = data["pagination"]
  print(pagination)
  details_selected = data["details_selected"]
  print(details_selected)
  print(products[0])


async def main():
  async with async_playwright() as p:
    browser = await p.chromium.launch(
      headless=False, args=["--disable-blink-features=AutomationControlled"]
    )
    context = await browser.new_context(
      viewport={"width": 1920, "height": 1080}, locale="en-GB"
    )
    page = await context.new_page()

    await page.goto("https://www.footlocker.co.uk/en/category/men.html")

    print("Page 1")
    await extract_data(page)

    await page.click('a[aria-label="Go to next page"]')
    prev_url = page.url
    while True:
      await page.wait_for_timeout(500)
      if page.url != prev_url:
        break

    await page.wait_for_selector('.ProductCard-image', timeout=0)
    await page.wait_for_timeout(1000)

    print("Page 2")
    await extract_data(page)

    await browser.close()


if __name__ == "__main__":
  asyncio.run(main())
