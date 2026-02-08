from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.config import get_config
from app.models import get_session, OriginalPost, ProcessedPost, PostStatus, ProcessedStatus
from app.bot.keyboards.inline_keyboards import get_main_menu
from sqlalchemy import select, func
from datetime import datetime, timedelta

router = Router(name="start")
config = get_config()


class ParsingStates(StatesGroup):
    """FSM состояния для парсинга."""
    waiting_for_username = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start.
    
    Приветствует пользователя и показывает главное меню.
    """
    # Проверка прав доступа
    if message.from_user.id != config.ADMIN_CHAT_ID:
        await message.answer("❌ У вас нет доступа к этому боту.")
        return
    
    text = """
🎉 *Добро пожаловать в Instagram Viral Bot!*

Я автоматизирую создание вирусного контента для Instagram:

*Как работает:*
1️⃣ Каждые 6 часов парсю топовых авторов
2️⃣ Фильтрую вирусные посты (5000+ лайков)
3️⃣ Переписываю через AI (Claude 3.5)
4️⃣ Генерирую карусель из 8 слайдов
5️⃣ Загружаю на Яндекс.Диск
6️⃣ Отправляю вам на одобрение

*Доступные команды:*
/queue - посмотреть очередь на одобрение
/status - статус системы
/history - история постов
/parse - парсить конкретный аккаунт
/help - помощь

Выберите действие:
"""
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    
    logger.info(f"User {message.from_user.id} started bot")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Показывает справку по командам."""
    if message.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    text = """
📖 *Справка по командам*

*Основные команды:*
/start - главное меню
/queue - очередь постов на одобрение
/status - статус системы и статистика
/history - история обработанных постов
/parse <username> - парсить конкретный аккаунт

*Процесс одобрения:*
• Когда готов новый пост, я пришлю его вам
• Вы можете одобрить (✅), отклонить (❌) или отредактировать (✏️)
• После одобрения пост готов к публикации

*Статусы постов:*
🔍 Parsing - в процессе парсинга
✅ Filtered - прошел фильтр
⚙️ Processing - обрабатывается AI
⏳ Pending - ждет одобрения
✔️ Approved - одобрен
❌ Rejected - отклонен
📤 Posted - опубликован
"""
    
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("status"))
async def cmd_status(message: Message):
    """
    Показывает статус системы и статистику.
    """
    if message.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    await message.answer("⏳ Собираю статистику...")
    
    try:
        async for session in get_session():
            # Посты на одобрении
            pending_result = await session.execute(
                select(func.count(ProcessedPost.id))
                .where(ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL)
            )
            pending_count = pending_result.scalar() or 0
            
            # Обработано сегодня
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_result = await session.execute(
                select(func.count(OriginalPost.id))
                .where(OriginalPost.created_at >= today_start)
            )
            today_count = today_result.scalar() or 0
            
            # Всего постов
            total_result = await session.execute(
                select(func.count(OriginalPost.id))
            )
            total_count = total_result.scalar() or 0
            
            # Одобрено всего
            approved_result = await session.execute(
                select(func.count(ProcessedPost.id))
                .where(ProcessedPost.status == ProcessedStatus.APPROVED)
            )
            approved_count = approved_result.scalar() or 0
        
        text = f"""
📊 *Статус системы*

*Очередь:*
⏳ На одобрении: {pending_count} постов

*Статистика сегодня:*
🆕 Распарсено: {today_count} постов

*Всего:*
📝 Всего постов: {total_count}
✅ Одобрено: {approved_count}

*Настройки:*
👥 Авторов отслеживается: {len(config.instagram_authors_list)}
❤️ Минимум лайков: {config.MIN_LIKES:,}
📅 Макс. возраст: {config.MAX_POST_AGE_DAYS} дней

*Система:*
🤖 Бот: Работает
⚙️ Celery Workers: Активны
📦 База данных: Подключена
"""
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.answer("❌ Ошибка при получении статистики")


@router.callback_query(F.data == "show_status")
async def callback_show_status(callback: CallbackQuery):
    """Callback для кнопки статуса."""
    await callback.answer()
    
    # Проверка админа
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    try:
        async for session in get_session():
            # Посты на одобрении
            pending_result = await session.execute(
                select(func.count(ProcessedPost.id))
                .where(ProcessedPost.status == ProcessedStatus.PENDING_APPROVAL)
            )
            pending_count = pending_result.scalar() or 0
            
            # Одобренные посты
            approved_result = await session.execute(
                select(func.count(ProcessedPost.id))
                .where(ProcessedPost.status == ProcessedStatus.APPROVED)
            )
            approved_count = approved_result.scalar() or 0
            
            # Опубликованные посты
            posted_result = await session.execute(
                select(func.count(ProcessedPost.id))
                .where(ProcessedPost.status == ProcessedStatus.POSTED)
            )
            posted_count = posted_result.scalar() or 0
            
            # Отклоненные посты
            rejected_result = await session.execute(
                select(func.count(ProcessedPost.id))
                .where(ProcessedPost.status == ProcessedStatus.REJECTED)
            )
            rejected_count = rejected_result.scalar() or 0
            
            text = (
                "📊 *Статус системы*\n\n"
                f"🔄 Бот работает\n"
                f"⏳ На одобрении: {pending_count}\n"
                f"✅ Одобрено: {approved_count}\n"
                f"📤 Опубликовано: {posted_count}\n"
                f"❌ Отклонено: {rejected_count}\n"
            )
            
            await callback.message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            
    except Exception as e:
        logger.error(f"Error showing status: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики",
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data == "start_parsing")
async def callback_start_parsing(callback: CallbackQuery, state: FSMContext):
    """Запрос username для парсинга."""
    await callback.answer()
    
    if callback.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    await state.set_state(ParsingStates.waiting_for_username)
    await callback.message.edit_text(
        "🔎 *Парсинг Instagram аккаунта*\n\n"
        "Введите username аккаунта для парсинга (без @):",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )


@router.message(ParsingStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    """Обработка введённого username."""
    if message.from_user.id != config.ADMIN_CHAT_ID:
        return
    
    username = message.text.strip().replace("@", "")
    
    if not username:
        await message.answer("❌ Username не может быть пустым!", reply_markup=get_main_menu())
        return
    
    await state.clear()
    
    try:
        from app.workers.tasks.parsing import parse_specific_account
        
        task = parse_specific_account.delay(username)
        
        await message.answer(
            f"✅ *Задача на парсинг запущена!*\n\n"
            f"Аккаунт: @{username}\n"
            f"Task ID: {task.id}\n\n"
            f"Результаты появятся в очереди на одобрение.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        
        logger.info(f"Parsing task started for @{username}, task_id={task.id}")
        
    except Exception as e:
        logger.error(f"Error starting parsing task: {e}")
        await message.answer(
            f"❌ Ошибка при запуске парсинга:\n{str(e)}",
            reply_markup=get_main_menu()
        )
