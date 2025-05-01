from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def main():
    async with async_playwright() as player:
        browser = await player.chromium.launch(headless=False)

        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        )

        page = await context.new_page()

        await page.goto(url="https://ru.iherb.com/c/supplements?cids=101072",
                        timeout=60000)

        html_content = await page.evaluate('document.documentElement.outerHTML')

        if html_content is None:
            print("Пустой html-документ")
            return

        soup = BeautifulSoup(html_content, "html.parser")

        product_cards = soup.select('div.product-cell-container')

        for card in product_cards:
            # Название
            name_tag = card.select_one('.product-title bdi')
            name = name_tag.get_text(strip=True) if name_tag else None

            # Цена
            price_tag = card.select_one('.product-price .price bdi')
            price = price_tag.get_text(strip=True) if price_tag else None

            # URL
            url_tag = card.select_one('a.absolute-link')
            product_url = url_tag['href'] if url_tag else None

            # Картинка
            img_tag = card.select_one('img.thumbnailImage, .product-image img')
            img_url = img_tag['src'] if img_tag else None

            # Бренд
            brand = url_tag['data-ga-brand-name'] if url_tag and 'data-ga-brand-name' in url_tag.attrs else None

            # SKU (внутри скрытого блока)
            sku_tag = card.select_one('[itemprop="sku"]')
            sku = sku_tag['content'] if sku_tag else None

            # Категория
            category_tag = card.select_one('[itemprop="category"]')
            category = category_tag['content'] if category_tag else None

            # Рейтинг
            rating_meta = card.select_one('[itemprop="ratingValue"]')
            rating = rating_meta['content'] if rating_meta else None

            # Кол-во отзывов
            review_meta = card.select_one('[itemprop="reviewCount"]')
            reviews = review_meta['content'] if review_meta else None

            print({
                "Name": name,
                "Price": price,
                "URL": product_url,
                "Image": img_url,
                "Brand": brand,
                "SKU": sku,
                "Category": category,
                "Rating": rating,
                "Reviews": reviews
            })

        await page.close()


import asyncio

asyncio.run(main())


