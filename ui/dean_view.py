#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Полная версия просмотра для деканата
"""

import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database.db_connector import DatabaseConnector
from agents.recommendation_agent import RecommendationAgent


class DeanView(QWidget):
    """Виджет для деканата"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnector()
        self.agent = RecommendationAgent()
        self.students = []
        self.predictions = []
        self.initUI()
        self.load_data()

    def initUI(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Верхняя панель с заголовком
        title_label = QLabel("Панель управления деканата")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Карточки статистики
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Карточка "Всего студентов"
        self.total_card = self.create_stat_card("Всего студентов", "0", "#2196F3")
        stats_layout.addWidget(self.total_card)

        # Карточка "Сдадут"
        self.passed_card = self.create_stat_card("✅ Сдадут", "0", "#4CAF50")
        stats_layout.addWidget(self.passed_card)

        # Карточка "Пересдача"
        self.retake_card = self.create_stat_card("📚 Пересдача", "0", "#FF9800")
        stats_layout.addWidget(self.retake_card)

        # Карточка "Группа риска"
        self.risk_card = self.create_stat_card("⚠️ Группа риска", "0", "#f44336")
        stats_layout.addWidget(self.risk_card)

        main_layout.addLayout(stats_layout)

        # Панель фильтров
        filter_frame = QFrame()
        filter_frame.setStyleSheet("QFrame { background-color: white; border-radius: 5px; padding: 10px; }")
        filter_layout = QHBoxLayout(filter_frame)

        filter_layout.addWidget(QLabel("Фильтр:"))

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Все студенты", "Группа риска", "Пересдача", "Сдадут"])
        self.filter_combo.currentTextChanged.connect(self.filter_students)
        self.filter_combo.setMinimumWidth(150)
        filter_layout.addWidget(self.filter_combo)

        filter_layout.addWidget(QLabel("Поиск:"))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ID, фамилия или имя...")
        self.search_edit.textChanged.connect(self.filter_students)
        self.search_edit.setMinimumWidth(200)
        filter_layout.addWidget(self.search_edit)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setMinimumWidth(100)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        report_btn = QPushButton("Отчет PDF")
        report_btn.setMinimumWidth(120)
        report_btn.setCursor(Qt.PointingHandCursor)
        report_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        report_btn.clicked.connect(self.generate_pdf_report)
        filter_layout.addWidget(report_btn)

        main_layout.addWidget(filter_frame)

        self.students_table = QTableWidget()
        self.students_table.setColumnCount(8)
        self.students_table.setHorizontalHeaderLabels([
            "ID", "Фамилия", "Имя", "Прогноз", "Вероятность",
            "Ср. балл", "Факторы риска", "Действие"
        ])
        self.students_table.horizontalHeader().setStretchLastSection(True)
        self.students_table.setAlternatingRowColors(True)
        self.students_table.setSortingEnabled(True)
        self.students_table.setWordWrap(True)
        self.students_table.setTextElideMode(Qt.ElideNone)
        self.students_table.setStyleSheet("""
            QTableView {
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #2196F3;
                gridline-color: #dddddd;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: 1px solid #dddddd;
                font-weight: bold;
            }
        """)

        # Устанавливаем ширину колонок
        self.students_table.setColumnWidth(0, 50)  # ID
        self.students_table.setColumnWidth(1, 120)  # Фамилия
        self.students_table.setColumnWidth(2, 120)  # Имя
        self.students_table.setColumnWidth(3, 100)  # Прогноз
        self.students_table.setColumnWidth(4, 100)  # Вероятность
        self.students_table.setColumnWidth(5, 70)  # Ср. балл
        self.students_table.setColumnWidth(6, 200)  # Факторы риска
        # 8 колонка (Действие) растянется автоматически

        self.students_table.verticalHeader().setDefaultSectionSize(60)

        main_layout.addWidget(self.students_table)

    def create_stat_card(self, title, value, color):
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

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        layout.addWidget(value_label)

        if "Всего" in title:
            self.total_value = value_label
        elif "Сдадут" in title:
            self.passed_value = value_label
        elif "Пересдача" in title:
            self.retake_value = value_label
        elif "риска" in title:
            self.risk_value = value_label

        return card

    def load_data(self):
        """Загрузка данных"""
        try:
            if not self.db.connect():
                QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
                return

            self.students = self.db.get_students()
            print(f"Загружено студентов из БД: {len(self.students)}")

            self.predictions = []
            for student in self.students:
                try:
                    pred = self.agent.predict_student(student['id'])
                    if pred:
                        self.predictions.append(pred)
                        print(f"Прогноз для студента {student['id']}: класс {pred['predicted_class']}")
                except Exception as e:
                    print(f"Ошибка прогноза для студента {student['id']}: {e}")
                    continue

            self.db.disconnect()

            print(f"Всего прогнозов: {len(self.predictions)}")

            self.update_statistics()

            self.update_students_table()

        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def update_statistics(self):
        """Обновление статистики"""
        total = len(self.predictions)
        passed = sum(1 for p in self.predictions if p['predicted_class'] == 0)
        retake = sum(1 for p in self.predictions if p['predicted_class'] == 1)
        commission = sum(1 for p in self.predictions if p['predicted_class'] == 2)
        expelled = sum(1 for p in self.predictions if p['predicted_class'] == 3)

        self.total_value.setText(str(total))
        self.passed_value.setText(str(passed))
        self.retake_value.setText(str(retake))
        self.risk_value.setText(str(commission + expelled))

        print(
            f"Статистика: всего={total}, сдадут={passed}, пересдача={retake}, комиссия={commission}, отчислен={expelled}")

    def update_students_table(self, filtered_indices=None):
        """Обновление таблицы студентов"""
        try:
            if filtered_indices is None:
                filtered_indices = range(len(self.predictions))

            self.students_table.setRowCount(0)
            self.students_table.setRowCount(len(filtered_indices))

            self.students_table.setSortingEnabled(False)

            valid_rows = 0
            for i, idx in enumerate(filtered_indices):
                try:
                    pred = self.predictions[idx]
                    student = next((s for s in self.students if s['id'] == pred['student_id']), None)

                    if not student:
                        continue

                    id_item = QTableWidgetItem(str(pred['student_id']))
                    self.students_table.setItem(valid_rows, 0, id_item)

                    last_name_item = QTableWidgetItem(student['last_name'])
                    self.students_table.setItem(valid_rows, 1, last_name_item)

                    first_name_item = QTableWidgetItem(student['first_name'])
                    self.students_table.setItem(valid_rows, 2, first_name_item)

                    class_names = ['Сдаст', 'Пересдача', 'Комиссия']
                    colors = ['#4CAF50', '#FF9800', '#f44336', '#8B0000']

                    pred_class = pred['predicted_class']
                    if 0 <= pred_class <= 3:
                        pred_item = QTableWidgetItem(class_names[pred_class])
                        pred_item.setForeground(QColor(colors[pred_class]))
                        if pred_class >= 2:
                            font = QFont()
                            font.setBold(True)
                            pred_item.setFont(font)
                    else:
                        pred_item = QTableWidgetItem("❓ Неизвестно")
                        pred_item.setForeground(QColor(128, 128, 128))
                    self.students_table.setItem(valid_rows, 3, pred_item)

                    prob = pred['class_probabilities'].get(pred_class, 0) * 100
                    prob_item = QTableWidgetItem(f"{prob:.1f}%")
                    self.students_table.setItem(valid_rows, 4, prob_item)

                    grade_item = QTableWidgetItem(f"{pred['predicted_grade']:.2f}")
                    self.students_table.setItem(valid_rows, 5, grade_item)

                    try:
                        factors = self.agent.get_risk_factors(pred['features'])
                        factors_text = ", ".join(factors[:3]) if factors else "Нет"
                    except Exception as e:
                        factors_text = f"Ошибка: {str(e)[:20]}"
                    self.students_table.setItem(valid_rows, 6, QTableWidgetItem(factors_text))


                    btn = QPushButton("Рекомендации")
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2196F3;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            padding: 5px 10px;
                            font-size: 11px;
                            min-width: 80px;
                        }
                        QPushButton:hover {
                            background-color: #1976D2;
                        }
                    """)
                    btn.clicked.connect(lambda checked, sid=pred['student_id']: self.show_recommendations(sid))
                    self.students_table.setCellWidget(valid_rows, 7, btn)

                    valid_rows += 1

                except Exception as e:
                    print(f"Ошибка обработки строки {i}: {e}")
                    continue

            if valid_rows < len(filtered_indices):
                self.students_table.setRowCount(valid_rows)

            self.students_table.setSortingEnabled(True)

            self.students_table.resizeColumnsToContents()
            self.students_table.setColumnWidth(0, 50)  # ID
            self.students_table.setColumnWidth(1, 120)  # Фамилия
            self.students_table.setColumnWidth(2, 120)  # Имя
            self.students_table.setColumnWidth(3, 100)  # Прогноз
            self.students_table.setColumnWidth(4, 100)  # Вероятность
            self.students_table.setColumnWidth(5, 70)  # Ср. балл
            self.students_table.setColumnWidth(6, 200)  # Факторы риска
            self.students_table.setColumnWidth(7, 50)  # Статус

            self.students_table.verticalHeader().setDefaultSectionSize(60)

            self.students_table.viewport().update()

        except Exception as e:
            print(f"Ошибка обновления таблицы: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка обновления таблицы: {str(e)}")

    def filter_students(self):
        """Фильтрация студентов"""
        filter_text = self.filter_combo.currentText()
        search_text = self.search_edit.text().lower()

        filtered_indices = []

        for idx, pred in enumerate(self.predictions):
            student = next((s for s in self.students if s['id'] == pred['student_id']), None)
            if not student:
                continue

            if filter_text == "Группа риска" and pred['predicted_class'] < 2:
                continue
            if filter_text == "Пересдача" and pred['predicted_class'] != 1:
                continue
            if filter_text == "Сдадут" and pred['predicted_class'] != 0:
                continue

            if search_text:
                if (str(pred['student_id']) not in search_text and
                        search_text not in student['last_name'].lower() and
                        search_text not in student['first_name'].lower()):
                    continue

            filtered_indices.append(idx)

        self.update_students_table(filtered_indices)

    def show_recommendations(self, student_id):
        """Показать рекомендации для студента"""
        recommendations = self.agent.generate_recommendations(student_id, use_gigachat=False)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Рекомендации для студента {student_id}")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Arial", 11))
        text_edit.setText(recommendations)
        layout.addWidget(text_edit)

        btn = QPushButton("Закрыть")
        btn.setMinimumHeight(35)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)

        dialog.exec_()


    def generate_pdf_report(self):
        """Генерация PDF-отчета для деканата"""
        try:
            if not hasattr(self, 'students') or not self.students or not hasattr(self,
                                                                                 'predictions') or not self.predictions:
                QMessageBox.warning(self, "Предупреждение", "Нет данных для формирования отчета")
                return

            from utils.report import ReportGenerator
            report_gen = ReportGenerator()

            filepath = report_gen.generate_dean_report_pdf(self.students, self.predictions)

            reply = QMessageBox.question(
                self,
                "Отчет создан",
                f"Отчет сохранен:\n{filepath}\n\nОткрыть папку с отчетом?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                report_dir = str(Path(filepath).parent)
                os.startfile(report_dir)

        except ImportError:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Библиотека ReportLab не установлена.\nУстановите: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Не удалось сгенерировать отчет:\n{str(e)}"
            )