import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

MAIN_WINDOW_MIN_WIDTH = 900
MAIN_WINDOW_MIN_HEIGHT = 600
MAIN_WINDOW_RESIZABLE = True

MESSAGE_BUBBLE_MIN_WIDTH = 100
MESSAGE_BUBBLE_MAX_WIDTH = 500

MESSAGE_LOADING_INTERVAL = 5

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem,
    QScrollArea, QLabel,
    QPushButton, QMessageBox, 
    QApplication, QSizePolicy, 
    QTextEdit
)
from PySide6.QtCore import QTimer, Qt
import styles.style as style
from api.client import ApiClient
from collections import OrderedDict
from datetime import datetime

class SelectableLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.setWordWrap(True)

class MainWindow(QWidget):
    def __init__(self, api_client=None, username=""):
        super().__init__()
        self.api = api_client or ApiClient(parent=self)
        self.username = username

        self.bubble_min_width = MESSAGE_BUBBLE_MIN_WIDTH
        self.bubble_max_width = MESSAGE_BUBBLE_MAX_WIDTH

        self.setMinimumSize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        if not MAIN_WINDOW_RESIZABLE:
            self.setFixedSize(self.minimumSize())
        self.setWindowTitle("CMS Client")
        self._setup_ui()
        self._load_chats()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(MESSAGE_LOADING_INTERVAL * 1000)

    def _setup_ui(self):
        main_v = QVBoxLayout(self)
        self.top_bar = QWidget()
        self.top_bar.setObjectName('topBar')
        top_h = QHBoxLayout(self.top_bar)
        lbl_title = QLabel('CMS Client')
        lbl_title.setObjectName('topBarTitle')
        lbl_user = QLabel(self.username)
        lbl_user.setObjectName('topBarUser')
        top_h.addWidget(lbl_title)
        top_h.addStretch()
        top_h.addWidget(lbl_user)
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutButton")
        logout_btn.setFixedWidth(70)
        logout_btn.clicked.connect(self._logout)
        top_h.addWidget(logout_btn)
        main_v.addWidget(self.top_bar)

        content_h = QHBoxLayout()
        self.chat_list = QListWidget()
        self.chat_list.setObjectName('chatList')
        self.chat_list.currentItemChanged.connect(self._on_select)
        content_h.addWidget(self.chat_list, 1)

        right_v = QVBoxLayout()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        self.messages_layout = QVBoxLayout(container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(container)
        container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        right_v.addWidget(self.scroll)

        bottom_h = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setObjectName('messageInput')
        bottom_h.addWidget(self.message_input)

        self.send_btn = QPushButton('Send')
        self.send_btn.setObjectName('sendBtn')
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._send)
        button_height = self.send_btn.sizeHint().height() + 4
        self.message_input.setFixedHeight(button_height)
        self.message_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_input.textChanged.connect(
            lambda: self._adjust_input_height(button_height)
        )

        bottom_h.addWidget(self.send_btn)
        right_v.addLayout(bottom_h)

        content_h.addLayout(right_v, 3)
        main_v.addLayout(content_h)

    def _adjust_input_height(self, base_height, max_lines=5):
        doc = self.message_input.document()
        fm = self.message_input.fontMetrics()
        line_height = fm.lineSpacing()
        margin = 8
        max_height = base_height + line_height * (max_lines - 1) + margin
        doc_height = doc.size().height()
        new_height = max(base_height, int(doc_height) + margin)
        new_height = min(new_height, max_height)
        self.message_input.setFixedHeight(new_height)

    def _on_width_change(self):
        self.bubble_min_width = self.min_width_spin.value()
        self.bubble_max_width = self.max_width_spin.value()
        if self.bubble_min_width > self.bubble_max_width:
            self.bubble_max_width = self.bubble_min_width
            self.max_width_spin.setValue(self.bubble_max_width)
        self._load_messages()

    def _clear_messages(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            l = item.layout()
            if l:
                while l.count():
                    child = l.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                l.deleteLater()

    def _load_chats(self):
        try:
            chats = self.api.get_chats()
            self.chat_list.clear()
            for c in chats:
                item = QListWidgetItem(c['user_name'])
                item.setData(Qt.UserRole, (c['id'], c['telegram_account_id']))
                self.chat_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def _on_select(self, current, _):
        if current:
            self.current_chat = current.data(Qt.UserRole)
            self._load_messages(scroll_to_bottom=True)

    def _load_messages(self, scroll_to_bottom=False):
        if not getattr(self, 'current_chat', None):
            return
        chat_id, _ = self.current_chat

        try:
            msgs = self.api.get_messages(chat_id)
            groups = OrderedDict()
            last_bubble = None
            bubbles = []

            self._clear_messages()
            for m in msgs:
                dt = datetime.fromisoformat(m['date'])
                key = dt.date()
                groups.setdefault(key, []).append((dt, m))

            for date_key in sorted(groups.keys()):
                date_lbl = QLabel(date_key.strftime('%d %B %Y'))
                date_lbl.setObjectName('dateLabel')
                self.messages_layout.addWidget(date_lbl, alignment=Qt.AlignHCenter)
                for dt, m in sorted(groups[date_key], key=lambda x: x[0]):
                    bubble = QWidget()
                    bubble.setObjectName('messageBubble')
                    bubble.setProperty('messageType', m['type'])
                    bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
                    bl = QVBoxLayout(bubble)
                    bl.setContentsMargins(8, 4, 8, 4)

                    msg_widget = SelectableLabel(m['message_text'])
                    msg_widget.setObjectName('messageLabel')
                    msg_widget.setWordWrap(True)
                    msg_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)

                    msg_widget.setMaximumWidth(self.bubble_max_width - 16)
                    msg_widget.adjustSize()
                    text_width = msg_widget.fontMetrics().boundingRect(
                        0, 0, self.bubble_max_width-16, 1000, Qt.TextWordWrap, m['message_text']
                    ).width()
                    bubble_width = max(self.bubble_min_width, min(text_width + 24, self.bubble_max_width))
                    bubble.setMinimumWidth(bubble_width)
                    bubble.setMaximumWidth(bubble_width)

                    bl.addWidget(msg_widget)
                    time_lbl = QLabel(dt.strftime('%H:%M'))
                    time_lbl.setObjectName('timeLabel')
                    bl.addWidget(time_lbl, alignment=Qt.AlignRight)

                    hlayout = QHBoxLayout()
                    if m['type'] == 'outgoing':
                        hlayout.addStretch()
                        hlayout.addWidget(bubble, 0, Qt.AlignRight)
                    else:
                        hlayout.addWidget(bubble, 0, Qt.AlignLeft)
                        hlayout.addStretch()
                    self.messages_layout.addLayout(hlayout)
                    last_bubble = bubble
                    bubbles.append(bubble)
            self.messages_layout.addStretch()

            if scroll_to_bottom and last_bubble is not None:
                def ensure_bottom():
                    self.scroll.ensureWidgetVisible(last_bubble)
                QTimer.singleShot(0, ensure_bottom)
                QTimer.singleShot(30, ensure_bottom)
                QTimer.singleShot(100, ensure_bottom)

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def _send(self):
        text = self.message_input.toPlainText().strip()
        if not text or not getattr(self, 'current_chat', None):
            return
        user_id, tg_id = self.current_chat
        try:
            self.api.send_message(user_id, text, tg_id)
            self.message_input.clear()
            self._load_messages()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def _poll(self):
        self._load_messages()

    def _logout(self):
        from ui.login_window import LoginWindow
        self.api.clear_tokens()
        self.login_window = LoginWindow(self.api)
        self.login_window.show()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(style.load_styles(theme='light'))
    class MockApiClient(ApiClient):
        def get_chats(self): return [{'id':1,'user_name':'TestUser','telegram_account_id':123,'telegram_account_phone':'+700'}]
        def get_messages(self, chat_id): return [
            {'id':'1','user_id':chat_id,'message_text':'ОченьдлинныйтекстДляПроверкиПереноса','date':'2025-04-26T12:00:00','type':'incoming','telegram_account_id':123},
            {'id':'2','user_id':chat_id,'message_text':'Reply','date':'2025-04-26T12:01:00','type':'outgoing','telegram_account_id':123},
        ]
        def send_message(self, user_id, text, telegram_account_id): print('Mock send', user_id, text); return {}
    api = MockApiClient()
    window = MainWindow(api, 'Your Login')
    window.show()
    sys.exit(app.exec())