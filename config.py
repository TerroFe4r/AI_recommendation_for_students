"""
Конфигурационный файл проекта
"""
import os
from pathlib import Path

# Пути к проекту
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'

# Создаем директории, если их нет
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Настройки MySQL
DB_CONFIG = {
    'host': 'localhost',
    'database': 'education_db',
    'user': 'root',
    'password': 'dr23062004',
    'port': 3306
}

# Альтернативный формат для SQLAlchemy
DATABASE_URL = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"

# Данные деканата
DEAN_LOGIN = "dean"
DEAN_PASSWORD = "dean123"

# Настройки GigaChat
GIGACHAT_CREDENTIALS = ""

# Настройки моделей
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Параметры для генерации данных
NUM_STUDENTS = 150
NUM_SUBJECTS = 10
NUM_WEEKS = 4
MAX_LESSONS_PER_DAY = 5
DAYS_PER_WEEK = 6