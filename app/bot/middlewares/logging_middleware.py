from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from loguru import logger


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех событий."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Логирует входящие события.
        
        Args:
            handler: Следующий handler в цепочке
            event: Событие (Message, CallbackQuery, etc.)
            data: Дополнительные данные
        
        Returns:
            Результат handler'а
        """
        # Логируем сообщения
        if isinstance(event, Message):
            logger.info(
                f"Message from {event.from_user.id} (@{event.from_user.username}): "
                f"{event.text or event.caption or '[media]'}"
            )
        
        # Логируем callback queries
        elif isinstance(event, CallbackQuery):
            logger.info(
                f"Callback from {event.from_user.id} (@{event.from_user.username}): "
                f"{event.data}"
            )
        
        # Вызываем handler
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error in handler: {e}", exc_info=True)
            
            # Отправляем сообщение об ошибке пользователю
            if isinstance(event, Message):
                await event.answer("❌ Произошла ошибка. Попробуйте позже.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Ошибка", show_alert=True)
            
            raise
