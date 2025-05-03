from logging import Logger
from parser import Parser

from config import Config


class MacysParser(Parser):
  def __init__(self, client, logger: Logger, config: Config):
    super().__init__("macys", client, logger, config)

  async def parse(self):
    pass
