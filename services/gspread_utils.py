import gspread
from oauth2client.service_account import ServiceAccountCredentials

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