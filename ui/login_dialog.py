#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Диалог авторизации
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from ui.styles import LOGIN_DIALOG_STYLE
from database.db_connector import DatabaseConnector
from utils.auth import AuthManager


class LoginDialog(QDialog):
    """Диалог входа в систему"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Атрибуты
        self.db = DatabaseConnector()
        self.auth = AuthManager(self.db)
        self.role = None
        self.user_id = None

        # Настройки окна
        self.setWindowTitle("Вход в систему")
        self.setSizeGripEnabled(False)
        self.setMaximumSize(600, 450)
        self.setMinimumSize(600, 450)
        self.setModal(True)

        # Создаем интерфейс
        self.initUI()

    def initUI(self):
        """Создание интерфейса"""
        # Основной layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("Интеллектуальный агент\nпрогнозирования успеваемости")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        layout.addWidget(title)

        # Подзаголовок
        subtitle = QLabel("Разработал Горчуков Денис ИС222")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666666; margin-bottom: 20px; font-size: 16px;")
        layout.addWidget(subtitle)

        # Поля ввода
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Логин")
        self.login_edit.setMinimumHeight(38)
        self.login_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dddddd;
                border-radius: 5px;
                padding: 8px;
                font-size: 16px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        layout.addWidget(self.login_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Пароль")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(38)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dddddd;
                border-radius: 5px;
                padding: 8px;
                font-size: 16px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        layout.addWidget(self.password_edit)

        # Кнопка входа
        self.login_btn = QPushButton("Войти")
        self.login_btn.setMinimumHeight(42)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        # Статус
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #f44336; font-size: 11px; margin-top: 5px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.setStyleSheet(LOGIN_DIALOG_STYLE)
        self.login_edit.returnPressed.connect(self.handle_login)
        self.password_edit.returnPressed.connect(self.handle_login)

    def handle_login(self):
        """Обработка входа"""
        login = self.login_edit.text().strip()
        password = self.password_edit.text()

        if not login or not password:
            self.status_label.setText("Введите логин и пароль")
            return

        # Подключаемся к БД
        if not self.db.connect():
            self.status_label.setText("Ошибка подключения к базе данных")
            return

        # Аутентификация
        role, user_id = self.auth.authenticate(login, password)
        self.db.disconnect()

        if role:
            self.role = role
            self.user_id = user_id
            self.accept()
        else:
            self.status_label.setText("Неверный логин или пароль")
            self.password_edit.clear()
            self.password_edit.setFocus()