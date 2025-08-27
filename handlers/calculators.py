"""
Обработчик калькуляторов в риэлторском боте.
Предоставляет интерфейс для расчёта ипотеки, оценки стоимости и доходности инвестиций.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
import logging
from math import pow

from utils.keyboards import get_main_menu, get_district_keyboard
from states.calculators import MortgageStates, ValuationStates, InvestmentStates, CalculatorStates
from services.error_handler import error_handler
from services.sheets import google_sheets_service
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("calculators"))
@error_handler(operation_name="Запуск калькуляторов (/calculators)")
async def cmd_calculators(message: Message, state: FSMContext):
    logger.debug("Обработчик /calculators активирован для пользователя %s", message.from_user.id)
    await state.set_state(CalculatorStates.choosing_calculator)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Калькулятор ипотеки", callback_data="calc_mortgage")],
        [InlineKeyboardButton(text="🏠 Оценка стоимости", callback_data="calc_valuation")],
        [InlineKeyboardButton(text="💰 Доходность инвестиций", callback_data="calc_investment")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="return_to_menu")]
    ])
    await message.answer("Выберите калькулятор:", reply_markup=keyboard)

# Калькулятор ипотеки
@router.callback_query(F.data == "calc_mortgage", StateFilter(CalculatorStates.choosing_calculator))
@error_handler(operation_name="Запуск калькулятора ипотеки")
async def start_mortgage_calc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MortgageStates.amount)
    await callback.message.edit_text("Введите сумму кредита (в рублях):")
    await callback.answer()

@router.message(StateFilter(MortgageStates.amount))
@error_handler(operation_name="Ввод суммы кредита")
async def process_mortgage_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))  # Заменяем запятую на точку
        await state.update_data(amount=amount)
        await state.set_state(MortgageStates.rate)
        await message.answer("Введите процентную ставку (в % годовых):")
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@router.message(StateFilter(MortgageStates.rate))
@error_handler(operation_name="Ввод ставки ипотеки")
async def process_mortgage_rate(message: Message, state: FSMContext):
    try:
        rate_input = message.text.strip().replace(",", ".")  # Заменяем запятую на точку
        logger.debug(f"Введена ставка: '{rate_input}'")
        rate = float(rate_input) / 100 / 12  # Месячная ставка
        logger.debug(f"Преобразованная месячная ставка: {rate}")
        await state.update_data(rate=rate)
        await state.set_state(MortgageStates.term)
        await message.answer("Введите срок кредита (в годах):")
    except ValueError:
        logger.error(f"Ошибка преобразования ставки '{rate_input}' в float")
        await message.answer("Пожалуйста, введите число.")

@router.message(StateFilter(MortgageStates.term))
@error_handler(operation_name="Ввод срока ипотеки")
async def process_mortgage_term(message: Message, state: FSMContext):
    try:
        term = int(message.text) * 12  # В месяцах
        await state.update_data(term=term)
        await state.set_state(MortgageStates.extra_payment)
        await message.answer("Введите дополнительный платёж (0, если без доплаты):")
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@router.message(StateFilter(MortgageStates.extra_payment))
@error_handler(operation_name="Ввод дополнительного платежа")
async def process_mortgage_extra(message: Message, state: FSMContext):
    try:
        logger.debug(f"Получено значение доплаты: '{message.text}' от пользователя {message.from_user.id}")
        extra = float(message.text.strip().replace(",", "."))  # Заменяем запятую на точку
        data = await state.get_data()
        logger.debug(f"Данные состояния: {data}")

        if 'amount' not in data or 'rate' not in data or 'term' not in data:
            await message.answer("Ошибка: данные для расчета отсутствуют. Начните заново.")
            await state.clear()
            return

        monthly_payment = (data['amount'] * data['rate'] * pow(1 + data['rate'], data['term'])) / (pow(1 + data['rate'], data['term']) - 1)
        remaining = data['amount']
        payment_schedule = []
        total_interest_paid = 0
        total_paid = 0
        months = 0

        while remaining > 0 and months < data['term'] * 2:
            interest = remaining * data['rate']
            principal = monthly_payment - interest
            total_payment = monthly_payment + extra
            remaining -= (principal + extra)
            remaining = max(remaining, 0)

            total_interest_paid += interest
            total_paid += total_payment
            payment_schedule.append([months + 1, f"{monthly_payment:.2f}", f"{extra:.2f}", f"{principal:.2f}", f"{interest:.2f}", f"{remaining:.2f}"])
            months += 1

            if remaining <= 0:
                break

        # Генерация PDF
        pdf_file = f"mortgage_calc_{message.from_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Регистрация шрифта с проверкой
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'fonts/DejaVuSans.ttf'))
            logger.debug("Шрифт DejaVuSans успешно зарегистрирован")
        except Exception as e:
            logger.error(f"Ошибка регистрации шрифта: {str(e)}")
            await message.answer("Ошибка: шрифт для PDF не найден. Убедитесь, что fonts/DejaVuSans.ttf доступен.")
            return

        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Применение шрифта ко всем стилям
        for style_name in ['Normal', 'Heading1', 'Heading2']:
            styles[style_name].fontName = 'DejaVuSans'

        elements = []

        # Заголовок
        elements.append(Paragraph(f"Расчет ипотеки для {message.from_user.username or message.from_user.id}", styles['Heading1']))
        elements.append(Spacer(1, 12))

        # Параметры
        params = [
            ["Сумма кредита", f"{data['amount']:.2f} руб."],
            ["Срок", f"{int(data['term'] / 12)} лет ({data['term']} месяцев)"],
            ["Ставка", f"{data['rate'] * 12 * 100:.2f}% годовых"],
            ["Ежемесячный платеж", f"{monthly_payment:.2f} руб."],
            ["Дополнительный платеж", f"{extra:.2f} руб."],
            ["Общая переплата", f"{total_interest_paid:.2f} руб."],
            ["Общая сумма выплат", f"{total_paid:.2f} руб."],
            ["Срок с доплатой", f"{months} месяцев"]
        ]
        elements.append(Table(params, colWidths=[200, 150], style=[
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT')  # Выравнивание текста
        ]))
        elements.append(Spacer(1, 12))

        # График платежей
        elements.append(Paragraph("График платежей", styles['Heading2']))
        schedule_table = [["Месяц", "Платеж", "Доп. платеж", "Основной долг", "Проценты", "Остаток"]]
        schedule_table.extend(payment_schedule)
        elements.append(Table(schedule_table, colWidths=[50, 80, 80, 80, 80, 80], style=[
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Выравнивание по центру
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Вертикальное выравнивание
        ]))

        doc.build(elements)

        # Отправка и удаление PDF
        await message.answer_document(FSInputFile(pdf_file), caption="Вот ваш расчет в PDF")
        os.remove(pdf_file)
        logger.info(f"PDF отправлен и удален для пользователя {message.from_user.id}")

        await state.clear()
        await message.answer("Расчёт завершён. Выберите действие:", reply_markup=get_main_menu())
    except ValueError as e:
        logger.error(f"Ошибка преобразования в float: {str(e)} для значения '{message.text}'")
        await message.answer("Пожалуйста, введите число.")
    except Exception as e:
        logger.error(f"Ошибка при расчете ипотеки: {str(e)}")
        await message.answer("Произошла ошибка при расчете. Попробуйте снова или свяжитесь с поддержкой.")

# Оставшиеся обработчики (оценка стоимости, доходность) остаются без изменений

@router.callback_query(F.data == "calc_valuation", StateFilter(CalculatorStates.choosing_calculator))
@error_handler(operation_name="Запуск оценки стоимости")
async def start_valuation_calc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ValuationStates.type)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Квартира", callback_data="val_type_apartment")],
        [InlineKeyboardButton(text="🏡 Дом", callback_data="val_type_house")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="return_to_menu")]
    ])
    await callback.message.edit_text("Выберите тип недвижимости:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("val_type_"), StateFilter(ValuationStates.type))
@error_handler(operation_name="Выбор типа недвижимости для оценки")
async def process_valuation_type(callback: CallbackQuery, state: FSMContext):
    property_type_raw = callback.data.replace("val_type_", "")
    property_type_mapping = {"apartment": "Квартира", "house": "Дом"}
    property_type = property_type_mapping.get(property_type_raw, property_type_raw)
    await state.update_data(type=property_type)
    await state.set_state(ValuationStates.district)
    await callback.message.edit_text("Выберите район:", reply_markup=get_district_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("val_district_"), StateFilter(ValuationStates.district))
@error_handler(operation_name="Выбор района для оценки")
async def process_valuation_district(callback: CallbackQuery, state: FSMContext):
    district = callback.data.replace("val_district_", "")
    await state.update_data(district=district)
    await state.set_state(ValuationStates.area)
    await callback.message.edit_text("Введите площадь недвижимости (в м²):")
    await callback.answer()

@router.message(StateFilter(ValuationStates.area))
@error_handler(operation_name="Ввод площади для оценки")
async def process_valuation_area(message: Message, state: FSMContext):
    try:
        area = float(message.text)
        data = await state.get_data()
        property_type = data['type']
        district = data['district']
        logger.debug(f"Расчет стоимости: district={district}, property_type={property_type}, area={area}")
        price_per_m2 = await google_sheets_service.get_price_per_m2(district, property_type)
        if price_per_m2 == 0:
            await message.answer("Цена для этого района и типа недвижимости не найдена.")
            await state.clear()
            return
        estimated_value = area * price_per_m2
        await message.answer(f"Оценочная стоимость: {estimated_value:.2f} руб.", reply_markup=get_main_menu())
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@router.callback_query(F.data == "calc_investment", StateFilter(CalculatorStates.choosing_calculator))
@error_handler(operation_name="Запуск калькулятора доходности")
async def start_investment_calc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(InvestmentStates.cost)
    await callback.message.edit_text("Введите стоимость недвижимости (в рублях):")
    await callback.answer()

@router.message(StateFilter(InvestmentStates.cost))
@error_handler(operation_name="Ввод стоимости инвестиции")
async def process_investment_cost(message: Message, state: FSMContext):
    try:
        cost = float(message.text)
        await state.update_data(cost=cost)
        await state.set_state(InvestmentStates.rent)
        await message.answer("Введите ежемесячный арендный доход (в рублях):")
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@router.message(StateFilter(InvestmentStates.rent))
@error_handler(operation_name="Ввод арендного дохода")
async def process_investment_rent(message: Message, state: FSMContext):
    try:
        rent = float(message.text)
        await state.update_data(rent=rent)
        await state.set_state(InvestmentStates.expenses)
        await message.answer("Введите ежемесячные расходы (в рублях):")
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@router.message(StateFilter(InvestmentStates.expenses))
@error_handler(operation_name="Ввод расходов инвестиции")
async def process_investment_expenses(message: Message, state: FSMContext):
    try:
        expenses = float(message.text)
        data = await state.get_data()
        annual_income = (data['rent'] - expenses) * 12
        roi = (annual_income / data['cost']) * 100
        await message.answer(f"Годовая доходность: {roi:.2f}%", reply_markup=get_main_menu())
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@router.callback_query(F.data == "return_to_menu", StateFilter(CalculatorStates))
@error_handler(operation_name="Возврат из калькулятора в главное меню")
async def return_from_calc(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=get_main_menu())
    await callback.answer()