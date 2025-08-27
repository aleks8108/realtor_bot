"""
Этот пакет содержит все обработчики событий, организованные по функциональным областям:
- admin: административные команды и функции
- request: обработка заявок на просмотр недвижимости  
- start: базовые команды и приветствие

Каждый модуль содержит роутер, который регистрируется в главном диспетчере.
"""
from .admin import router as admin_router
from .request import router as request_router
from .start import router as start_router
from .calculators import router as calculators_router  # Проверка импорта

__all__ = [
    'admin_router',
    'request_router',
    'start_router',
    'calculators_router'
]