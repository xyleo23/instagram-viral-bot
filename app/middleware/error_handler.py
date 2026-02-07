"""
Middleware для обработки ошибок
"""
from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from app.utils.logger import log


class ErrorHandlerMiddleware(BaseMiddleware):
    """Обрабатывает ошибки в обработчиках"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            log.error(f"Ошибка в обработчике: {e}", exc_info=True)
            # Можно отправить сообщение пользователю
            if hasattr(event, 'answer'):
                try:
                    await event.answer("❌ Произошла ошибка. Попробуйте позже.")
                except:
                    pass
            raise
