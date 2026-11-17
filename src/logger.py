import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def init_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Настраивает и возвращает логгер с выводом в консоль и файл (раз в день).
    """
    # Создаем папку для логов, если её еще нет
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Защита от дублирования логов, если init_logger вызовут повторно с тем же именем
    if logger.handlers:
        return logger

    # Единый формат: [Время] [Уровень] [Модуль:строка] - Сообщение
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-15s:%(lineno)-2d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Обработчик для записи в файл (новый файл каждую полночь, храним 30 дней)
    file_handler = TimedRotatingFileHandler(
        filename=log_path / "etl.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Обработчик для вывода в терминал
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger