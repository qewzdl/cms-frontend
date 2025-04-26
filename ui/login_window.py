import os, sys
# ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Window Settings
LOGIN_WINDOW_MIN_WIDTH = 300
LOGIN_WINDOW_MIN_HEIGHT = 200
LOGIN_WINDOW_RESIZABLE = False

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtWidgets import QApplication
import style
from api.client import ApiClient
from ui.main_window import MainWindow

class LoginWindow(QWidget):
    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client or ApiClient(parent=self)
        # apply window hints
        self.setMinimumSize(LOGIN_WINDOW_MIN_WIDTH, LOGIN_WINDOW_MIN_HEIGHT)
        if not LOGIN_WINDOW_RESIZABLE:
            self.setFixedSize(self.minimumSize())
        self.setWindowTitle("Login")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Login:"))
        self.login_input = QLineEdit()
        layout.addWidget(self.login_input)
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        btn = QPushButton("Login")
        btn.clicked.connect(self._login)
        layout.addWidget(btn)
        self.setLayout(layout)

    def _login(self):
        login = self.login_input.text().strip()
        pwd = self.password_input.text().strip()
        if not login or not pwd:
            QMessageBox.warning(self, "Error", "Enter login and password")
            return
        try:
            self.api.login(login, pwd)
            self.main_window = MainWindow(self.api)
            self.main_window.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Login Failed", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(style.load_styles())
    # mock client for standalone testing
    class MockApiClient(ApiClient):
        def __init__(self):
            super().__init__()
        def login(self, login, password):
            self.access_token = "mock_access"
            self.refresh_token = "mock_refresh"
            self.save_tokens()
            return {"access_token": self.access_token, "refresh_token": self.refresh_token}

    api = MockApiClient()
    window = LoginWindow(api)
    window.show()
    sys.exit(app.exec())