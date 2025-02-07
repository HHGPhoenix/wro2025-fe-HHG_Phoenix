import requests
import base64
import time
import warnings
from urllib3.exceptions import InsecureRequestWarning
import socket
from urllib.parse import urlparse

warnings.simplefilter('ignore', InsecureRequestWarning)

class NotificationClient:
    def __init__(self, base_url='https://192.168.178.28'):
        self.base_url = base_url
        username = "phil"
        password = "phil"
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.authHeader = "Basic " + encoded_credentials

    def server_online(self):
        try:
            parsed = urlparse(self.base_url)
            host = parsed.hostname
            port = parsed.port if parsed.port else (443 if parsed.scheme == "https" else 80)
            conn = socket.create_connection((host, port), timeout=1)
            conn.close()
            return True
        except Exception:
            return False

    def send_message(self, topic, message):
        url = f"{self.base_url}/{topic}"
        try:
            response = requests.post(url, data=message, verify=False)
        except Exception:
            # silently ignore if offline or error
            return None
        return response

    def send_battery(self, battery_level):
        if not self.server_online():
            return None
        url = f"{self.base_url}/battery"
        battery = f"Battery Level: {battery_level}V"
        headers = {
            "Title": "Battery Alert",
            "Priority": "high",
            "Authorization": self.authHeader
        }
        try:
            response = requests.post(url, data=battery, headers=headers, verify=False)
        except Exception:
            return None
        return response

if __name__ == '__main__':
    ntfy = NotificationClient()
    for i in range(10):
        response = ntfy.send_battery(i*10)
        print(response.status_code)
        print(response.text)
        time.sleep(3)
    response = ntfy.send_battery(100)
    print(response.status_code)
    print(response.text)