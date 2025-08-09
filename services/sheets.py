import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Настройка доступа к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

def get_listings():
    sheet = client.open_by_key("1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w").worksheet("listings")
    data = sheet.get_all_records()
    for item in data:
        if isinstance(item.get("photo_url"), str):
            item["photo_url"] = item["photo_url"].split(",")
    return data

def save_request(data):
    sheet = client.open_by_key("1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w").worksheet("requests")  # Новая вкладка "requests"
    headers = ["name", "phone", "property_type", "deal_type", "district", "budget", "rooms", "comments", "user_id", "username", "timestamp"]
    row = [
        data.get("name", ""),
        data.get("phone", ""),
        data.get("property_type", ""),
        data.get("deal_type", ""),
        data.get("district", ""),
        data.get("budget", ""),
        data.get("rooms", ""),
        data.get("comments", ""),
        data.get("user_id", ""),
        data.get("username", ""),
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    sheet.append_row(row)
    logging.info(f"Заявка сохранена: {row}")