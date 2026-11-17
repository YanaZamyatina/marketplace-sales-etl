import time
from datetime import datetime, timedelta
from config.settings import API_URL, API_TIMEOUT, DB_CONFIG, DATA_DIR
from src.api_client import MarketplaceAPIClient
from src.transformer import transform_sales_data
from src.db_loader import PostgresLoader
from src.notifier import send_email_report
from src.logger import init_logger

log = init_logger("daily_etl")


def run_daily():
    start_time = time.time()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    log.info(f"Запуск ежедневного ETL за {yesterday}")

    try:
        loader = PostgresLoader(db_config=DB_CONFIG)

        # Проверяем БД до обращения к API
        if loader.is_date_loaded(yesterday):
            msg = f"Данные за {yesterday} уже присутствуют в БД. Повторная загрузка не требуется"
            log.info(msg)
            send_email_report(f"[ETL SKIP] Данные за {yesterday} уже в БД", msg)
            return

        api = MarketplaceAPIClient(base_url=API_URL, timeout=API_TIMEOUT)
        data = api.load_data(yesterday, input_dir=DATA_DIR)
        if data is None:
            data = api.extract_data(yesterday)
            api.save_data(yesterday, data, output_dir=DATA_DIR)
        
        clean_data, validation_skipped = transform_sales_data(data)
        inserted_count, duplicates_skipped = loader.load_data(yesterday, clean_data)

        # Собираем краткую статистику для email-отчета
        total_revenue = sum(row[8] for row in clean_data)
        duration = round(time.time() - start_time, 2)

        subject = f"[ETL OK] Загрузка продаж за {yesterday}"
        body = (
            f"Ежедневная загрузка данных успешно завершена\n\n"
            f"Дата данных: {yesterday}\n"
            f"Получено записей из API: {len(data)}\n"
            f"Загружено в БД: {inserted_count}\n"
            f"Пропущено (ошибки валидации): {validation_skipped}\n"
            f"Пропущено (дубли в БД): {duplicates_skipped}\n"
            f"Общая сумма продаж: {total_revenue:,.2f} руб.\n"
            f"Время выполнения: {duration} сек."
        )
        send_email_report(subject, body)
        log.info(f"Ежедневный ETL за {yesterday} успешно завершен")

    except Exception as e:
        log.error(f"Ошибка при выполнении ETL за {yesterday}: {e}")
        subject = f"[ETL ERROR] Сбой загрузки за {yesterday}"
        body = (
            f"При ежедневной загрузке данных произошла ошибка:\n\n"
            f"{e}\n\n"
            f"Проверьте логи на сервере: logs/etl.log"
        )
        send_email_report(subject, body)
        raise


if __name__ == "__main__":
    run_daily()