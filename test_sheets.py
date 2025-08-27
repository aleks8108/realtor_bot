import requests
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request  # Импортируем правильный Request

# Путь к файлу учетных данных
CREDS_PATH = 'credentials.json'

# Загружаем учетные данные
credentials = Credentials.from_service_account_file(
    CREDS_PATH,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

# Обновляем токен доступа с использованием правильного объекта Request
request = Request()  # Создаем экземпляр Request из google.auth.transport.requests
credentials.refresh(request)

# Токен доступа
access_token = credentials.token

# Заголовки с токеном
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

# Тестовый запрос
url = 'https://sheets.googleapis.com/v4/spreadsheets/1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w'
response = requests.get(url, headers=headers, timeout=30)

print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")