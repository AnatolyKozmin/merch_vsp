import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Путь к вашему credentials.json
CREDENTIALS_FILE = 'credentials.json'
# Название вашей Google таблицы
SPREADSHEET_NAME = 'MERCH'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open(SPREADSHEET_NAME)
worksheet = sh.sheet1

def add_order(user_id, username, product, size, color, quantity):
    worksheet.append_row([
        user_id,
        username,
        product,
        size,
        color,
        quantity,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ])

def remove_order(user_id, product, size, color):
    cell_list = worksheet.findall(str(user_id))
    rows_to_delete = []
    for cell in cell_list:
        row = worksheet.row_values(cell.row)
        if len(row) >= 5 and row[2] == product and row[3] == size and row[4] == color:
            rows_to_delete.append(cell.row)
    # Удаляем строки с конца, чтобы индексы не смещались
    for row_num in sorted(rows_to_delete, reverse=True):
        worksheet.delete_rows(row_num)
