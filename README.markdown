# Telegram-бот для риэлтора

Бот для автоматизации взаимодействия риэлтора с клиентами: поиск недвижимости, сбор заявок, назначение встреч и чат.

## Установка

1. Установите Python 3.8+.
2. Клонируйте репозиторий:
   ```bash
   git clone <repository_url>
   cd realtor_bot
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Настройте файл `.env`:
   ```plaintext
   BOT_TOKEN=<your_bot_token>
   ADMIN_ID=<your_telegram_id>
   GOOGLE_SHEETS_CREDENTIALS=<path_to_credentials.json>
   SPREADSHEET_ID=<your_spreadsheet_id>
   ```
5. Запустите бота:
   ```bash
   python bot.py
   ```
  
## создание виртуальной среды 
  C:\Users\aleks\AppData\Local\Programs\Python\Python312\python.exe -m venv venv

## активация виртуальной среды
.\venv\Scripts\activate

## Если используете PowerShell и возникает ошибка, связанная с политиками выполнения скриптов, сначала выполните: 
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

## Удаление кэш
     Remove-Item -Path "__pycache__" -Recurse -Force   

## Требования

- Telegram Bot API (токен от @BotFather)
- Google Sheets API (настройте credentials в Google Cloud Console)
- VPS для хостинга (например, Heroku, DigitalOcean)

## Тестирование

1. Запустите бота и проверьте команду `/start`.
2. Проверьте отправку заявок и уведомлений.
3. Убедитесь, что данные сохраняются в Google Sheets.

## Документация

- **handlers/**: Обработчики команд и кнопок.
- **keyboards/**: Reply и Inline клавиатуры.
- **services/**: Интеграции с Google Sheets и уведомления.