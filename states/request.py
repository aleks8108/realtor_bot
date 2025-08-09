# Файл: states/request.py
from aiogram.fsm.state import State, StatesGroup

class RequestStates(StatesGroup):
    name = State()
    phone = State()
    property_type = State()
    deal_type = State()
    district = State()
    budget = State()
    rooms = State()
    comments = State()
    listing = State()