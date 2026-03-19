"""
Модуль для подключения к MySQL базе данных
"""
import mysql.connector
from mysql.connector import Error
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DB_CONFIG

class DatabaseConnector:
    """Класс для работы с MySQL базой данных"""

    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """Установка соединения с БД"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor(dictionary=True)
            print("✅ Подключение к MySQL успешно")
            return True
        except Error as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def disconnect(self):
        """Закрытие соединения"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("🔌 Соединение закрыто")

    def execute_query(self, query, params=None):
        """Выполнение SQL запроса"""
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return True
        except Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return False

    def fetch_all(self, query, params=None):
        """Получение всех записей"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            print(f"Ошибка получения данных: {e}")
            return []

    def fetch_one(self, query, params=None):
        """Получение одной записи"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Error as e:
            print(f"Ошибка получения данных: {e}")
            return None

    def get_students(self):
        """Получение списка всех студентов"""
        query = "SELECT * FROM students"
        return self.fetch_all(query)

    def get_student_by_id(self, student_id):
        """Получение студента по ID"""
        query = "SELECT * FROM students WHERE id = %s"
        return self.fetch_one(query, (student_id,))

    def get_student_by_login(self, login):
        """Получение студента по логину"""
        query = "SELECT * FROM students WHERE login = %s"
        return self.fetch_one(query, (login,))

    def get_attendance(self, student_id=None):
        """Получение посещаемости с названиями предметов"""
        if student_id:
            query = """
                SELECT a.*, s.name as subject_name 
                FROM attendance a
                JOIN subjects s ON a.subject_id = s.id
                WHERE a.student_id = %s
                ORDER BY a.date DESC
            """
            return self.fetch_all(query, (student_id,))
        query = """
            SELECT a.*, s.name as subject_name 
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.id
            ORDER BY a.date DESC
        """
        return self.fetch_all(query)

    def get_session_results(self, student_id=None):
        """Получение результатов сессии"""
        if student_id:
            query = "SELECT * FROM session WHERE student_id = %s"
            return self.fetch_all(query, (student_id,))
        query = "SELECT * FROM session"
        return self.fetch_all(query)

    def get_subjects(self):
        """Получение списка дисциплин"""
        query = "SELECT * FROM subjects"
        return self.fetch_all(query)

    def get_student_full_info(self, student_id):
        """Получение полной информации о студенте"""
        info = {}

        # Основные данные
        student = self.get_student_by_id(student_id)
        if not student:
            return None
        info['student'] = student

        # Посещаемость
        info['attendance'] = self.get_attendance(student_id)

        # Результаты сессии
        info['session'] = self.get_session_results(student_id)

        return info

    def to_dataframe(self, query, params=None):
        """Преобразование результата запроса в DataFrame"""
        try:
            self.cursor.execute(query, params or ())
            data = self.cursor.fetchall()
            return pd.DataFrame(data)
        except Error as e:
            print(f"Ошибка создания DataFrame: {e}")
            return pd.DataFrame()