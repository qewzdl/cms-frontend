from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from api.client import ApiClient
from ui.main_window import MainWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.api = ApiClient(parent=self)
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
