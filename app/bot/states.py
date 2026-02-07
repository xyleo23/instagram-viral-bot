from aiogram.fsm.state import State, StatesGroup


class ApprovalStates(StatesGroup):
    """Состояния для процесса одобрения постов."""
    waiting_approval = State()
    editing_caption = State()
    editing_hashtags = State()


class ManualParsingStates(StatesGroup):
    """Состояния для ручного парсинга."""
    waiting_username = State()
