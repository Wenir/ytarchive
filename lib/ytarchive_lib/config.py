import os
from dotenv import load_dotenv


def load_config():
    load_dotenv()
    return os.environ