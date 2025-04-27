import sys
import os
from PySide6.QtWidgets import QApplication
import style
from api.client import ApiClient
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(style.load_styles(theme="light"))

    api = ApiClient()
    if api.access_token and api.refresh_access():
        window = MainWindow(api, api.username)
    else:
        api.clear_tokens()
        window = LoginWindow(api)

    window.show()
    sys.exit(app.exec())