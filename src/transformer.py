from datetime import datetime, timedelta
from src.logger import init_logger

log = init_logger(__name__)


def transform_sales_data(raw_records: list[dict]) -> list[tuple]:
    """
    Преобразует список словарей из API в список кортежей для вставки в PostgreSQL
    """
    transformed = []
    skipped = 0

    for row in raw_records:
        try:
            # Склеиваем дату и секунды в полный datetime
            base_date = datetime.strptime(row["purchase_datetime"], "%Y-%m-%d")
            seconds = int(row.get("purchase_time_as_seconds_from_midnight", 0))
            purchase_datetime = base_date + timedelta(seconds=seconds)

            gender = str(row["gender"]).strip().upper()
            quantity = int(row["quantity"])
            price_per_item = float(row["price_per_item"])
            discount_per_item = float(row["discount_per_item"])
            total_price = float(row["total_price"])

            # Проверка соответствия требованиям до отправки в БД
            if (
                gender not in ("F", "M")
                or not (0 <= seconds <= 86400)
                or quantity <= 0
                or price_per_item <= 0
                or discount_per_item < 0
                or total_price < 0
            ):
                log.debug(f"Запись не прошла валидацию и пропущена: {row}") # На случай необходимости посмотреть пропущенные строки
                # if skipped < 3:
                #     log.warning(f"Пример отброшенной записи: {row}")
                skipped += 1
                continue

            record = (
                int(row["client_id"]),
                gender,
                base_date.date(),
                purchase_datetime,
                int(row["product_id"]),
                quantity,
                price_per_item,
                discount_per_item,
                total_price,
            )
            transformed.append(record)

        except (KeyError, ValueError, TypeError) as e:
            log.error(f"Ошибка преобразования записи {row}: {e}")
            continue

    log.info(
        f"Успешно преобразовано {len(transformed)} из {len(raw_records)} записей "
        f"(пропущено при валидации: {skipped})"
    )
    
    return transformed, skipped