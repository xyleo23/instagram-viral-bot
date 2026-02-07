from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from loguru import logger


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех событий."""
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
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
        if event.message:
            msg = event.message
            logger.info(
                f"Message from {msg.from_user.id} (@{msg.from_user.username}): "
                f"{msg.text or '[media]'}"
            )
        
        # Логируем callback queries
        elif event.callback_query:
            cb = event.callback_query
            logger.info(
                f"Callback from {cb.from_user.id} (@{cb.from_user.username}): "
                f"{cb.data}"
            )
        
        # Вызываем handler
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error in handler: {e}", exc_info=True)
            
            # Отправляем сообщение об ошибке пользователю
            if event.message:
                await event.message.answer("❌ Произошла ошибка. Попробуйте позже.")
            elif event.callback_query:
                await event.callback_query.answer("❌ Ошибка", show_alert=True)
            
            raise
