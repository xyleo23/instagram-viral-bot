"""
Сервис AI рерайта постов через OpenRouter API.
Стиль: theivansergeev (Иван Сергеев).
"""
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
import aiohttp
from loguru import logger

from app.config import get_config


# Промпт для переписывания в стиле theivansergeev
REWRITE_PROMPT_TEMPLATE = """
Перепиши текст для Instagram, СОХРАНЯЯ ОРИГИНАЛЬНЫЙ СМЫСЛ И СТИЛЬ.

Ты копирайтер блогера theivansergeev (Иван Сергеев). Стиль Ивана:
- Мотивационный, но без токсичного позитива
- Практичные советы из личного опыта
- Структурированный контент (списки, шаги)
- Простой язык, без воды
- Акцент на действия, а не теорию
- Эмодзи используются умеренно

Требования:
- Сохрани тему и тон оригинала
- Перефразируй, чтобы избежать копирайта
- НЕ меняй смысл и контекст
- Длина caption: {min_length}-{max_length} символов

Формат вывода - JSON:
{{
  "title": "Заголовок поста (до 200 символов)",
  "caption": "Описание для Instagram (до 2200 символов)",
  "hashtags": "#бизнес #мотивация #продуктивность",
  "slides": [
    "Текст слайда 1 (главная идея)",
    "Текст слайда 2",
    ...
    "Текст слайда 5-10"
  ]
}}

Оригинал:
{original_text}
"""

# Промпт для разбивки текста на слайды
SLIDES_PROMPT_TEMPLATE = """
Разбей текст на 5-10 слайдов для Instagram-карусели. Каждый слайд — одна чёткая мысль, 20-40 слов.
Стиль: как у theivansergeev — простой язык, без воды, структурированно.

Ответ СТРОГО JSON массив строк:
["Текст слайда 1", "Текст слайда 2", ...]

Текст:
{text}
"""


class AIRewriter:
    """Сервис AI рерайта через OpenRouter API (стиль theivansergeev)."""
    
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 4000

    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-3.5-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ):
        """
        Инициализация AI Rewriter.
        
        Args:
            api_key: OpenRouter API ключ
            model: Модель AI (по умолчанию anthropic/claude-3.5-sonnet)
            temperature: Температура (0.7 — баланс креативности и стабильности)
            max_tokens: Максимум токенов в ответе
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = self.OPENROUTER_URL
        
        # Стоимость моделей (USD за 1M токенов: input / output)
        self.pricing = {
            "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
            "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
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

    async def rewrite_post(
        self,
        original_text: str,
        author_context: Optional[str] = None,
        min_length: int = 100,
        max_length: int = 2200,
    ) -> Dict[str, Any]:
        """
        Переписывает пост в стиле theivansergeev (Иван Сергеев).
        
        Args:
            original_text: Оригинальный текст поста
            author_context: Доп. контекст об авторе (например @username или описание)
            min_length: Минимальная длина caption в символах (по умолчанию 100)
            max_length: Максимальная длина caption в символах (по умолчанию 2200)
        
        Returns:
            dict: {
                "title": str,
                "caption": str,
                "hashtags": str,
                "slides": List[str],
                "tokens_used": int,
                "cost_usd": float,
                "ai_model": str
            }
        """
        prompt = REWRITE_PROMPT_TEMPLATE.format(
            original_text=original_text.strip(),
            min_length=min_length,
            max_length=max_length,
        )
        if author_context:
            prompt = f"Контекст автора: {author_context}\n\n{prompt}"

        logger.info(
            f"rewrite_post: request model={self.model} prompt_len={len(prompt)} chars"
        )
        try:
            response = await self._call_openrouter(prompt, max_tokens=self.max_tokens)
            content = response["choices"][0]["message"]["content"]
            parsed = await self._parse_response(content)

            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
            cost_usd = self._calculate_cost(prompt_tokens, completion_tokens)

            logger.info(
                f"rewrite_post: tokens prompt={prompt_tokens} completion={completion_tokens} "
                f"total={total_tokens} cost_usd={cost_usd:.4f}"
            )

            if not self._validate_rewrite_result(parsed):
                logger.warning("rewrite_post: validation failed, using fallback")
                parsed = await self._fallback_parse(original_text, slides_count=8)

            parsed["tokens_used"] = total_tokens
            parsed["cost_usd"] = cost_usd
            parsed["ai_model"] = self.model
            return parsed

        except Exception as e:
            logger.error(f"rewrite_post error: {e}", exc_info=True)
            return await self._fallback_parse(original_text, slides_count=8)

    async def generate_slides(self, text: str) -> List[str]:
        """
        Разбивает текст на слайды для карусели (5-10 слайдов).
        
        Args:
            text: Исходный текст (пост или описание)
        
        Returns:
            Список строк — тексты слайдов
        """
        prompt = SLIDES_PROMPT_TEMPLATE.format(text=text.strip())
        logger.info(f"generate_slides: request model={self.model} text_len={len(text)}")
        try:
            response = await self._call_openrouter(
                prompt, max_tokens=min(self.max_tokens, 2000)
            )
            content = response["choices"][0]["message"]["content"]
            slides = self._parse_slides_response(content)

            usage = response.get("usage", {})
            total = usage.get("total_tokens", 0)
            cost = self._calculate_cost(
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
            )
            logger.info(
                f"generate_slides: {len(slides)} slides, tokens={total} cost_usd={cost:.4f}"
            )
            return slides
        except Exception as e:
            logger.error(f"generate_slides error: {e}", exc_info=True)
            return self._fallback_slides(text)

    async def rewrite(
        self,
        text: str,
        author: str,
        slides_count: int = 8,
        style: str = "viral",
    ) -> Dict[str, Any]:
        """
        Переписывает пост в виральный формат карусели (совместимость с processing).
        Вызывает rewrite_post в стиле theivansergeev.
        
        Args:
            text: Оригинальный текст поста
            author: Автор поста (@username)
            slides_count: Желаемое кол-во слайдов (слайды обрезаются/дополняются при необходимости)
            style: Игнорируется, используется стиль theivansergeev
        
        Returns:
            dict: title, slides, caption, hashtags, tokens_used, cost_usd, ai_model
        """
        logger.info(f"rewrite for @{author} ({len(text)} chars)")
        result = await self.rewrite_post(original_text=text, author_context=author)

        slides = result.get("slides", [])
        if len(slides) > slides_count:
            result["slides"] = slides[:slides_count]
        elif len(slides) < slides_count and slides:
            while len(result["slides"]) < slides_count:
                result["slides"].append(slides[-1] if slides else "")

        logger.info(
            f"rewrite completed: {len(result['slides'])} slides, "
            f"{result['tokens_used']} tokens, ${result['cost_usd']:.4f}"
        )
        return result
    
    def _validate_rewrite_result(self, parsed: Dict[str, Any]) -> bool:
        """Проверяет наличие title, caption, hashtags, slides (5-10 слайдов)."""
        if not all(k in parsed for k in ("title", "caption", "hashtags", "slides")):
            return False
        if not isinstance(parsed.get("slides"), list):
            return False
        slides = parsed["slides"]
        if len(slides) < 1 or len(slides) > 15:
            return False
        if any(not (s and str(s).strip()) for s in slides):
            return False
        return True

    def _parse_slides_response(self, content: str) -> List[str]:
        """Парсит из ответа AI JSON-массив строк (слайды)."""
        content = content.strip()
        # Убираем markdown code block
        m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", content)
        if m:
            content = m.group(1)
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Попытка найти массив в тексте
            m = re.search(r"\[[\s\S]*\]", content)
            if m:
                try:
                    data = json.loads(m.group(0))
                except json.JSONDecodeError:
                    return []
            else:
                return []
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return [s.strip() for s in data if s and s.strip()]
        return []

    def _fallback_slides(self, text: str) -> List[str]:
        """Простая разбивка на слайды по предложениям."""
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 15]
        if not sentences:
            return [text[:200]] if text else []
        slides = []
        per_slide = max(1, (len(sentences) + 4) // 5)
        for i in range(0, len(sentences), per_slide):
            part = " ".join(sentences[i : i + per_slide])
            if part:
                slides.append(part[:300])
            if len(slides) >= 10:
                break
        return slides if slides else [text[:200]]

    async def _call_openrouter(
        self,
        prompt: str,
        retry_count: int = 3,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Отправляет запрос в OpenRouter API. Логирует запрос и токены.
        
        Args:
            prompt: Текст запроса (user message)
            retry_count: Количество попыток при ошибке
            max_tokens: Лимит токенов ответа (по умолчанию self.max_tokens)
        
        Returns:
            Ответ API (choices, usage, ...)
        """
        session = await self._get_session()
        tokens_limit = max_tokens if max_tokens is not None else self.max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/instagram-bot",
            "X-Title": "Instagram Bot AI Rewriter",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": tokens_limit,
        }

        logger.debug(
            f"OpenRouter request model={self.model} temperature={self.temperature} "
            f"max_tokens={tokens_limit} prompt_len={len(prompt)}"
        )
        last_error = None

        for attempt in range(retry_count):
            try:
                async with session.post(
                    self.base_url, headers=headers, json=payload
                ) as resp:
                    result = await resp.json()
                    if resp.status != 200:
                        err_msg = result.get("error", {}).get("message", resp.reason)
                        raise aiohttp.ClientResponseError(
                            resp.request_info,
                            resp.history,
                            status=resp.status,
                            message=err_msg,
                        )
                    usage = result.get("usage", {})
                    logger.info(
                        f"OpenRouter response tokens: prompt={usage.get('prompt_tokens', 0)} "
                        f"completion={usage.get('completion_tokens', 0)} "
                        f"total={usage.get('total_tokens', 0)}"
                    )
                    return result
            except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
                last_error = e
                logger.warning(
                    f"OpenRouter attempt {attempt + 1}/{retry_count} failed: {e}"
                )
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                last_error = e
                logger.error(f"OpenRouter unexpected error: {e}", exc_info=True)
                break

        raise Exception(
            f"OpenRouter API failed after {retry_count} attempts: {last_error}"
        )
    
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
        temperature=config.OPENROUTER_TEMPERATURE,
        max_tokens=config.OPENROUTER_MAX_TOKENS,
    )

    test_post = """
    Сегодня я хочу поделиться с вами своим опытом запуска успешного онлайн-бизнеса.
    Главное что я понял за 5 лет: успех это не про идеи, а про исполнение.
    У меня было 10 идей которые провалились, и только одна выстрелила.
    Ключ к успеху: начать делать, получать обратную связь, улучшать продукт.
    Не ждите идеального момента. Он никогда не наступит.
    """

    try:
        # Основной метод — переписывание в стиле theivansergeev
        result = await rewriter.rewrite_post(
            original_text=test_post,
            author_context="@theivansergeev",
        )
        print("\n✅ rewrite_post (theivansergeev) completed!\n")
        print(f"📝 Title: {result['title']}")
        print(f"\n📊 Slides ({len(result['slides'])}):")
        for i, slide in enumerate(result["slides"], 1):
            print(f"  {i}. {slide[:80]}...")
        print(f"\n💬 Caption: {result['caption'][:100]}...")
        print(f"🏷️  Hashtags: {result['hashtags']}")
        print(f"\n💰 Cost: ${result['cost_usd']:.4f}  Tokens: {result['tokens_used']}")

        # Отдельно: только разбить текст на слайды
        slides_only = await rewriter.generate_slides(test_post)
        print(f"\n✅ generate_slides: {len(slides_only)} slides")
    finally:
        await rewriter.close()


if __name__ == "__main__":
    from app.utils.logger import setup_logger
    setup_logger()
    asyncio.run(main())
