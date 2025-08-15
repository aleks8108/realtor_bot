import requests
import certifi
import ssl

url = 'https://sheets.googleapis.com/v4/spreadsheets/1TLkCSd8lyuz3kNjxE6SvxwkG9WH1NERK_dML969R43w?includeGridData=false'
try:
    response = requests.get(url, verify=certifi.where())
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")