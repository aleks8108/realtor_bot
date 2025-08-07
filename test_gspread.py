import gspread
from google.oauth2.service_account import Credentials

scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file('credentials.json', scopes=scopes)
gc = gspread.Client(auth=credentials)
spreadsheet = gc.open_by_key("1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w")
worksheet = spreadsheet.worksheet("listings")
print(worksheet.get_all_records())