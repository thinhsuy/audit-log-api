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
DATA_DIR = Path(PACKAGE_DIR, "data")
TEST_DIR = Path(PACKAGE_DIR, "test")
dir = os.listdir()

ACCESS_TOKEN_EXPIRE_MINUTES = 30
WARNING_THRESHOLD = 50
ERROR_THRESHOLD = 30
CRITICAL_THRESHOLD = 10
RATE_LIMIT_DEFAULT = "10000/minute"
VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")
DATA_ENCRYPTION_KEY = os.environ.get("DATA_ENCRYPTION_KEY")

DB_HOST = os.environ.get("DBHOST", None)
DB_PORT = os.environ.get("DBPORT", None)
DB_USER = os.environ.get("DBUSER", None)
DB_PASSWORD = os.environ.get("DBPASSWORD", None)
DB_NAME = os.environ.get("DBNAME", None)
AUDIT_USER_DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

PANDAS_API_KEY = os.environ.get("PANDAS_API_KEY", None)
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION")
AUDIT_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")

AZURE_OPENAI_EMB_DEPLOYMENT = os.environ.get(
    "AZURE_OPENAI_EMB_DEPLOYMENT"
)
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get(
    "AZURE_OPENAI_DEPLOYMENT_NAME"
)
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")

ONE_WEEK_TOKEN = os.environ.get("ONE_WEEK_TOKEN")
ONE_WEEK_SESSION = os.environ.get("ONE_WEEK_SESSION")

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
