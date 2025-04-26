from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QTextEdit, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import QTimer, Qt

class MainWindow(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.current_chat = None
        self.setWindowTitle("CMS Client")
        self._setup_ui()
        self._load_chats()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(5000)

    def _setup_ui(self):
        h = QHBoxLayout(self)
        self.chat_list = QListWidget()
        self.chat_list.currentItemChanged.connect(self._on_select)
        h.addWidget(self.chat_list, 1)

        v = QVBoxLayout()
        self.messages_view = QTextEdit(readOnly=True)
        v.addWidget(self.messages_view)
        self.message_input = QLineEdit()
        v.addWidget(self.message_input)
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send)
        v.addWidget(send_btn)
        h.addLayout(v, 3)

    def _load_chats(self):
        try:
            chats = self.api.get_chats()
            self.chat_list.clear()
            for c in chats:
                item = QListWidgetItem(f"{c['user_name']} ({c['telegram_account_phone']})")
                item.setData(Qt.UserRole, (c['id'], c['telegram_account_id']))
                self.chat_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_select(self, current, _):
        if current:
            self.current_chat = current.data(Qt.UserRole)
            self._load_messages()

    def _load_messages(self):
        if not self.current_chat:
            return
        chat_id, _ = self.current_chat
        try:
            msgs = self.api.get_messages(chat_id)
            self.messages_view.clear()
            for m in msgs:
                sender = 'You' if m['type']=='outgoing' else m['user_id']
                self.messages_view.append(f"{m['date']} - {sender}: {m['message_text']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _send(self):
        text = self.message_input.text().strip()
        if not text or not self.current_chat:
            return
        user_id, tg_id = self.current_chat
        try:
            self.api.send_message(user_id, text, tg_id)
            self.message_input.clear()
            self._load_messages()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _poll(self):
        self._load_messages()
