import psycopg2
from psycopg2.extras import execute_values
from src.logger import init_logger

log = init_logger(__name__)


class PostgresLoader:
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def create_tables(self):
        """Создает таблицу sales в базе данных"""
        ddl = """
        CREATE TABLE IF NOT EXISTS sales(
            id SERIAL PRIMARY KEY,
            client_id INT NOT NULL,
            gender CHAR(1) NOT NULL CHECK (gender IN ('F', 'M')),
            purchase_date DATE NOT NULL,
            purchase_datetime TIMESTAMP NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL CHECK (quantity > 0),
            price_per_item NUMERIC(10, 2) NOT NULL CHECK (price_per_item > 0),
            discount_per_item NUMERIC(10, 2) CHECK (discount_per_item >= 0),
            total_price NUMERIC(14, 2) NOT NULL CHECK (total_price >= 0),
            CONSTRAINT unique_purchase UNIQUE (client_id, purchase_datetime, product_id)
        );

        CREATE INDEX IF NOT EXISTS idx_sales_purchase_date ON sales(purchase_date);

        COMMENT ON COLUMN sales.purchase_date IS 'Дата покупки (YYYY-MM-DD)';
        COMMENT ON COLUMN sales.purchase_datetime IS 'Полные дата и время покупки (YYYY-MM-DD HH:MM:SS)';
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(ddl)
            conn.commit()
        log.info("Таблица sales проверена/создана")

    def is_date_loaded(self, date_str: str) -> bool:
        """Проверяет, есть ли уже в базе данные за указанную дату."""
        query = "SELECT EXISTS(SELECT 1 FROM sales WHERE purchase_date = %s);"
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (date_str,))
                return cursor.fetchone()[0]

    def load_data(self, date_str: str, records: list[tuple]) -> tuple[int, int]:
        """Загружает данные за указанную дату"""
        if self.is_date_loaded(date_str):
            log.info(f"Данные за {date_str} уже существуют в БД. Перезапись отменена.")
            return 0, 0

        if not records:
            log.warning(f"Нет данных для загрузки за {date_str}")
            return 0, 0

        insert_sql = """
            INSERT INTO sales (
                client_id, gender, purchase_date, purchase_datetime, product_id,
                quantity, price_per_item, discount_per_item, total_price
            ) VALUES %s
            ON CONFLICT ON CONSTRAINT unique_purchase DO NOTHING
            RETURNING id
        """

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                inserted_rows = execute_values(cursor, insert_sql, records, fetch=True)
                inserted_count = len(inserted_rows)
            conn.commit()
        
        duplicates_skipped = len(records) - inserted_count      
        log.info(
            f"Загружено {inserted_count} строк за {date_str} "
            f"(пропущено дублей в БД: {duplicates_skipped})"
        )
        return inserted_count, duplicates_skipped