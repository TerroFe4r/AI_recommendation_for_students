#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Полная версия просмотра для студента
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database.db_connector import DatabaseConnector
from agents.recommendation_agent import RecommendationAgent


class StudentView(QWidget):
    """Виджет для студента"""

    def __init__(self, student_id, parent=None):
        super().__init__(parent)
        self.student_id = student_id
        self.db = DatabaseConnector()
        self.agent = RecommendationAgent()
        self.student_data = None
        self.session_table = None
        self.initUI()
        self.load_data()

    def initUI(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Верхняя панель с приветствием
        top_panel = QFrame()
        top_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        top_layout = QHBoxLayout(top_panel)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(50, 50)
        self.avatar_label.setStyleSheet("""
            background-color: #2196F3;
            border-radius: 25px;
            color: white;
            font-size: 20px;
            font-weight: bold;
            qproperty-alignment: AlignCenter;
        """)
        top_layout.addWidget(self.avatar_label)

        self.welcome_label = QLabel("Загрузка данных...")
        self.welcome_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-left: 10px;")
        top_layout.addWidget(self.welcome_label)

        top_layout.addStretch()

        main_layout.addWidget(top_panel)

        # Карточки с прогнозами
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        # Карточка прогноза
        self.prediction_card = self.create_card(
            "Прогноз",
            "Загрузка...",
            "#4CAF50"
        )
        cards_layout.addWidget(self.prediction_card)

        # Карточка среднего балла
        self.grade_card = self.create_card(
            "Средний балл",
            "Загрузка...",
            "#2196F3"
        )
        cards_layout.addWidget(self.grade_card)

        # Карточка риска
        self.risk_card = self.create_card(
            "Уровень риска",
            "Загрузка...",
            "#FF9800"
        )
        cards_layout.addWidget(self.risk_card)

        main_layout.addLayout(cards_layout)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dddddd;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 12px 25px;  /* УВЕЛИЧЕНО: было 8px 16px, стало 12px 25px */
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 13px;      /* ДОБАВЛЕНО: размер шрифта */
                font-weight: bold;     /* ДОБАВЛЕНО: жирный шрифт */
                min-width: 120px;      /* ДОБАВЛЕНО: минимальная ширина */
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 3px solid #2196F3;  /* УВЕЛИЧЕНО: было 2px, стало 3px */
                color: #2196F3;         /* ДОБАВЛЕНО: цвет текста выбранной вкладки */
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;  /* ДОБАВЛЕНО: эффект при наведении */
            }
        """)

        # Вкладка с рекомендациями
        self.recommendations_tab = QWidget()
        self.setup_recommendations_tab()
        self.tabs.addTab(self.recommendations_tab, "Рекомендации")

        # Вкладка с посещаемостью
        self.attendance_tab = QWidget()
        self.setup_attendance_tab()
        self.tabs.addTab(self.attendance_tab, "Посещаемость")

        # Вкладка с оценками
        self.grades_tab = QWidget()
        self.setup_grades_tab()
        self.tabs.addTab(self.grades_tab, "Оценки")

        # Вкладка с сессией
        self.session_tab = QWidget()
        self.setup_session_tab()
        self.tabs.addTab(self.session_tab, "Сессия")

        main_layout.addWidget(self.tabs)
        # Настройка таблиц
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attendance_table.setAlternatingRowColors(True)
        self.attendance_table.setStyleSheet("""
            QTableView {
                border: 1px solid #dddddd;
                border-radius: 4px;
            }
        """)

        self.grades_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.grades_table.setAlternatingRowColors(True)
        self.grades_table.setStyleSheet("""
            QTableView {
                border: 1px solid #dddddd;
                border-radius: 4px;
            }
        """)
        # Кнопка обновления
        refresh_btn = QPushButton("Обновить данные")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        main_layout.addWidget(refresh_btn)

    def create_card(self, title, value, color):
        """Создание карточки статистики"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                padding: 15px;
                border-left: 5px solid {color};
            }}
        """)

        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #666666;")
        layout.addWidget(title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.value_label)

        if title == "Прогноз":
            self.prediction_value = self.value_label
        elif title == "Средний балл":
            self.grade_value = self.value_label
        elif title == "Уровень риска":
            self.risk_value = self.value_label

        return card

    def setup_recommendations_tab(self):
        """Настройка вкладки с рекомендациями"""
        layout = QVBoxLayout(self.recommendations_tab)

        # Текст рекомендаций
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setFont(QFont("Arial", 11))
        self.recommendations_text.setLineWrapMode(QTextEdit.WidgetWidth)  # ПЕРЕНОС ПО ШИРИНЕ
        self.recommendations_text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)  # ПЕРЕНОС СЛОВ
        layout.addWidget(self.recommendations_text)

        # Кнопка генерации
        generate_btn = QPushButton("Сгенерировать новые рекомендации")
        generate_btn.setMinimumHeight(35)
        generate_btn.setCursor(Qt.PointingHandCursor)
        generate_btn.setStyleSheet("""
               QPushButton {
                   background-color: #4CAF50;
                   color: white;
                   border: none;
                   border-radius: 4px;
                   font-weight: bold;
               }
               QPushButton:hover {
                   background-color: #45a049;
               }
           """)
        generate_btn.clicked.connect(self.generate_recommendations)
        layout.addWidget(generate_btn)

    def setup_attendance_tab(self):
        """Настройка вкладки с посещаемостью"""
        layout = QVBoxLayout(self.attendance_tab)

        # Таблица посещаемости
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)
        self.attendance_table.setHorizontalHeaderLabels(["Предмет", "Тип", "Дата", "Посещение"])
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attendance_table.setAlternatingRowColors(True)
        layout.addWidget(self.attendance_table)

    def setup_grades_tab(self):
        """Настройка вкладки с оценками"""
        layout = QVBoxLayout(self.grades_tab)

        # Таблица оценок
        self.grades_table = QTableWidget()
        self.grades_table.setColumnCount(4)
        self.grades_table.setHorizontalHeaderLabels(["Предмет", "Тип", "Дата", "Оценка"])
        self.grades_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.grades_table.setAlternatingRowColors(True)
        layout.addWidget(self.grades_table)

    def setup_session_tab(self):
        """Настройка вкладки с результатами сессии"""
        layout = QVBoxLayout(self.session_tab)

        # Таблица сессии
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(5)
        self.session_table.setHorizontalHeaderLabels(["Предмет", "Тип", "Попытка", "Результат", "Статус"])
        self.session_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.session_table.setAlternatingRowColors(True)
        self.session_table.setWordWrap(True)
        self.session_table.setTextElideMode(Qt.ElideNone)
        layout.addWidget(self.session_table)

    def load_data(self):
        """Загрузка данных студента"""
        if not self.db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        student = self.db.get_student_by_id(self.student_id)
        if student:
            full_name = f"{student['last_name']} {student['first_name']} {student['middle_name'] or ''}"
            self.welcome_label.setText(f"Здравствуйте, {student['first_name']}!")

            initials = (student['first_name'][0] + student['last_name'][0]).upper()
            self.avatar_label.setText(initials)

        session_results = self.db.get_session_results(self.student_id)

        is_expelled = False
        if session_results:
            for record in session_results:
                if record['status'] == 'отчислен':
                    is_expelled = True
                    break

        prediction = self.agent.predict_student(self.student_id)

        if prediction:
            if is_expelled:
                self.prediction_value.setText("ОТЧИСЛЕН")
                self.prediction_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #8B0000;")

                self.risk_value.setText("ОТЧИСЛЕН")
                self.risk_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #8B0000;")
            else:
                class_names = ['Сдаст', 'Пересдача', 'Комиссия', 'ОТЧИСЛЕН']
                colors = ['#4CAF50', '#FF9800', '#f44336', '#000000']

                if prediction['predicted_class'] == 3:
                    self.prediction_value.setText("⚠️ ОТЧИСЛЕН (прогноз)")
                    self.prediction_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #8B0000;")
                else:
                    self.prediction_value.setText(class_names[prediction['predicted_class']])
                    self.prediction_value.setStyleSheet(
                        f"font-size: 20px; font-weight: bold; color: {colors[prediction['predicted_class']]};")

                risk_level = "Низкий" if prediction['predicted_class'] == 0 else \
                    "Средний" if prediction['predicted_class'] == 1 else \
                        "Высокий" if prediction['predicted_class'] == 2 else "Критический"
                risk_color = "#4CAF50" if prediction['predicted_class'] == 0 else \
                    "#FF9800" if prediction['predicted_class'] == 1 else \
                        "#f44336" if prediction['predicted_class'] == 2 else "#8B0000"

                self.risk_value.setText(risk_level)
                self.risk_value.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {risk_color};")

            self.grade_value.setText(f"{prediction['predicted_grade']:.2f}")

        attendance = self.db.get_attendance(self.student_id)
        self.attendance_table.setRowCount(len(attendance))
        for i, record in enumerate(attendance):
            self.attendance_table.setItem(i, 0, QTableWidgetItem(str(record.get('subject_name', 'Неизвестно'))))
            self.attendance_table.setItem(i, 1, QTableWidgetItem(record['lesson_type']))
            self.attendance_table.setItem(i, 2, QTableWidgetItem(str(record['date'])))

            present_item = QTableWidgetItem("✅ Посетил" if record['is_present'] else "❌ Отсутствовал")
            if record['is_present']:
                present_item.setForeground(QColor(76, 175, 80))
            else:
                present_item.setForeground(QColor(244, 67, 54))
            self.attendance_table.setItem(i, 3, present_item)

        grades = [a for a in attendance if a.get('grade') is not None]
        self.grades_table.setRowCount(len(grades))
        for i, record in enumerate(grades):
            self.grades_table.setItem(i, 0, QTableWidgetItem(str(record.get('subject_name', 'Неизвестно'))))
            self.grades_table.setItem(i, 1, QTableWidgetItem(record['lesson_type']))
            self.grades_table.setItem(i, 2, QTableWidgetItem(str(record['date'])))

            grade_item = QTableWidgetItem(str(record['grade']))
            if record['grade'] >= 4:
                grade_item.setForeground(QColor(76, 175, 80))
            elif record['grade'] == 3:
                grade_item.setForeground(QColor(255, 152, 0))
            else:
                grade_item.setForeground(QColor(244, 67, 54))
            self.grades_table.setItem(i, 3, grade_item)

        self.session_table.setRowCount(len(session_results))
        for i, record in enumerate(session_results):
            subject_query = "SELECT name FROM subjects WHERE id = %s"
            subject_result = self.db.fetch_one(subject_query, (record['subject_id'],))
            subject_name = subject_result['name'] if subject_result else f"Предмет {record['subject_id']}"

            self.session_table.setItem(i, 0, QTableWidgetItem(subject_name))
            self.session_table.setItem(i, 1, QTableWidgetItem(record['exam_type']))

            # Попытка
            attempt_text = {1: "Первичная", 2: "Пересдача", 3: "Комиссия"}.get(record['attempt'],
                                                                               str(record['attempt']))
            self.session_table.setItem(i, 2, QTableWidgetItem(attempt_text))

            # Результат
            result_item = QTableWidgetItem(record['result'])
            if record['status'] == 'сдал':
                result_item.setForeground(QColor(76, 175, 80))
            else:
                result_item.setForeground(QColor(244, 67, 54))
            self.session_table.setItem(i, 3, result_item)

            # Статус
            status_item = QTableWidgetItem(record['status'])
            if record['status'] == 'сдал':
                status_item.setForeground(QColor(76, 175, 80))
            elif record['status'] == 'пересдача':
                status_item.setForeground(QColor(255, 152, 0))
            elif record['status'] == 'комиссия':
                status_item.setForeground(QColor(244, 67, 54))
            else:  # отчислен
                status_item.setForeground(QColor(139, 0, 0))
                font = QFont()
                font.setBold(True)
                status_item.setFont(font)
            self.session_table.setItem(i, 4, status_item)

        self.attendance_table.resizeRowsToContents()
        self.attendance_table.resizeColumnsToContents()
        self.grades_table.resizeRowsToContents()
        self.grades_table.resizeColumnsToContents()
        self.session_table.resizeRowsToContents()
        self.session_table.resizeColumnsToContents()

        self.db.disconnect()

    def generate_recommendations(self):
        """Генерация рекомендаций"""
        self.recommendations_text.setText("Генерация рекомендаций...")
        QApplication.processEvents()

        recommendations = self.agent.generate_recommendations(self.student_id, use_gigachat=False)
        self.recommendations_text.setText(recommendations)