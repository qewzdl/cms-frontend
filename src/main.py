# main.py
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QListWidget, QTextEdit)
from PySide6.QtCore import QTimer
from api import ApiClient

BASE_URL = "https://savychk1.fvds.ru"

class LoginWindow(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.setWindowTitle("Login")
        self.resize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Login")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login)
        self.status_label = QLabel()
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def handle_login(self):
        login = self.login_input.text()
        pwd = self.password_input.text()
        try:
            self.api.login(login, pwd)
            self.close()
            self.chat_window = ChatWindow(self.api)
            self.chat_window.show()
        except Exception as e:
            self.status_label.setText(f"Login failed: {e}")

class ChatWindow(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.setWindowTitle("Chats")
        self.resize(600, 400)
        self.init_ui()
        self.load_chats()
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.refresh_messages)
        self.poll_timer.start(5000)  # poll every 5 seconds
        self.current_chat_id = None

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.chat_list = QListWidget()
        self.chat_list.currentTextChanged.connect(self.chat_selected)
        main_layout.addWidget(self.chat_list)
        right_layout = QVBoxLayout()
        self.messages_view = QTextEdit()
        self.messages_view.setReadOnly(True)
        self.message_input = QLineEdit()
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        right_layout.addWidget(self.messages_view)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)
        right_layout.addLayout(input_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def load_chats(self):
        chats = self.api.get_chats()
        for c in chats:
            self.chat_list.addItem(f"{c['id']} - {c['user_name']}")

    def chat_selected(self, text):
        if not text:
            return
        chat_id = int(text.split(" - ")[0])
        self.current_chat_id = chat_id
        self.refresh_messages()

    def refresh_messages(self):
        if self.current_chat_id:
            msgs = self.api.get_messages(self.current_chat_id)
            self.messages_view.clear()
            for m in msgs:
                direction = "<" if m['type'] == "incoming" else ">"
                self.messages_view.append(f"{m['date']} {direction} {m['message_text']}")

    def send_message(self):
        txt = self.message_input.text()
        if txt and self.current_chat_id:
            self.api.send_message(self.current_chat_id, txt)
            self.message_input.clear()
            self.refresh_messages()

if __name__ == "__main__":
    api = ApiClient(BASE_URL)
    app = QApplication(sys.argv)
    login = LoginWindow(api)
    login.show()
    sys.exit(app.exec())
