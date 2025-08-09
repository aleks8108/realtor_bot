"""
Пакет обработчиков сообщений для риэлторского бота.

Этот пакет содержит все обработчики событий, организованные по функциональным областям:
- admin: административные команды и функции
- request: обработка заявок на просмотр недвижимости  
- search: поиск и просмотр объектов недвижимости
- start: базовые команды и приветствие

Каждый модуль содержит роутер, который регистрируется в главном диспетчере.
"""

# Импортируем все роутеры для удобства использования в главном файле
from .admin import router as admin_router
from .request import router as request_router  
from .search import router as search_router
from .start import router as start_router

__all__ = [
    'admin_router',
    'request_router', 
    'search_router',
    'start_router'
]