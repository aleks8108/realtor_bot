import gspread
from google.oauth2.service_account import Credentials

try:
    credentials = Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key('1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w')
    print("Доступ к таблице получен успешно!")
    print(f"Название таблицы: {spreadsheet.title}")
except Exception as e:
    print(f"Ошибка: {e}")