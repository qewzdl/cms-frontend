import requests
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox

API_BASE = "https://savychk1.fvds.ru/api/v1"
ORGANIZATION = "MyCompany"
APPLICATION  = "CMSClient"

class ApiClient:
    def __init__(self, parent=None):
        self.parent = parent
        self.settings = QSettings(ORGANIZATION, APPLICATION)
        self.access_token = None
        self.refresh_token = None
        self.load_tokens()

    def _headers(self, use_refresh=False):
        token = self.refresh_token if use_refresh else self.access_token
        return {"Authorization": f"Bearer {token}"} if token else {}

    def save_tokens(self):
        self.settings.setValue("access_token", self.access_token)
        self.settings.setValue("refresh_token", self.refresh_token)

    def load_tokens(self):
        at = self.settings.value("access_token", "")
        rt = self.settings.value("refresh_token", "")
        if at and rt:
            self.access_token = at
            self.refresh_token = rt

    def clear_tokens(self):
        self.settings.remove("access_token")
        self.settings.remove("refresh_token")
        self.access_token = None
        self.refresh_token = None

    def login(self, login, password):
        resp = requests.post(f"{API_BASE}/authorization",
                             json={"login": login, "password": password})
        resp.raise_for_status()
        data = resp.json()
        self.access_token  = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.save_tokens()
        return data

    def refresh_access(self):
        if not self.refresh_token:
            return False
        resp = requests.post(f"{API_BASE}/authorization/refresh",
                             headers=self._headers(use_refresh=True))
        if resp.status_code == 401:
            self.clear_tokens()
            return False
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.save_tokens()
        return True

    def get_chats(self):
        resp = requests.get(f"{API_BASE}/chats", headers=self._headers())
        if resp.status_code == 401 and self.refresh_access():
            resp = requests.get(f"{API_BASE}/chats", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def get_messages(self, chat_id):
        url = f"{API_BASE}/chats/messages/{chat_id}"
        resp = requests.get(url, headers=self._headers())
        if resp.status_code == 401 and self.refresh_access():
            resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def send_message(self, user_id, text, telegram_account_id):
        payload = {"user_id": user_id, "message_text": text, "telegram_account_id": str(telegram_account_id)}
        resp = requests.post(f"{API_BASE}/chats/messages/send", json=payload, headers=self._headers())
        if resp.status_code == 401 and self.refresh_access():
            resp = requests.post(f"{API_BASE}/chats/messages/send", json=payload, headers=self._headers())
        resp.raise_for_status()
        return resp.json()