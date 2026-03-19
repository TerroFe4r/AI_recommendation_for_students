#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Автоматическое обновление модели при изменении данных
"""

import subprocess
import threading
import time
import logging
from pathlib import Path
from datetime import datetime
import sys

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))
from database.db_connector import DatabaseConnector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / 'logs' / 'model_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelUpdater:
    """Автоматическое обновление модели при изменении данных"""

    def __init__(self, check_interval=60):  # Проверка каждые 60 секунд
        self.check_interval = check_interval
        self.last_update = None
        self.running = False
        self.thread = None
        self.db = DatabaseConnector()

    def start(self):
        """Запуск автоматического обновления"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Автоматическое обновление модели запущено")

    def stop(self):
        """Остановка автоматического обновления"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Автоматическое обновление модели остановлено")

    def _monitor_loop(self):
        """Цикл мониторинга изменений"""
        while self.running:
            try:
                if self._check_for_updates():
                    logger.info("Обнаружены новые данные, запускаю обновление модели...")
                    self._update_model()
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")

            # Ждем перед следующей проверкой
            time.sleep(self.check_interval)

    def _check_for_updates(self):
        """Проверка наличия новых данных"""
        try:
            if not self.db.connect():
                return False

            # Получаем время последнего изменения в таблицах
            queries = [
                "SELECT MAX(updated_at) FROM students",
                "SELECT MAX(date) FROM attendance",
                "SELECT MAX(id) FROM session"
            ]

            latest_timestamp = None
            for query in queries:
                result = self.db.fetch_one(query)
                if result and list(result.values())[0]:
                    current = list(result.values())[0]
                    if latest_timestamp is None or current > latest_timestamp:
                        latest_timestamp = current

            self.db.disconnect()

            # Если есть новые данные и прошло больше 5 минут с последнего обновления
            if latest_timestamp and (self.last_update is None or
                                     (datetime.now() - self.last_update).seconds > 300):
                self.last_update = datetime.now()
                return True

            return False

        except Exception as e:
            logger.error(f"Ошибка проверки обновлений: {e}")
            return False

    def _update_model(self):
        """Обновление модели на новых данных"""
        try:
            logger.info("=" * 60)
            logger.info("НАЧАЛО ОБНОВЛЕНИЯ МОДЕЛИ")

            # Шаг 1: Создание признаков
            logger.info("📊 Шаг 1/3: Создание признаков...")
            result = subprocess.run(
                [sys.executable, "-m", "models.feature_engineering"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Ошибка создания признаков: {result.stderr}")
                return
            logger.info("Признаки созданы")

            # Шаг 2: Обучение модели
            logger.info("🤖 Шаг 2/3: Обучение модели...")
            result = subprocess.run(
                [sys.executable, "-m", "models.classifier"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Ошибка обучения модели: {result.stderr}")
                return
            logger.info("Модель обучена")

            # Шаг 3: Перезагрузка агента (опционально)
            logger.info("Шаг 3/3: Модель готова к использованию")

            logger.info("=" * 60)
            logger.info("МОДЕЛЬ УСПЕШНО ОБНОВЛЕНА")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Ошибка обновления модели: {e}")

    def force_update(self):
        """Принудительное обновление модели"""
        logger.info("Принудительное обновление модели...")
        self._update_model()


# Декоратор для автоматического обновления после операций с БД
def auto_update_model(func):
    """Декоратор для автоматического обновления модели после изменения данных"""

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        # Запускаем обновление в отдельном потоке
        updater = ModelUpdater()
        thread = threading.Thread(target=updater.force_update)
        thread.daemon = True
        thread.start()

        return result

    return wrapper