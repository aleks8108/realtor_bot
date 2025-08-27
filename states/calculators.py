"""
Состояния FSM для калькуляторов в риэлторском боте.
"""

from aiogram.fsm.state import State, StatesGroup

class MortgageStates(StatesGroup):
    amount = State()
    rate = State()
    term = State()
    extra_payment = State()

class ValuationStates(StatesGroup):
    type = State()
    district = State()
    area = State()

class InvestmentStates(StatesGroup):
    cost = State()
    rent = State()
    expenses = State()

class CalculatorStates(StatesGroup):
    choosing_calculator = State()