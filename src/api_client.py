import time
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.logger import init_logger
import json

log = init_logger(__name__)


class MarketplaceAPIClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = self._init_session()

    def _init_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504]
        )
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def extract_data(self, date_str: str) -> list[dict]:
        """Выгружает данные за конкретную дату (формат yyyy-mm-dd)"""
        params = {"date": date_str}

        while True:
            try:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout
                )

                if response.status_code == 429:
                    log.warning(f"Rate limit (429) для даты {date_str}. Ждем 10 секунд...")
                    time.sleep(10)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                log.error(f"Ошибка при запросе данных за {date_str}: {e}")
                raise

    def save_data(self, date_str: str, data: list[dict], output_dir: str = "data"):
        """Сохраняет ответ API в JSON-файл"""
        dir_path = Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / f"sales_{date_str}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        log.info(f"Данные сохранены в {file_path}")

    def load_data(self, date_str: str, input_dir: str = "data") -> list[dict] | None:
        """Читает сохраненный JSON-файл с диска, если он существует."""
        file_path = Path(input_dir) / f"sales_{date_str}.json"
        if file_path.exists():
            log.info(f"Файл {file_path.name} уже существует локально. Читаем с диска без запроса в API.")
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None