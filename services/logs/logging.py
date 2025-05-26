import logging
import colorlog


class LoggerFactory:
    def __init__(self, logfile: str, level=logging.DEBUG, logger_name: str = None):
        self.logfile = logfile
        self.level = level
        self.logger_name = logger_name
        self.logger = self._create_logger()

    def _create_logger(self):
        color_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s [line:%(lineno)d]')

        logger = colorlog.getLogger(self.logger_name)
        logger.setLevel(self.level)
        logger.handlers.clear()

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(color_formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(self.logfile, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logging.getLogger("asyncio").setLevel(logging.ERROR)
        logging.getLogger("curl_cffi").setLevel(logging.ERROR)

        return logger

    def get_logger(self):
        return self.logger
