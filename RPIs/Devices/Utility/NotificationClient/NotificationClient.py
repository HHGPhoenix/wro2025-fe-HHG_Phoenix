import requests

class NotificationClient:
    def __init__(self, base_url='http://localhost:80'):
        self.base_url = base_url

    def send_message(self, topic, message):
        url = f"{self.base_url}/{topic}"
        response = requests.post(url, data=message)
        return response
    
    def send_battery(self, battery_level):
        url = f"{self.base_url}/battery"
        battery = f"🤬 Battery Level: {battery_level} %"
        headers={
        "Title": "Battery Alert",
        "Priority": "urgent",
        "Tags": "warning,skull"
        }
        response = requests.post(url, data=battery, headers=headers)
        return response
    
if __name__ == '__main__':
    ntfy = NotificationClient()
    # # response = ntfy.send_message('test', 'Hello, World!')
    # print(response.status_code)
    # print(response.text)
    
    response = ntfy.send_battery(10)