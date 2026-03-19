"""
Модуль аутентификации и хэширования паролей
"""
import hashlib
import os
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DEAN_LOGIN, DEAN_PASSWORD

logger = logging.getLogger(__name__)


class AuthManager:
    """Менеджер аутентификации"""

    def __init__(self, db_connector):
        self.db = db_connector

    @staticmethod
    def hash_password(password):
        """
        Хэширование пароля с солью
        Возвращает (salt, hash)
        """
        salt = os.urandom(32).hex()

        hash_obj = hashlib.sha256((password + salt).encode())
        password_hash = hash_obj.hexdigest()

        return salt, password_hash

    @staticmethod
    def verify_password(password, salt, stored_hash):
        """Проверка пароля"""
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == stored_hash

    def check_dean_auth(self, login, password):
        """Проверка аутентификации деканата"""
        return login == DEAN_LOGIN and password == DEAN_PASSWORD

    def check_student_auth(self, login, password):
        """Проверка аутентификации студента"""
        query = "SELECT id, password_hash, salt FROM students WHERE login = %s"
        result = self.db.fetch_one(query, (login,))

        if not result:
            return None

        if self.verify_password(password, result['salt'], result['password_hash']):
            return result['id']

        return None

    def authenticate(self, login, password):
        """
        Основной метод аутентификации
        Возвращает (role, user_id)
        """
        if self.check_dean_auth(login, password):
            logger.info(f"Аутентификация деканата: {login}")
            return ('dean', None)

        student_id = self.check_student_auth(login, password)
        if student_id:
            logger.info(f"Аутентификация студента ID: {student_id}")
            return ('student', student_id)

        logger.warning(f"Неудачная попытка входа: {login}")
        return (None, None)

    def create_student_account(self, student_id, login, password):
        """
        Создание учетной записи студента
        (для генератора данных)
        """
        salt, password_hash = self.hash_password(password)

        query = """
            UPDATE students 
            SET login = %s, password_hash = %s, salt = %s 
            WHERE id = %s
        """

        return self.db.execute_query(query, (login, password_hash, salt, student_id))