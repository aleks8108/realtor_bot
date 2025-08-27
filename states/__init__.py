# Файл: states/__init__.py
"""
Инициализация всех состояний FSM для риэлторского бота.
"""

from .request import RequestStates
from .calculators import MortgageStates, ValuationStates, InvestmentStates, CalculatorStates  # Только актуальные состояния

__all__ = [
    'RequestStates',
    'MortgageStates',
    'ValuationStates',
    'InvestmentStates',
    'CalculatorStates'
]