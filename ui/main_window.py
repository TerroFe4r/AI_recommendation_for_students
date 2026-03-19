#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Главное окно приложения (полная версия)
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from ui.student_view import StudentView
from ui.dean_view import DeanView


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self, role=None, user_id=None):
        super().__init__()
        self.role = role
        self.user_id = user_id

        self.initUI()
        self.show_content()

    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Интеллектуальный агент - Прогнозирование успеваемости")
        self.setGeometry(100, 100, 1200, 800)

        # Центральный виджет
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Основной layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def show_content(self):
        """Показ контента в зависимости от роли"""
        self.create_menu_bar()

        if self.role == 'dean':
            self.main_layout.addWidget(DeanView())
            self.statusBar().showMessage("Деканат", 3000)
        else:
            self.main_layout.addWidget(StudentView(self.user_id))
            self.statusBar().showMessage(f"Студент ID: {self.user_id}", 3000)

    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()
        # Меню Справка
        help_menu = menubar.addMenu("Справка")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def logout(self):
        """Выход из аккаунта"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.close()

    def show_about(self):
        """О программе"""
        QMessageBox.about(
            self,
            "О программе",
            """<h2>Интеллектуальный агент</h2>
            <p><b>Прогнозирование успеваемости студентов</b></p>
            <p>Версия: 1.0</p>
            <p>Разработано в рамках курсовой работы</p>
            <br>
            <p><b>Функции:</b></p>
            <ul>
                <li>Прогнозирование успеваемости на основе ML</li>
                <li>Классификация студентов по группам риска</li>
                <li>Персонализированные рекомендации</li>
                <li>Отчеты для деканата</li>
                <li>Авторизация с разделением ролей</li>
            </ul>
            <br>
            <p>© 2026</p>"""
        )