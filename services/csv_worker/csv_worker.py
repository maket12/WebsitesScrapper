import os
import csv
from services.logs.logging import logger as lg


class CsvWorker:
    def __init__(self, parser_name: str, logger=lg):
        self.parser_name = parser_name
        self.logger = logger
        self.file = self._init_file()
        self.fieldnames = [
            'id', 'category', 'name', 'description',
            'images', 'discounted_price', 'regular_price', 'rating',
            'color', 'size', 'url'
        ]

    def _init_file(self):
        path = os.path.join(
            os.getcwd(), f"files/{self.parser_name}"
        )
        os.makedirs(path, exist_ok=True)

        full_path = os.path.join(path, "out.csv")

        self.logger.info(f"Файл по пути {full_path} успешно создан.")
        return full_path

    def create_table(self):
        try:
            with open(self.file, mode='w', encoding='utf-8-sig', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames, delimiter=';')
                writer.writeheader()
        except Exception as e:
            self.logger.error(f"Возникла ошибка при создании таблицы: {e}.")

    def write_to_table(self, rows: list[dict]):
        try:
            with open(self.file, mode='a', encoding='utf-8-sig', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames, delimiter=';')
                writer.writerows(rowdicts=rows)
            self.logger.info(f"Записано {len(rows)} строк в файл.")
        except Exception as e:
            self.logger.error(f"Возникла ошибка при записи в таблицу: {e}.")
