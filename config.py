import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = [int(os.getenv("ADMIN_ID"))] if os.getenv("ADMIN_ID") else []
GOOGLE_SHEETS_CREDENTIALS = r"C:\Users\aleks\source\repos\aleks8108\realtor_bot\credentials.json"  # Используем r для сырой строки
SPREADSHEET_ID = "1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w"  # Убедитесь, что ID верный