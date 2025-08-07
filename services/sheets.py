import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID
import logging

logging.basicConfig(level=logging.DEBUG)

def init_sheets(sheet_name: str):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        return spreadsheet.worksheet(sheet_name)
    except Exception as e:
        logging.error(f"Ошибка при инициализации Google Sheets ({sheet_name}): {e}")
        raise

def save_request(data: dict):
    try:
        sheet = init_sheets("requests")
        sheet.append_row([
            data.get("name", ""),
            data.get("phone", ""),
            data.get("property_type", ""),
            data.get("deal_type", ""),
            data.get("district", ""),
            data.get("budget", ""),
            data.get("comments", "")
        ])
        logging.info("Заявка успешно сохранена в Google Sheets")
    except Exception as e:
        logging.error(f"Ошибка при сохранении заявки: {e}")
        raise

def save_appointment(data: dict, user_name: str, user_id: int):
    try:
        sheet = init_sheets("appointments")
        sheet.append_row([
            data.get("date", ""),
            data.get("time", ""),
            data.get("address", ""),
            user_name,
            user_id
        ])
        logging.info("Встреча успешно сохранена в Google Sheets")
    except Exception as e:
        logging.error(f"Ошибка при сохранении встречи: {e}")
        raise

def get_listings():
    try:
        sheet = init_sheets("listings")
        return sheet.get_all_records()
    except Exception as e:
        logging.error(f"Ошибка при получении объектов недвижимости: {e}")
        raise