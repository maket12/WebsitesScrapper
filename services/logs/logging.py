import logging
import colorlog


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


logger = colorlog.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(color_formatter)
logger.addHandler(console_handler)


logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("curl_cffi").setLevel(logging.ERROR)
