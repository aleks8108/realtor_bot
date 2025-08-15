# Файл: states/__init__.py
"""
Инициализация модуля состояний.
Экспортирует все группы состояний для удобного импорта в других модулях.
"""

from .request import RequestStates
from .search import SearchStates

__all__ = ['RequestStates', 'SearchStates']