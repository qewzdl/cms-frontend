import sys
from PySide6.QtWidgets import QApplication
from ui.login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())
