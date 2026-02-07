"""
Сервис AI рерайта постов через OpenRouter API.
"""
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from loguru import logger

from app.config import get_config


class AIRewriter:
    """Сервис AI рерайта через OpenRouter API."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-3.5-sonnet",
        temperature: float = 0.85
    ):
        """
        Инициализация AI Rewriter.
        
        Args:
            api_key: OpenRouter API ключ
            model: Модель AI (claude-3.5-sonnet, gpt-4-turbo, gemini-pro-1.5)
            temperature: Температура (0-1, выше = более креативно)
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Стоимость моделей (за 1M токенов)
        self.pricing = {
            "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
            "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "google/gemini-pro-1.5": {"input": 1.25, "output": 5.0},
        }
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает HTTP сессию."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=120)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Закрывает HTTP сессию."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def rewrite(
        self,
        text: str,
        author: str,
        slides_count: int = 8,
        style: str = "viral"
    ) -> Dict[str, Any]:
        """
        Переписывает пост в виральный формат карусели.
        
        Args:
            text: Оригинальный текст поста
            author: Автор поста (@username)
            slides_count: Количество слайдов (обычно 8)
            style: Стиль переписывания (viral, minimalist, educational)
        
        Returns:
            dict: {
                "title": str,           # Цепляющий заголовок (5-10 слов)
                "slides": List[str],    # Тексты для слайдов
                "caption": str,         # Caption для Instagram
                "hashtags": str,        # Хештеги
                "tokens_used": int,     # Использовано токенов
                "cost_usd": float       # Стоимость запроса
            }
        """
        logger.info(f"Starting AI rewrite for @{author} post ({len(text)} chars)")
        
        try:
            # 1. Построить промпт
            prompt = self._build_prompt(text, author, slides_count, style)
            
            # 2. Отправить запрос в OpenRouter
            response = await self._call_openrouter(prompt)
            
            # 3. Парсить ответ
            content = response["choices"][0]["message"]["content"]
            parsed = await self._parse_response(content)
            
            # 4. Валидация
            if not self._validate_result(parsed, slides_count):
                logger.warning("AI response validation failed, using fallback")
                parsed = await self._fallback_parse(text, slides_count)
            
            # 5. Подсчет стоимости
            usage = response.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            cost_usd = self._calculate_cost(
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0)
            )
            
            # 6. Добавление метрик
            parsed["tokens_used"] = tokens_used
            parsed["cost_usd"] = cost_usd
            parsed["ai_model"] = self.model
            
            logger.info(
                f"AI rewrite completed: {len(parsed['slides'])} slides, "
                f"{tokens_used} tokens, ${cost_usd:.4f}"
            )
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error in AI rewrite: {e}")
            # Fallback на простой парсинг
            return await self._fallback_parse(text, slides_count)
    
    def _build_prompt(
        self,
        text: str,
        author: str,
        slides_count: int,
        style: str
    ) -> str:
        """
        Строит промпт для AI.
        
        Returns:
            Промпт в формате системного сообщения
        """
        system_prompt = f"""Ты эксперт по созданию вирального контента для Instagram в стиле топовых блогеров (@theivansergeev, @sanyaagainst).

Твоя задача: переписать пост в формат КАРУСЕЛИ из {slides_count} слайдов для максимального вовлечения.

СТРУКТУРА:

**Слайд 1** (Заголовок):
- Цепляющий заголовок 5-10 слов
- Вызывает любопытство
- Обещание ценности
- Примеры: "7 ошибок которые убивают ваш бизнес", "Как я заработал 1M на AI за месяц"

**Слайды 2-{slides_count}** (Содержание):
- По 20-30 слов на слайд
- Каждый слайд = одна мысль
- Простой язык, без воды
- Конкретика и примеры
- Эмоциональные триггеры

СТИЛЬ:
- Как у {author} (изучи его стиль)
- Минимализм в дизайне
- Максимум ценности
- Разговорный тон
- Короткие предложения

ПРАВИЛА:
- Сохрани главную мысль оригинала
- Добавь структуру и логику
- Убери воду и повторы
- Добавь эмоции и примеры
- НЕ копируй текст 1:1

ОТВЕТ СТРОГО В JSON:
{{
  "title": "Цепляющий заголовок",
  "slides": ["Слайд 1 текст", "Слайд 2 текст", ...],
  "caption": "Основной текст для описания поста в Instagram",
  "hashtags": "#тег1 #тег2 #тег3"
}}

ОРИГИНАЛЬНЫЙ ПОСТ:
{text}

Переписывай!"""

        return system_prompt
    
    async def _call_openrouter(self, prompt: str, retry_count: int = 3) -> Dict[str, Any]:
        """
        Отправляет запрос в OpenRouter API с retry логикой.
        
        Args:
            prompt: Промпт
            retry_count: Количество попыток
        
        Returns:
            Ответ API
        """
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Опционально
            "X-Title": "Instagram Viral Bot"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": 2000,
            "top_p": 1,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5
        }
        
        last_error = None
        
        for attempt in range(retry_count):
            try:
                logger.debug(f"OpenRouter API call attempt {attempt + 1}/{retry_count}")
                
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                ) as resp:
                    resp.raise_for_status()
                    result = await resp.json()
                    
                    logger.info(
                        f"OpenRouter API success: {result.get('usage', {}).get('total_tokens', 0)} tokens"
                    )
                    
                    return result
                    
            except aiohttp.ClientError as e:
                last_error = e
                logger.warning(f"OpenRouter API error (attempt {attempt + 1}): {e}")
                
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in OpenRouter API call: {e}")
                break
        
        raise Exception(f"OpenRouter API failed after {retry_count} attempts: {last_error}")
    
    async def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        Парсит JSON из ответа AI.
        
        AI может вернуть JSON в markdown блоке или просто текст.
        
        Args:
            content: Текст ответа
        
        Returns:
            Распарсенный dict
        """
        # Попытка 1: Извлечь JSON из markdown блока
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Попытка 2: Извлечь любой JSON блок
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Попытка 3: Весь content это JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Если ничего не сработало - бросаем ошибку
        raise ValueError(f"Could not parse JSON from AI response: {content[:200]}")
    
    def _validate_result(self, parsed: Dict[str, Any], expected_slides: int) -> bool:
        """
        Валидирует результат парсинга.
        
        Args:
            parsed: Распарсенный результат
            expected_slides: Ожидаемое количество слайдов
        
        Returns:
            True если валидный
        """
        required_keys = ["title", "slides", "caption", "hashtags"]
        
        # Проверяем наличие ключей
        if not all(k in parsed for k in required_keys):
            logger.warning(f"Missing required keys: {set(required_keys) - set(parsed.keys())}")
            return False
        
        # Проверяем slides
        if not isinstance(parsed["slides"], list):
            logger.warning("slides is not a list")
            return False
        
        if len(parsed["slides"]) < expected_slides - 2:
            logger.warning(f"Too few slides: {len(parsed['slides'])} < {expected_slides - 2}")
            return False
        
        # Проверяем что слайды не пустые
        if any(not slide or len(slide.strip()) < 10 for slide in parsed["slides"]):
            logger.warning("Some slides are too short")
            return False
        
        return True
    
    async def _fallback_parse(
        self,
        text: str,
        slides_count: int
    ) -> Dict[str, Any]:
        """
        Fallback парсинг если AI не вернул JSON.
        
        Простая логика: разбивает текст на предложения и группирует.
        
        Args:
            text: Оригинальный текст
            slides_count: Количество слайдов
        
        Returns:
            Структурированный результат
        """
        logger.warning("Using fallback parsing")
        
        # Разбиваем на предложения
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
        if not sentences:
            sentences = [text]
        
        # Группируем в слайды
        slides = []
        sentences_per_slide = max(1, len(sentences) // slides_count)
        
        for i in range(0, len(sentences), sentences_per_slide):
            slide_text = ' '.join(sentences[i:i+sentences_per_slide])
            if slide_text:
                # Ограничиваем длину слайда
                if len(slide_text) > 150:
                    slide_text = slide_text[:147] + "..."
                slides.append(slide_text)
            
            if len(slides) >= slides_count:
                break
        
        # Заполняем если не хватает
        while len(slides) < slides_count:
            slides.append(sentences[0] if sentences else text[:100])
        
        # Заголовок = первое предложение
        title = sentences[0][:60] if sentences else "Важная информация"
        
        return {
            "title": title,
            "slides": slides[:slides_count],
            "caption": text[:500],
            "hashtags": "#мотивация #успех #саморазвитие #бизнес #ai",
            "tokens_used": 0,
            "cost_usd": 0.0,
            "ai_model": "fallback"
        }
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Подсчитывает стоимость запроса.
        
        Args:
            prompt_tokens: Входные токены
            completion_tokens: Выходные токены
        
        Returns:
            Стоимость в USD
        """
        pricing = self.pricing.get(self.model, {"input": 5.0, "output": 15.0})
        
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost


# ==================== USAGE EXAMPLE ====================

async def main():
    """Пример использования AI Rewriter."""
    config = get_config()
    
    rewriter = AIRewriter(
        api_key=config.OPENROUTER_API_KEY,
        model=config.OPENROUTER_MODEL,
        temperature=0.85
    )
    
    # Тестовый пост
    test_post = """
    Сегодня я хочу поделиться с вами своим опытом запуска успешного онлайн-бизнеса.
    
    Главное что я понял за 5 лет: успех это не про идеи, а про исполнение.
    
    У меня было 10 идей которые провалились, и только одна выстрелила.
    
    Но эта одна идея изменила всю мою жизнь. Сейчас мой доход 500к+ в месяц.
    
    Ключ к успеху: начать делать, получать обратную связь, улучшать продукт.
    
    Не ждите идеального момента. Он никогда не наступит.
    """
    
    try:
        result = await rewriter.rewrite(
            text=test_post,
            author="@testauthor",
            slides_count=8
        )
        
        print("\n✅ AI Rewrite completed!\n")
        print(f"📝 Title: {result['title']}")
        print(f"\n📊 Slides ({len(result['slides'])}):")
        for i, slide in enumerate(result['slides'], 1):
            print(f"  {i}. {slide[:80]}...")
        
        print(f"\n💬 Caption: {result['caption'][:100]}...")
        print(f"🏷️  Hashtags: {result['hashtags']}")
        print(f"\n💰 Cost: ${result['cost_usd']:.4f}")
        print(f"🔢 Tokens: {result['tokens_used']}")
        
    finally:
        await rewriter.close()


if __name__ == "__main__":
    from app.utils.logger import setup_logger
    setup_logger()
    asyncio.run(main())
