import os
from dotenv import dotenv_values


def load_config():
    if os.path.exists(".env_tmp"):
        return dotenv_values(".env_tmp")
    else:
        return dotenv_values("/.env")