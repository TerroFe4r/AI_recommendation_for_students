#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Стили оформления для интерфейса
"""

COLORS = {
    'bg_dark': '#2b2b2b',
    'bg_light': '#f5f5f5',
    'primary': '#2196F3',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'danger': '#f44336',
    'info': '#00BCD4',
    'text_dark': '#333333',
    'text_light': '#ffffff',
    'border': '#dddddd'
}

GLOBAL_STYLE = """
/* Главное окно */
QMainWindow {
    background-color: #f5f5f5;
}

/* Меню */
QMenuBar {
    background-color: white;
    border-bottom: 1px solid #dddddd;
    padding: 2px;
}
QMenuBar::item {
    padding: 5px 10px;
    background-color: transparent;
}
QMenuBar::item:selected {
    background-color: #e3f2fd;
    border-radius: 3px;
}

/* Статус бар */
QStatusBar {
    background-color: white;
    border-top: 1px solid #dddddd;
    color: #666666;
}

/* Таблицы */
QTableView {
    background-color: white;
    alternate-background-color: #f9f9f9;
    gridline-color: #dddddd;
    selection-background-color: #bbdefb;
    selection-color: #333333;
    font-size: 11px;
}
QTableView::item {
    padding: 8px;
    border-bottom: 1px solid #eeeeee;
}
QHeaderView::section {
    background-color: #f5f5f5;
    padding: 8px;
    border: 1px solid #dddddd;
    border-top: none;
    font-weight: bold;
    font-size: 11px;
}

/* Кнопки */
QPushButton {
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 15px;
    font-size: 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1976D2;
}
QPushButton:pressed {
    background-color: #0D47A1;
}
QPushButton:disabled {
    background-color: #bbbbbb;
}

/* Опасные кнопки */
QPushButton.danger {
    background-color: #f44336;
}
QPushButton.danger:hover {
    background-color: #d32f2f;
}

/* Поля ввода */
QLineEdit {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 8px;
    background-color: white;
    font-size: 12px;
}
QLineEdit:focus {
    border: 2px solid #2196F3;
}

/* Выпадающие списки */
QComboBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 8px;
    background-color: white;
    font-size: 12px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #666666;
    margin-right: 5px;
}

/* Вкладки */
QTabWidget::pane {
    border: 1px solid #dddddd;
    background-color: white;
    border-radius: 5px;
}
QTabBar::tab {
    background-color: #f5f5f5;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid #2196F3;
    font-weight: bold;
}

/* Карточки */
QFrame.card {
    background-color: white;
    border-radius: 10px;
    padding: 15px;
}
QFrame.card QLabel#title {
    font-size: 14px;
    color: #666666;
    font-weight: normal;
}
QFrame.card QLabel#value {
    font-size: 24px;
    color: #2196F3;
    font-weight: bold;
}

/* Прогресс-бар */
QProgressBar {
    border: 1px solid #dddddd;
    border-radius: 4px;
    text-align: center;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #2196F3;
    border-radius: 3px;
}
"""

LOGIN_DIALOG_STYLE = """
QDialog {
    background-color: white;
}
QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #2196F3;
}
QLabel#subtitle {
    color: #666666;
    font-size: 11px;
}
QLabel#info {
    background-color: #f5f5f5;
    border-radius: 5px;
    padding: 10px;
    color: #666666;
    font-size: 10px;
}
"""