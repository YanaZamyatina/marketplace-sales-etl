import time
from datetime import datetime, timedelta
from config.settings import API_URL, API_TIMEOUT, DB_CONFIG, BACKFILL_DAYS, DATA_DIR
from src.api_client import MarketplaceAPIClient
from src.transformer import transform_sales_data
from src.db_loader import PostgresLoader
from src.logger import init_logger

log = init_logger("backfill")


def run_backfill(days_back: int = BACKFILL_DAYS):
    """
    Выгружает исторические данные за указанное количество дней
    до вчерашнего дня (включительно или до позавчерашнего).
    """
    log.info(f"Запуск первичной выгрузки данных за последние {days_back} дней")

    api = MarketplaceAPIClient(base_url=API_URL, timeout=API_TIMEOUT)
    loader = PostgresLoader(db_config=DB_CONFIG)

    today = datetime.now().date()
    start_date = today - timedelta(days=days_back)
    end_date = today - timedelta(days=1)

    current_date = start_date
    total_days = (end_date - start_date).days + 1
    processed_days = 0

    skipped_days = 0
    loaded_days = 0

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        processed_days += 1

        # Проверяем, есть ли уже данные за этот день в БД
        if loader.is_date_loaded(date_str):
            log.info(f"[{processed_days}/{total_days}] Дата {date_str} уже загружена в БД. Пропускаем")
            skipped_days += 1
            current_date += timedelta(days=1)
            continue

        log.info(f"[{processed_days}/{total_days}] Обработка даты: {date_str}")
        try:
            data = api.load_data(date_str, input_dir=DATA_DIR)

            if data is None:
                data = api.extract_data(date_str)
                api.save_data(date_str, data, output_dir=DATA_DIR)
                time.sleep(0.5)

            clean_data, _ = transform_sales_data(data)
            loader.load_data(date_str, clean_data)
            loaded_days += 1
        except Exception as e:
            log.error(f"Сбой при обработке даты {date_str}: {e}")

        current_date += timedelta(days=1)

    log.info(
        f"Историческая выгрузка завершена. "
        f"Загружено новых дней: {loaded_days}, пропущено (уже в БД): {skipped_days}"
    )


if __name__ == "__main__":
    run_backfill()