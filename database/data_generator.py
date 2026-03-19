#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Генератор синтетических данных для интеллектуального агента
Создает 25 студентов, 10 дисциплин, расписание, посещаемость и сессию
"""

import mysql.connector
import random
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))
try:
    from config import DB_CONFIG
except ImportError:
    # Если config не найден, используем настройки по умолчанию
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'edu_risk_db',
        'user': 'root',
        'password': '',  # Введите ваш пароль
        'port': 3306
    }
    print("[WARN] Файл config.py не найден, используются настройки по умолчанию")


class DataGenerator:
    """Генератор данных для MySQL базы"""

    def __init__(self):
        self.connection = None
        self.cursor = None
        self.student_ids = []
        self.subject_ids = []

        # Данные для генерации
        self.last_names_male = [
            'Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов',
            'Попов', 'Васильев', 'Соколов', 'Михайлов', 'Новиков',
            'Федоров', 'Морозов', 'Волков', 'Алексеев', 'Лебедев',
            'Семенов', 'Егоров', 'Павлов', 'Козлов', 'Степанов',
            'Николаев', 'Орлов', 'Андреев', 'Макаров', 'Зайцев'
        ]
        self.last_names_female = [
            'Иванова', 'Петрова', 'Сидорова', 'Смирнова', 'Кузнецова',
            'Попова', 'Васильева', 'Соколова', 'Михайлова', 'Новикова',
            'Федорова', 'Морозова', 'Волкова', 'Алексеева', 'Лебедева',
            'Семенова', 'Егорова', 'Павлова', 'Козлова', 'Степанова',
            'Николаева', 'Орлова', 'Андреева', 'Макарова', 'Зайцева'
        ]

        self.first_names_male = [
            'Иван', 'Петр', 'Сергей', 'Алексей', 'Дмитрий',
            'Андрей', 'Михаил', 'Александр', 'Владимир', 'Николай'
        ]

        self.first_names_female = [
            'Анна', 'Мария', 'Елена', 'Ольга', 'Наталья',
            'Татьяна', 'Ирина', 'Светлана', 'Екатерина', 'Юлия'
        ]

        self.middle_names_male = [
            'Иванович', 'Петрович', 'Сергеевич', 'Алексеевич', 'Дмитриевич',
            'Андреевич', 'Михайлович', 'Александрович', 'Владимирович', 'Николаевич'
        ]

        self.middle_names_female = [
            'Ивановна', 'Петровна', 'Сергеевна', 'Алексеевна', 'Дмитриевна',
            'Андреевна', 'Михайловна', 'Александровна', 'Владимировна', 'Николаевна'
        ]

        self.subject_names = [
            'Математический анализ',
            'Алгебра и геометрия',
            'Программирование',
            'Базы данных',
            'Физика',
            'Дискретная математика',
            'Английский язык',
            'История',
            'Web-технологии',
            'Операционные системы'
        ]

        self.lesson_types = ['лекция', 'практическое', 'лабораторная']

    def create_database_if_not_exists(self):
        """Создание базы данных, если её нет"""
        try:
            # Подключаемся без указания БД
            config_without_db = DB_CONFIG.copy()
            database_name = config_without_db.pop('database')

            print(f"[*] Подключение к MySQL для создания БД '{database_name}'...")

            conn = mysql.connector.connect(**config_without_db)
            cursor = conn.cursor()

            # Создаем БД с UTF-8 кодировкой
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"[OK] База данных '{database_name}' создана или уже существует")

            cursor.close()
            conn.close()
            return True

        except mysql.connector.Error as e:
            print(f"[ERROR] Ошибка создания БД: {e}")
            print("\n💡 Возможные решения:")
            print("  1. Проверьте, запущен ли MySQL сервер")
            print("  2. Проверьте правильность пароля в config.py")
            print("  3. Убедитесь, что пользователь 'root' имеет права на создание БД")
            return False

    def connect(self):
        """Подключение к MySQL с выбором БД"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            print(f"[OK] Подключено к БД '{DB_CONFIG['database']}'")
            return True
        except mysql.connector.Error as e:
            print(f"[ERROR] Ошибка подключения: {e}")
            return False

    def disconnect(self):
        """Закрытие соединения"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("[OK] Соединение закрыто")

    def create_tables(self):
        """Создание таблиц"""
        try:
            # Таблица студентов
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    last_name VARCHAR(50) NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    middle_name VARCHAR(50),
                    gender ENUM('М', 'Ж') NOT NULL,
                    course INT DEFAULT 2,
                    department VARCHAR(100) DEFAULT 'Прикладная информатика',
                    login VARCHAR(50) UNIQUE,
                    password_hash VARCHAR(256),
                    salt VARCHAR(32)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # Таблица дисциплин
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # Таблица расписания
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedule (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    subject_id INT NOT NULL,
                    lesson_type ENUM('лекция', 'практическое', 'лабораторная') NOT NULL,
                    lesson_order INT NOT NULL,
                    day_of_week INT CHECK (day_of_week BETWEEN 1 AND 6),
                    week_number INT CHECK (week_number IN (1, 2)),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # Таблица посещаемости
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    student_id INT NOT NULL,
                    subject_id INT NOT NULL,
                    lesson_type ENUM('лекция', 'практическое', 'лабораторная') NOT NULL,
                    lesson_order INT NOT NULL,
                    date DATE NOT NULL,
                    is_present BOOLEAN DEFAULT FALSE,
                    grade INT CHECK (grade BETWEEN 2 AND 5 OR grade IS NULL),
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id),
                    UNIQUE KEY unique_attendance (student_id, subject_id, date, lesson_order)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # Таблица сессии
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS session (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    student_id INT NOT NULL,
                    subject_id INT NOT NULL,
                    exam_type ENUM('зачет', 'диф.зачет', 'экзамен') NOT NULL,
                    attempt INT DEFAULT 1 CHECK (attempt IN (1, 2, 3)),
                    result VARCHAR(20) NOT NULL,
                    status ENUM('сдал', 'пересдача', 'комиссия', 'отчислен') DEFAULT 'сдал',
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            self.connection.commit()
            print("[OK] Таблицы созданы")
            return True

        except mysql.connector.Error as e:
            print(f"[ERROR] Ошибка создания таблиц: {e}")
            self.connection.rollback()
            return False

    def hash_password(self, password):
        """Хэширование пароля с солью"""
        salt = os.urandom(16).hex()
        hash_obj = hashlib.sha256((password + salt).encode())
        return salt, hash_obj.hexdigest()

    def generate_students(self):
        """Генерация 25 студентов"""
        print("[*] Генерация студентов...")

        # Транслитерация фамилий для логинов
        translit_map = {
            'Иванов': 'ivanov', 'Петров': 'petrov', 'Сидоров': 'sidorov',
            'Смирнов': 'smirnov', 'Кузнецов': 'kuznetsov', 'Попов': 'popov',
            'Васильев': 'vasiliev', 'Соколов': 'sokolov', 'Михайлов': 'mikhailov',
            'Новиков': 'novikov', 'Федоров': 'fedorov', 'Морозов': 'morozov',
            'Волков': 'volkov', 'Алексеев': 'alekseev', 'Лебедев': 'lebedev',
            'Семенов': 'semenov', 'Егоров': 'egorov', 'Павлов': 'pavlov',
            'Козлов': 'kozlov', 'Степанов': 'stepanov', 'Николаев': 'nikolaev',
            'Орлов': 'orlov', 'Андреев': 'andreev', 'Макаров': 'makarov',
            'Зайцев': 'zaitsev', 'Иванова': 'ivanova', 'Петрова': 'petrova', 'Сидорова': 'sidorova',
            'Смирнова': 'smirnova', 'Кузнецова': 'kuznetsova', 'Попова': 'popova',
            'Васильева': 'vasilieva', 'Соколова': 'sokolova', 'Михайлова': 'mikhailova',
            'Новикова': 'novikova', 'Федорова': 'fedorova', 'Морозова': 'morozova',
            'Волкова': 'volkova', 'Алексеева': 'alekseeva', 'Лебедева': 'lebedeva',
            'Семенова': 'semenova', 'Егорова': 'egorova', 'Павлова': 'pavlova',
            'Козлова': 'kozlova', 'Степанова': 'stepanova', 'Николаева': 'nikolaeva',
            'Орлова': 'orlova', 'Андреева': 'andreeva', 'Макарова': 'makarova',
            'Зайцева': 'zaitseva'
        }

        # Транслитерация имен
        first_names_map = {
            'Иван': 'ivan', 'Петр': 'petr', 'Сергей': 'sergey', 'Алексей': 'alexey',
            'Дмитрий': 'dmitry', 'Андрей': 'andrey', 'Михаил': 'mikhail',
            'Александр': 'alexander', 'Владимир': 'vladimir', 'Николай': 'nikolay',
            'Анна': 'anna', 'Мария': 'maria', 'Елена': 'elena', 'Ольга': 'olga',
            'Наталья': 'natalia', 'Татьяна': 'tatiana', 'Ирина': 'irina',
            'Светлана': 'svetlana', 'Екатерина': 'ekaterina', 'Юлия': 'yulia'
        }

        for i in range(150):
            # Определяем пол (примерно 50/50)
            gender = 'М' if i < 13 else 'Ж'

            # Выбираем имя и отчество по полу
            if gender == 'М':
                last_name = random.choice(self.last_names_male)
                last_name_en = translit_map.get(last_name, last_name.lower())
                first_name = random.choice(self.first_names_male)
                middle_name = random.choice(self.middle_names_male)
            else:
                last_name = random.choice(self.last_names_female)
                last_name_en = translit_map.get(last_name, last_name.lower())
                first_name = random.choice(self.first_names_female)
                middle_name = random.choice(self.middle_names_female)

            first_name_en = first_names_map.get(first_name, first_name.lower())

            # Создаем английский логин
            login = f"{last_name_en}.{first_name_en}.{i}"

            # Хэшируем пароль (пароль = фамилия на английском + '123')
            password = f"{last_name_en}123"
            salt, password_hash = self.hash_password(password)

            print(f"   Создан студент: {last_name} {first_name} -> login: {login}, password: {password}")

            query = """
                INSERT INTO students 
                (last_name, first_name, middle_name, gender, login, password_hash, salt)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            values = (last_name, first_name, middle_name, gender, login, password_hash, salt)
            self.cursor.execute(query, values)

        self.connection.commit()
        print(f"[OK] Сгенерировано 25 студентов")

        # Получаем ID студентов
        self.cursor.execute("SELECT id, last_name, first_name, login FROM students ORDER BY id")
        students = self.cursor.fetchall()
        self.student_ids = [row[0] for row in students]

        # Выводим примеры логинов
        print("\n📋 Примеры логинов и паролей:")
        for row in students[:5]:  # Первые 5 студентов
            last_name_en = translit_map.get(row[1], row[1].lower())
            print(f"   {row[1]} {row[2]}: login={row[3]}, password={last_name_en}123")

    def generate_subjects(self):
        """Генерация 10 дисциплин"""
        print("[*] Генерация дисциплин...")

        for name in self.subject_names:
            query = "INSERT INTO subjects (name) VALUES (%s)"
            self.cursor.execute(query, (name,))

        self.connection.commit()
        print(f"[OK] Сгенерировано {len(self.subject_names)} дисциплин")

        # Получаем ID дисциплин
        self.cursor.execute("SELECT id FROM subjects ORDER BY id")
        self.subject_ids = [row[0] for row in self.cursor.fetchall()]

    def generate_schedule(self):
        """Генерация расписания на 2 недели"""
        print("[*] Генерация расписания...")

        schedule_count = 0

        for week in [1, 2]:
            for day in range(1, 7):  # пн-сб
                # Количество пар в день (3-5)
                num_lessons = random.randint(3, 5)

                for order in range(1, num_lessons + 1):
                    subject_id = random.choice(self.subject_ids)
                    lesson_type = random.choice(self.lesson_types)

                    query = """
                        INSERT INTO schedule 
                        (subject_id, lesson_type, lesson_order, day_of_week, week_number)
                        VALUES (%s, %s, %s, %s, %s)
                    """

                    values = (subject_id, lesson_type, order, day, week)
                    self.cursor.execute(query, values)
                    schedule_count += 1

        self.connection.commit()
        print(f"[OK] Сгенерировано {schedule_count} записей расписания")

    def generate_attendance(self):
        """Генерация посещаемости и оценок за 2 недели"""
        print("[*] Генерация посещаемости...")

        start_date = datetime(2026, 2, 9)  # начало семестра
        attendance_count = 0

        for week in [1, 2]:
            for day_offset in range(7):
                current_date = start_date + timedelta(days=(week - 1) * 7 + day_offset)

                # Воскресенье пропускаем
                if current_date.isoweekday() == 7:
                    continue

                # Получаем расписание на этот день
                self.cursor.execute("""
                    SELECT * FROM schedule 
                    WHERE day_of_week = %s AND week_number = %s
                    ORDER BY lesson_order
                """, (current_date.isoweekday(), week))

                day_schedule = self.cursor.fetchall()

                for lesson in day_schedule:
                    for student_id in self.student_ids:
                        # Вероятность посещения 80-95%
                        is_present = random.random() < random.uniform(0.8, 0.95)

                        grade = None
                        if is_present and lesson[2] in ['практическое', 'лабораторная']:
                            # Оценка от 2 до 5 (2 - редко)
                            grade = random.choices([2, 3, 4, 5], weights=[0.05, 0.2, 0.4, 0.35])[0]

                        query = """
                            INSERT INTO attendance 
                            (student_id, subject_id, lesson_type, lesson_order, date, is_present, grade)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """

                        values = (
                            student_id, lesson[1], lesson[2], lesson[3],
                            current_date.date(), is_present, grade
                        )

                        try:
                            self.cursor.execute(query, values)
                            attendance_count += 1
                        except Exception as e:
                            # Пропускаем дубликаты
                            pass

        self.connection.commit()
        print(f"[OK] Сгенерировано {attendance_count} записей посещаемости")

    def generate_session(self):
        """Генерация результатов прошлой сессии с нужным распределением:
           80% - сдал с первого раза
           17% - пересдача
           3% - комиссия (пара человек)
        """
        print("[*] Генерация результатов сессии...")

        session_count = 0
        class_counts = {0: 0, 1: 0, 2: 0}  # 0-сдал, 1-пересдача, 2-комиссия

        for student_id in self.student_ids:
            for subject_id in self.subject_ids:
                # Тип экзамена
                exam_type = random.choices(
                    ['зачет', 'диф.зачет', 'экзамен'],
                    weights=[0.3, 0.3, 0.4]
                )[0]

                # Генерируем ОДНО случайное число для выбора класса
                rand = random.random()

                # 80% - сдал с первого раза
                if rand < 0.8:  # 80% - сдал
                    attempt = 1
                    if exam_type == 'зачет':
                        result = 'зачет'
                    else:
                        # Высокие оценки для сдавших
                        result = str(random.choices([3, 4, 5], weights=[0.1, 0.4, 0.5])[0])
                    status = 'сдал'
                    class_counts[0] += 1

                    query = """
                        INSERT INTO session 
                        (student_id, subject_id, exam_type, attempt, result, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    values = (student_id, subject_id, exam_type, attempt, result, status)
                    self.cursor.execute(query, values)
                    session_count += 1

                # 17% - пересдача (0.8 + 0.17 = 0.97)
                elif rand < 0.97:  # 17% - пересдача
                    attempt = 2
                    if exam_type == 'зачет':
                        # 85% шанс сдать пересдачу
                        if random.random() < 0.85:
                            result = 'зачет'
                            status = 'сдал'
                        else:
                            result = 'незачет'
                            status = 'пересдача'
                    else:
                        # Для экзамена
                        grade = random.choices([3, 4], weights=[0.7, 0.3])[0]
                        result = str(grade)
                        # 80% шанс сдать пересдачу
                        if random.random() < 0.8:
                            status = 'сдал'
                        else:
                            status = 'пересдача'
                    class_counts[1] += 1

                    query = """
                        INSERT INTO session 
                        (student_id, subject_id, exam_type, attempt, result, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    values = (student_id, subject_id, exam_type, attempt, result, status)
                    self.cursor.execute(query, values)
                    session_count += 1

                # 3% - комиссия (всего пара человек)
                else:  # 3% - комиссия
                    attempt = 3
                    if exam_type == 'зачет':
                        # 30% шанс сдать комиссию
                        if random.random() < 0.3:
                            result = 'зачет'
                            status = 'сдал'
                        else:
                            result = 'незачет'
                            status = 'комиссия'
                    else:
                        # Для экзамена
                        if random.random() < 0.3:  # 30% сдают на 3
                            result = '3'
                            status = 'сдал'
                        else:
                            result = '2'
                            status = 'комиссия'
                    class_counts[2] += 1

                    query = """
                        INSERT INTO session 
                        (student_id, subject_id, exam_type, attempt, result, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    values = (student_id, subject_id, exam_type, attempt, result, status)
                    self.cursor.execute(query, values)
                    session_count += 1

        self.connection.commit()
        print(f"[OK] Сгенерировано {session_count} записей сессии")
        print(f"   Распределение по попыткам:")
        print(f"      0 (сдал): {class_counts[0]}")
        print(f"      1 (пересдача): {class_counts[1]}")
        print(f"      2 (комиссия): {class_counts[2]}")
        total = class_counts[0] + class_counts[1] + class_counts[2]
        print(
            f"   Проценты: сдал {class_counts[0] / total * 100:.1f}%, пересдача {class_counts[1] / total * 100:.1f}%, комиссия {class_counts[2] / total * 100:.1f}%")

    def show_statistics(self):
        """Показать статистику сгенерированных данных"""
        print("\n" + "=" * 60)
        print("СТАТИСТИКА СГЕНЕРИРОВАННЫХ ДАННЫХ")
        print("=" * 60)

        # Количество студентов
        self.cursor.execute("SELECT COUNT(*) FROM students")
        students_count = self.cursor.fetchone()[0]
        print(f"👥 Студентов: {students_count}")

        # Количество дисциплин
        self.cursor.execute("SELECT COUNT(*) FROM subjects")
        subjects_count = self.cursor.fetchone()[0]
        print(f"📚 Дисциплин: {subjects_count}")

        # Количество записей в расписании
        self.cursor.execute("SELECT COUNT(*) FROM schedule")
        schedule_count = self.cursor.fetchone()[0]
        print(f"📅 Записей в расписании: {schedule_count}")

        # Количество записей посещаемости
        self.cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = self.cursor.fetchone()[0]
        print(f"📊 Записей посещаемости: {attendance_count}")

        # Количество записей в сессии
        self.cursor.execute("SELECT COUNT(*) FROM session")
        session_count = self.cursor.fetchone()[0]
        print(f"🎓 Записей в сессии: {session_count}")

        # Статистика посещаемости
        self.cursor.execute("""
            SELECT 
                ROUND(AVG(is_present) * 100, 1) as avg_attendance,
                SUM(CASE WHEN grade IS NOT NULL THEN 1 ELSE 0 END) as graded_lessons
            FROM attendance
        """)
        stats = self.cursor.fetchone()
        print(f"📈 Средняя посещаемость: {stats[0]}%")
        print(f"📝 Оцененных занятий: {stats[1]}")

        # Статистика сессии
        self.cursor.execute("""
            SELECT status, COUNT(*) FROM session GROUP BY status
        """)
        print("\n📊 Результаты сессии:")
        for status, count in self.cursor.fetchall():
            print(f"  {status}: {count}")

        print("=" * 60)

    def clear_tables(self):
        """Очистка таблиц перед генерацией"""
        try:
            self.cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            self.cursor.execute("TRUNCATE TABLE attendance")
            self.cursor.execute("TRUNCATE TABLE session")
            self.cursor.execute("TRUNCATE TABLE schedule")
            self.cursor.execute("TRUNCATE TABLE students")
            self.cursor.execute("TRUNCATE TABLE subjects")
            self.cursor.execute("SET FOREIGN_KEY_CHECKS=1")
            self.connection.commit()
            print("[OK] Таблицы очищены")
        except mysql.connector.Error as e:
            print(f"[WARN] Ошибка при очистке таблиц: {e}")

    def generate_all(self):
        """Генерация всех данных"""
        print("\n" + "=" * 60)
        print("ГЕНЕРАЦИЯ ДАННЫХ ДЛЯ ИНТЕЛЛЕКТУАЛЬНОГО АГЕНТА")
        print("=" * 60)

        # Сначала создаем БД, если её нет
        if not self.create_database_if_not_exists():
            return False

        # Подключаемся к БД
        if not self.connect():
            return False

        # Создаем таблицы
        if not self.create_tables():
            self.disconnect()
            return False

        # Очищаем таблицы
        self.clear_tables()

        # Генерируем данные
        self.generate_students()
        self.generate_subjects()
        self.generate_schedule()
        self.generate_attendance()
        self.generate_session()

        # Показываем статистику
        self.show_statistics()

        self.disconnect()
        print("\n[OK] Генерация данных завершена успешно!")
        return True


def main():
    """Точка входа для генератора"""
    generator = DataGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()