"""
Модуль содержит пользовательские исключения для риэлторского бота.
Эти исключения помогают обрабатывать специфические ошибки более точно и информативно.
"""

# Базовые исключения
class ValidationError(Exception):
    """Базовое исключение для ошибок валидации данных."""
    pass

class ServiceError(Exception):
    """Базовое исключение для ошибок внешних сервисов."""
    pass

class BotException(Exception):
    """
    Базовое исключение для всех ошибок бота.
    Все остальные пользовательские исключения должны наследоваться от него.
    """
    def __init__(self, message: str, user_id: int = None):
        super().__init__(message)
        self.message = message
        self.user_id = user_id

class GoogleSheetsError(ServiceError):
    """
    Исключение для ошибок работы с Google Sheets.
    Возникает при проблемах с аутентификацией, сетевых ошибках или проблемах со структурой таблицы.
    """
    def __init__(self, message: str, operation: str = None, sheet_name: str = None):
        super().__init__(message)
        self.operation = operation  # Например: "read", "write", "authenticate"
        self.sheet_name = sheet_name

class ListingNotFoundError(BotException):
    """
    Исключение для случаев, когда объект недвижимости не найден.
    """
    def __init__(self, listing_id: str = None):
        message = f"Объект недвижимости не найден"
        if listing_id:
            message += f" (ID: {listing_id})"
        super().__init__(message)
        self.listing_id = listing_id

class StateError(BotException):
    """
    Исключение для ошибок управления состояниями FSM.
    Возникает при попытке выполнить действие в неподходящем состоянии.
    """
    def __init__(self, message: str, current_state: str = None, expected_state: str = None):
        super().__init__(message)
        self.current_state = current_state
        self.expected_state = expected_state

class PhotoProcessingError(ServiceError):
    """
    Исключение для ошибок обработки фотографий объектов недвижимости.
    Возникает при проблемах с загрузкой или обработкой изображений.
    """
    def __init__(self, message: str, photo_url: str = None):
        super().__init__(message)
        self.photo_url = photo_url