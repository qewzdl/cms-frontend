# api.py
import requests

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None

    def login(self, login, password):
        url = f"{self.base_url}/api/v1/authorization"
        resp = requests.post(url, json={'login': login, 'password': password})
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        return data

    def refresh_access(self):
        url = f"{self.base_url}/api/v1/authorization/refresh"
        headers = {'Authorization': f"Bearer {self.refresh_token}"}
        resp = requests.post(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data['access_token']
        return data

    def get_headers(self):
        return {'Authorization': f"Bearer {self.access_token}"}

    def get_chats(self):
        url = f"{self.base_url}/api/v1/chats"
        resp = requests.get(url, headers=self.get_headers())
        if resp.status_code == 401:
            self.refresh_access()
            resp = requests.get(url, headers=self.get_headers())
        resp.raise_for_status()
        return resp.json()

    def get_messages(self, chat_id):
        url = f"{self.base_url}/api/v1/chats/messages/{chat_id}"
        resp = requests.get(url, headers=self.get_headers())
        if resp.status_code == 401:
            self.refresh_access()
            resp = requests.get(url, headers=self.get_headers())
        resp.raise_for_status()
        return resp.json()

    def send_message(self, chat_id, text):
        url = f"{self.base_url}/api/v1/chats/messages"
        payload = {'user_id': chat_id, 'message_text': text}
        resp = requests.post(url, json=payload, headers=self.get_headers())
        if resp.status_code == 401:
            self.refresh_access()
            resp = requests.post(url, json=payload, headers=self.get_headers())
        resp.raise_for_status()
        return resp.json()
