"""
Состояния FSM для процесса поиска недвижимости.
Эти состояния управляют процессом поиска объектов без оформления заявки.
"""

from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    """
    Группа состояний для поиска недвижимости.
    Отличается от RequestStates тем, что не требует персональных данных
    и предназначена только для просмотра объектов.
    """
    
    # Критерии поиска
    selecting_property_type = State()    # Выбор типа недвижимости
    selecting_deal_type = State()        # Выбор типа сделки  
    selecting_district = State()         # Выбор района
    selecting_budget = State()           # Выбор бюджета
    selecting_rooms = State()            # Выбор количества комнат
    
    # Просмотр результатов
    viewing_results = State()            # Просмотр найденных объектов
    
    # Выражение интереса (переход к заявке)
    expressing_interest = State()        # Пользователь выразил интерес к объекту