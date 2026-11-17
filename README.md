# Marketplace Sales ETL Pipeline

Автоматизированный ETL-пайплайн на Python для сбора, валидации и загрузки данных о продажах онлайн-маркетплейса из REST API в базу данных PostgreSQL.

## Архитектура и возможности проекта

* **Извлечение (Extract):** загрузка статистики продаж по API через библиотеку `requests` с повторными попытками при ошибках соединения и сохранением сырых JSON-файлов на диск.
* **Преобразование и валидация (Transform):** приведение типов, объединение даты и времени покупки в `TIMESTAMP`, фильтрация некорректных записей по бизнес-правилам.
* **Загрузка (Load):** пакетная вставка в PostgreSQL (`execute_values`), защита от дублей (`UNIQUE` constraint) и проверка уже загруженных дат.
* **Автоматизация и мониторинг:** ежедневный запуск по расписанию через `cron` в 07:00, ротация лог-файлов по дням и отправка Email-отчетов о результатах работы.

---

## Структура репозитория

```text
marketplace_etl/
├── config/
│   ├── __init__.py
│   ├── config.ini           # Основные настройки API, путей и параметров ETL
│   └── settings.py          # Загрузка конфигурации и переменных окружения
├── src/
│   ├── __init__.py
│   ├── api_client.py        # Клиент для работы с API и локальным JSON-кэшем
│   ├── db_loader.py         # Создание таблиц, проверка дат и загрузка в PostgreSQL
│   ├── logger.py            # Настройка логирования (консоль + ротация файлов)
│   ├── notifier.py          # Отправка уведомлений и статистики на Email (SMTP SSL)
│   └── transformer.py       # Очистка, валидация и преобразование данных
├── scripts/
│   ├── __init__.py
│   ├── init_db.py           # Инициализация структуры БД (DDL)
│   ├── backfill.py          # Первичная выгрузка исторических данных
│   ├── daily_etl.py         # Ежедневный скрипт загрузки данных за вчерашний день
│   └── restore_db.py        # Восстановление данных в БД из локальных JSON-файлов
├── data/                    # (создается автоматически, в .gitignore) Сырые JSON-файлы: sales_YYYY-MM-DD.json
├── logs/                    # (создается автоматически, в .gitignore) Логи работы: etl.log
├── .env.example             # Шаблон файла с переменными окружения
├── .gitignore               # Исключение логов, сырых данных и venv
├── requirements.txt         # Зависимости проекта
└── README.md                # Документация проекта
```

---

## Схема базы данных

Данные сохраняются в таблицу `sales` (PostgreSQL):

| Поле | Тип данных | Описание и ограничения |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Уникальный идентификатор записи в БД |
| `client_id` | `INT NOT NULL` | Идентификатор клиента |
| `gender` | `CHAR(1) NOT NULL` | Пол клиента (`'F'` или `'M'`) |
| `purchase_date` | `DATE NOT NULL` | Дата покупки (индексируемое поле) |
| `purchase_datetime` | `TIMESTAMP NOT NULL` | Точные дата и время покупки |
| `product_id` | `INT NOT NULL` | Идентификатор товара |
| `quantity` | `INT NOT NULL` | Количество единиц товара (`> 0`) |
| `price_per_item` | `NUMERIC(10, 2) NOT NULL` | Цена за единицу товара (`> 0`) |
| `discount_per_item` | `NUMERIC(10, 2)` | Скидка на единицу товара (`>= 0`) |
| `total_price` | `NUMERIC(14, 2) NOT NULL` | Итоговая стоимость покупки (`>= 0`) |

Дополнительно установлен уникальный ключ `UNIQUE (client_id, purchase_datetime, product_id)` для исключения дублирования транзакций.

---

## Установка и запуск (Ubuntu + PostgreSQL)

### 1. Клонирование репозитория и установка зависимостей
```bash
git clone https://github.com<ваш_логин>/<ваш_репозиторий>.git /opt/marketplace_etl
cd /opt/marketplace_etl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
Скопируйте шаблон `.env.example` в `.env` и укажите реальные доступы к PostgreSQL и SMTP:
```bash
cp .env.example .env
nano .env
```

Пример заполнения `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=marketplace_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password

SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password_here
EMAIL_TO=recipient_email@example.com
```

### 3. Инициализация базы данных и первичная загрузка
```bash
# Создание таблицы и индексов
python -m scripts.init_db

# Первичная выгрузка исторических данных
python -m scripts.backfill
```

### 4. Настройка автоматического запуска по расписанию (`cron`)
Откройте планировщик задач (`crontab -e`) и добавьте правило для ежедневного запуска скрипта в **07:00**:
```cron
0 7 * * * cd /opt/marketplace_etl && /opt/marketplace_etl/venv/bin/python -m scripts.daily_etl >> /opt/marketplace_etl/logs/cron.log 2>&1
```

---

## Логирование и аварийное восстановление
* Все события работы скриптов записываются в `logs/etl.log` с автоматической ежедневной ротацией (хранение за последние 30 дней).
* Ответы API сохраняются в директорию `data/`. В случае необходимости повторной загрузки данных в базу без обращения к API используется скрипт:
  ```bash
  python -m scripts.restore_db
  ```