import json
from pathlib import Path
from config.settings import DB_CONFIG, DATA_DIR
from src.transformer import transform_sales_data
from src.db_loader import PostgresLoader
from src.logger import init_logger

log = init_logger("restore_db")


def upload_local_files():
    """Читает все сохраненные JSON-файлы из DATA_DIR и загружает их в БД"""
    dir = Path(DATA_DIR)
    json_files = sorted(dir.glob("sales_*.json"))

    if not json_files:
        log.warning(f"В папке {dir} не найдено файлов sales_*.json")
        return

    log.info(f"Найдено {len(json_files)} файлов для загрузки в БД")
    loader = PostgresLoader(db_config=DB_CONFIG)

    restored_days = 0
    skipped_days = 0

    for idx, file_path in enumerate(json_files, start=1):
        # Извлекаем дату из имени файла
        date_str = file_path.stem.replace("sales_", "")
        
        if loader.is_date_loaded(date_str):
            log.info(f"[{idx}/{len(json_files)}] Дата {date_str} уже есть в БД. Пропускаем")
            skipped_days += 1
            continue
        
        log.info(f"[{idx}/{len(json_files)}] Восстановление из файла {file_path.name} за {date_str}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            clean_data, _ = transform_sales_data(data)
            loader.load_data(date_str, clean_data)
            restored_days += 1

        except Exception as e:
            log.error(f"Ошибка при загрузке файла {file_path.name}: {e}")

    log.info(
        f"Восстановление завершено. "
        f"Загружено новых дней: {restored_days}, пропущено (уже в БД): {skipped_days}"
    )


if __name__ == "__main__":
    upload_local_files()