"""
Обработчик генерации каруселей
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.utils.logger import log
from app.services.carousel_generator import CarouselGenerator

router = Router()


@router.callback_query(F.data.startswith("generate_"))
async def generate_carousel(callback: CallbackQuery):
    """Генерирует карусель из слайдов"""
    try:
        post_id = int(callback.data.split("_")[1])
        
        await callback.answer("🎨 Генерирую карусель...")
        
        generator = CarouselGenerator()
        # TODO: Получить данные поста из БД
        # media_group = await generator.generate_carousel(post_id)
        
        # if media_group:
        #     await callback.message.answer_media_group(media_group)
        #     await callback.message.answer(
        #         f"🎨 Карусель готова!\n\n"
        #         f"📸 Слайдов: {len(media_group)}\n\n"
        #         f"💡 Скопируйте подпись и опубликуйте в Instagram вручную."
        #     )
        
        await callback.message.answer("⚠️ Генерация каруселей в разработке")
        log.info(f"Запрос на генерацию карусели для поста {post_id}")
        
    except Exception as e:
        log.error(f"Ошибка в generate_carousel: {e}")
        await callback.answer("❌ Ошибка при генерации", show_alert=True)
