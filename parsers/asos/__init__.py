from logging import Logger
from parser import Parser

from config import Config


class AsosParser(Parser):
  def __init__(self, client, logger: Logger, config: Config):
    super().__init__("asos", client, logger, config)

  async def parse(self):
    pass
