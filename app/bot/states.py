from aiogram.fsm.state import State, StatesGroup


class ApprovalStates(StatesGroup):
    """Состояния для процесса одобрения постов."""
    waiting_approval = State()
    editing_caption = State()
    editing_hashtags = State()


class ManualParsingStates(StatesGroup):
    """Состояния для ручного парсинга."""
    waiting_username = State()


class AddAuthorStates(StatesGroup):
    """Состояния для добавления автора."""
    username = State()
    min_likes = State()
    max_age_days = State()
    confirm = State()


class EditAuthorStates(StatesGroup):
    """Состояния для редактирования автора."""
    field_choice = State()
    new_value = State()
