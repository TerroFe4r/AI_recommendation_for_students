#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Главный файл запуска приложения
"""

import sys
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt


from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog
from ui.styles import GLOBAL_STYLE


def main():
    """Точка входа в приложение"""

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setStyle('Fusion')

    app.setStyleSheet(GLOBAL_STYLE)

    dialog = LoginDialog()

    if dialog.exec_() == QDialog.Accepted:
        window = MainWindow(dialog.role, dialog.user_id)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
