import os, sys
# ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Window Settings
MAIN_WINDOW_MIN_WIDTH = 900
MAIN_WINDOW_MIN_HEIGHT = 600
MAIN_WINDOW_RESIZABLE = True

# Message Bubble Width Constraints
MESSAGE_BUBBLE_MIN_WIDTH = 150
MESSAGE_BUBBLE_MAX_WIDTH = 400

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QScrollArea, QLabel, QLineEdit, QPushButton, QMessageBox, QApplication
)
from PySide6.QtCore import QTimer, Qt
import style
from api.client import ApiClient
from collections import OrderedDict
from datetime import datetime

class MainWindow(QWidget):
    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client or ApiClient(parent=self)
        # apply window hints
        self.setMinimumSize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        if not MAIN_WINDOW_RESIZABLE:
            self.setFixedSize(self.minimumSize())
        self.setWindowTitle("CMS Client")
        self._setup_ui()
        self._load_chats()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(5000)

    def _setup_ui(self):
        # Overall vertical layout: topbar + content
        main_vlayout = QVBoxLayout(self)
        # Top bar
        self.top_bar = QWidget()
        self.top_bar.setObjectName('topBar')
        top_layout = QHBoxLayout(self.top_bar)
        title_label = QLabel('CMS Client')
        title_label.setObjectName('topBarTitle')
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        main_vlayout.addWidget(self.top_bar)

        # Content layout: chat list + messages
        content_layout = QHBoxLayout()

        # Chat list on the left
        self.chat_list = QListWidget()
        self.chat_list.setObjectName('chatList')  # for styling rounded corners
        self.chat_list.currentItemChanged.connect(self._on_select)
        content_layout.addWidget(self.chat_list, 1)

        # Right pane: messages area and input/send
        right_layout = QVBoxLayout()
        # Scrollable messages area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        container = QWidget()
        self.messages_layout = QVBoxLayout(container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(container)
        right_layout.addWidget(self.scroll_area)

        # Bottom row: input and send button
        bottom = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setObjectName('messageInput')
        bottom.addWidget(self.message_input)
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName('sendButton')
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._send)
        bottom.addWidget(self.send_btn)
        right_layout.addLayout(bottom)

        content_layout.addLayout(right_layout, 3)
        main_vlayout.addLayout(content_layout)

    def _clear_messages(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def _load_chats(self):
        try:
            chats = self.api.get_chats()
            self.chat_list.clear()
            for c in chats:
                # display only username in chat list
                item = QListWidgetItem(c['user_name'])
                item.setData(Qt.UserRole, (c['id'], c['telegram_account_id']))
                self.chat_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_select(self, current, _):
        if current:
            self.current_chat = current.data(Qt.UserRole)
            self._load_messages()

    def _load_messages(self):
        if not getattr(self, 'current_chat', None):
            return
        chat_id, _ = self.current_chat
        try:
            msgs = self.api.get_messages(chat_id)
            groups = OrderedDict()
            for m in msgs:
                dt = datetime.fromisoformat(m['date'])
                date_key = dt.date()
                groups.setdefault(date_key, []).append((dt, m))
            self._clear_messages()
            for date_key, items in groups.items():
                date_str = date_key.strftime('%d %B %Y')
                date_label = QLabel(date_str)
                date_label.setObjectName('dateLabel')
                self.messages_layout.addWidget(date_label, alignment=Qt.AlignHCenter)
                for dt, m in items:
                    bubble = QWidget()
                    bubble.setObjectName('messageBubble')
                    bubble.setProperty('messageType', m['type'])
                    bubble.setMinimumWidth(MESSAGE_BUBBLE_MIN_WIDTH)
                    bubble.setMaximumWidth(MESSAGE_BUBBLE_MAX_WIDTH)
                    bubble_layout = QVBoxLayout(bubble)
                    bubble_layout.setContentsMargins(8, 4, 8, 4)
                    msg_label = QLabel(m['message_text'])
                    msg_label.setWordWrap(True)
                    msg_label.setObjectName('messageLabel')
                    time_label = QLabel(dt.strftime('%H:%M'))
                    time_label.setObjectName('timeLabel')
                    bubble_layout.addWidget(msg_label)
                    bubble_layout.addWidget(time_label, alignment=Qt.AlignRight)
                    alignment = Qt.AlignRight if m['type']=='outgoing' else Qt.AlignLeft
                    self.messages_layout.addWidget(bubble, alignment=alignment)
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _send(self):
        text = self.message_input.text().strip()
        if not text or not getattr(self, 'current_chat', None):
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(style.load_styles(theme='light'))
    class MockApiClient(ApiClient):
        def __init__(self):
            super().__init__()
            self.access_token = 'mock'
            self.refresh_token = 'mock'
        def get_chats(self):
            return [{'id': 1, 'user_name': 'Test', 'telegram_account_id': 123, 'telegram_account_phone': '+700000'}]
        def get_messages(self, chat_id):
            return [
                {'id':'1','user_id':chat_id,'message_text':'Hello!','date':'2025-04-26T12:00:00','type':'incoming','telegram_account_id':123},
                {'id':'2','user_id':chat_id,'message_text':'Reply','date':'2025-04-26T12:01:00','type':'outgoing','telegram_account_id':123},
            ]
        def send_message(self, user_id, text, telegram_account_id):
            print('Mock send', user_id, text)
            return {}
    api = MockApiClient()
    window = MainWindow(api)
    window.show()
    sys.exit(app.exec())