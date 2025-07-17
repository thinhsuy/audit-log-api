import logging
import os
import sys
from logging import config
from pathlib import Path
from dotenv import load_dotenv
from rich.logging import RichHandler
from zoneinfo import ZoneInfo
load_dotenv()

BASE_DIR = Path(__file__).parent.parent.absolute()
LOGS_DIR = Path(BASE_DIR, "logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PACKAGE_DIR = Path(BASE_DIR, "core")
dir = os.listdir()

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256" 
ACCESS_TOKEN_EXPIRE_MINUTES = 30
VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

HOST = os.environ.get("DBHOST", None)
PORT = os.environ.get("DBPORT", None)
DBUSER = os.environ.get("DBUSER", None)
DBPASSWORD = os.environ.get("DBPASSWORD", None)
DBNAME = os.environ.get("DBNAME", None)
AUDIT_USER_DB_URL = f"postgresql+asyncpg://{DBUSER}:{DBPASSWORD}@{HOST}:{PORT}/{DBNAME}"

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "minimal": {"format": "%(message)s"},
        "detailed": {
            "format": "%(levelname)s %(asctime)s [%(name)s:%(filename)s:\
                %(funcName)s:%(lineno)d]\n%(message)s\n"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "minimal",
            "level": logging.DEBUG,
        },
        "info": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": Path(LOGS_DIR, "info.log"),
            "maxBytes": 10485760,  # 1 MB
            "backupCount": 10,
            "formatter": "detailed",
            "level": logging.INFO,
        },
        "error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": Path(LOGS_DIR, "error.log"),
            "maxBytes": 10485760,  # 1 MB
            "backupCount": 10,
            "formatter": "detailed",
            "level": logging.ERROR,
        },
    },
    "root": {
        "handlers": ["console", "info", "error"],
        "level": logging.INFO,
        "propagate": True,
    },
}

config.dictConfig(logging_config)
logger = logging.getLogger("Core")
logger.setLevel(logging.DEBUG)

if len(logger.handlers):
    logger.handlers[0] = RichHandler(markup=True)
else:
    logger.handlers.append(RichHandler(markup=True))