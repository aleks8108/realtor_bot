import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID

def init_sheets():
    try:
        print(f"Попытка загрузки credentials из: {GOOGLE_SHEETS_CREDENTIALS}")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_ID).sheet1
    except FileNotFoundError:
        print(f"Ошибка: Файл {GOOGLE_SHEETS_CREDENTIALS} не найден")
        raise
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Ошибка: Таблица с ID {SPREADSHEET_ID} не найдена")
        raise
    except Exception as e:
        print(f"Ошибка при подключении к Google Sheets: {e}")
        raise

def save_request(data: dict):
    try:
        sheet = init_sheets()
        sheet.append_row([
            data.get("name", ""),
            data.get("phone", ""),
            data.get("property_type", ""),
            data.get("deal_type", ""),
            data.get("district", ""),
            data.get("budget", ""),
            data.get("comments", "")
        ])
    except Exception as e:
        print(f"Ошибка при сохранении заявки: {e}")
        raise

def get_listings():
    try:
        sheet = init_sheets()
        return sheet.get_all_records()
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        raise