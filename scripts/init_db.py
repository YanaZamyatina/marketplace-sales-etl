from config.settings import DB_CONFIG
from src.db_loader import PostgresLoader
from src.logger import init_logger

log = init_logger("init_db")


def main():
    log.info("Запуск инициализации базы данных")
    loader = PostgresLoader(db_config=DB_CONFIG)
    loader.create_tables()
    log.info("Инициализация базы данных успешно завершена.")


if __name__ == "__main__":
    main()