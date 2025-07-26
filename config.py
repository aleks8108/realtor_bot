import os
from dotenv import load_dotenv
load_dotenv()
from decouple import config

BOT_TOKEN = config('BOT_TOKEN')
ADMIN_ID = int(config('ADMIN_ID'))
GOOGLE_SHEETS_CREDENTIALS = config('GOOGLE_SHEETS_CREDENTIALS')
SPREADSHEET_ID = config('SPREADSHEET_ID')
