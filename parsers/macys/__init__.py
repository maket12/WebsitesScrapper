from services.logs.logging import logger
from parsers.parser import Parser

from config import Config


class MacysParser(Parser):
    def __init__(self, client, logger: logger, config: Config):
        super().__init__("macys", client, logger, config)

    async def parse(self):
        pass
