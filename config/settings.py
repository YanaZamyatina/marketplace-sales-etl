import configparser
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем данные из .env
load_dotenv()

# Читаем config.ini
config = configparser.ConfigParser()
config_path = Path(__file__).parent / "config.ini"
config.read(config_path, encoding="utf-8")

# Настройки из config.ini
API_URL = config.get("API", "BASE_URL")
API_TIMEOUT = config.getint("API", "TIMEOUT")
API_MAX_RETRIES = config.getint("API", "MAX_RETRIES")

LOG_DIR = config.get("ETL", "LOG_DIR")
DATA_DIR = config.get("ETL", "DATA_DIR", fallback="data/raw")
BATCH_SIZE = config.getint("ETL", "BATCH_SIZE")
BACKFILL_DAYS = config.getint("ETL", "BACKFILL_DAYS", fallback=30)

EMAIL_ENABLED = config.getboolean("EMAIL", "ENABLED", fallback=False)
SMTP_SERVER = config.get("EMAIL", "SMTP_SERVER", fallback="smtp.mail.ru")
SMTP_PORT = config.getint("EMAIL", "SMTP_PORT", fallback=465)

# Настройки БД из .env
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "marketplace_db"),
    "user": os.getenv("DB_USER", "etl_user"),
    "password": os.getenv("DB_PASSWORD"),
}

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")