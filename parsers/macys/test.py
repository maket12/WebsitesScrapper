from pathlib import Path
import asyncio
from curl_cffi import AsyncSession
import json
from services.logs.logging import logger


test_sample = {
    "category_name": "all-men's-clothing",
    "url": "https://www.macys.com/shop/mens-clothing/all-mens-clothing?id=197651"
}


async def test():
    try:
        async with AsyncSession() as client:
            response = await client.get(url=test_sample["url"])
            if response.status_code == 200:
                path_to_file = Path(__file__).resolve().parent.parent.parent / "data" / "macys" / "test.json"
                path_to_file.parent.mkdir(parents=True, exist_ok=True)
                with open(path_to_file, "w", encoding="utf-8") as file:
                    file.write(response.text)
                    # json.dump(response.json(), file, ensure_ascii=False, indent=2)
                logger.info("Успешно извлекли данные!")
            else:
                logger.warning(f"Не удалось получить корректный ответ(code={response.status_code}).")
    except Exception as e:
        logger.error(f"Возникла ошибка в test: {e}")
    finally:
        logger.debug("Скрипт завершил свою работу.")


asyncio.run(test())
