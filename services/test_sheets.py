import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID
import logging

logging.basicConfig(level=logging.DEBUG)

def test_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet("listings")
        print("Successfully connected to Google Sheets!")
        print(sheet.get_all_records())
    except Exception as e:
        logging.error(f"Ошибка при подключении к Google Sheets: {e}")
        raise

if __name__ == "__main__":
    test_sheets()