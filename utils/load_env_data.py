import os
from dotenv import load_dotenv


def get_asocks_key():
    load_dotenv()
    return os.getenv("ASOCKS_API_KEY")


def get_iherb_key():
    load_dotenv()
    return os.getenv("IHERB_API_KEY")
