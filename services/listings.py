import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CREDENTIALS_FILE, SPREADSHEET_ID

def cached_get_listings():
    # Настройка аутентификации
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    
    # Получение данных из Google Sheets
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet('listings')
    data = sheet.get_all_records()
    
    # Преобразование данных (упрощённая версия)
    listings = []
    for row in data:
        listing = {
            'id': row.get('id', 0),
            'property_type': row.get('property_type', ''),
            'deal_type': row.get('deal_type', ''),
            'district': row.get('district', ''),
            'price': float(row.get('price', 0)) if row.get('price') else 0,
            'rooms': row.get('rooms', ''),
            'description': row.get('description', ''),
            'photo_url': row.get('photo_url', '')
        }
        listings.append(listing)
    return listings