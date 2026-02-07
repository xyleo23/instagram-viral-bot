"""
Сервис загрузки изображений на Яндекс.Диск.
"""
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import aiohttp
import base64
from loguru import logger

from app.config import get_config


class YandexDiskUploader:
    """Сервис загрузки файлов на Яндекс.Диск."""
    
    def __init__(self, token: str):
        """
        Инициализация.
        
        Args:
            token: OAuth токен Яндекс.Диска
        """
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает HTTP сессию."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=300)
            headers = {"Authorization": f"OAuth {self.token}"}
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        return self._session
    
    async def close(self):
        """Закрывает HTTP сессию."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def upload_images(
        self,
        images: List[str],
        folder_path: Optional[str] = None,
        post_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Загружает изображения на Яндекс.Диск.
        
        Args:
            images: Список изображений (base64 или URL)
            folder_path: Путь к папке (если None, генерируется автоматически)
            post_id: ID поста (для имени папки)
        
        Returns:
            dict: {
                "folder_url": str,
                "uploaded_files": List[str],
                "total_size_mb": float
            }
        """
        logger.info(f"Uploading {len(images)} images to Yandex.Disk")
        
        # 1. Генерируем путь к папке
        if not folder_path:
            folder_path = self._generate_folder_path(post_id)
        
        # 2. Создаем папку
        await self._create_folder(folder_path)
        
        # 3. Загружаем каждое изображение
        uploaded_files = []
        total_size = 0
        
        for idx, image_data in enumerate(images, 1):
            try:
                filename = f"slide_{idx}.png"
                remote_path = f"{folder_path}/{filename}"
                
                # Загружаем
                file_size = await self._upload_file(image_data, remote_path)
                
                uploaded_files.append(remote_path)
                total_size += file_size
                
                logger.info(f"Uploaded {filename} ({file_size / 1024:.1f} KB)")
                
            except Exception as e:
                logger.error(f"Error uploading image {idx}: {e}")
                continue
        
        # 4. Получаем публичную ссылку на папку
        folder_url = await self.get_public_url(folder_path)
        
        result = {
            "folder_path": folder_path,
            "folder_url": folder_url,
            "uploaded_files": uploaded_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
        
        logger.info(
            f"Upload completed: {len(uploaded_files)} files, "
            f"{result['total_size_mb']} MB"
        )
        
        return result
    
    async def _create_folder(self, path: str) -> None:
        """
        Создает папку на Яндекс.Диске.
        
        Args:
            path: Путь к папке
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/resources"
        params = {"path": path}
        
        async with session.put(url, params=params) as resp:
            if resp.status == 201:
                logger.info(f"Folder created: {path}")
            elif resp.status == 409:
                logger.debug(f"Folder already exists: {path}")
            else:
                resp.raise_for_status()
    
    async def _upload_file(
        self,
        file_data: str,
        remote_path: str
    ) -> int:
        """
        Загружает файл на Яндекс.Диск.
        
        Args:
            file_data: Base64 строка или URL изображения
            remote_path: Путь на Яндекс.Диске
        
        Returns:
            Размер файла в байтах
        """
        session = await self._get_session()
        
        # 1. Получаем URL для загрузки
        upload_url = await self._get_upload_url(remote_path)
        
        # 2. Подготавливаем данные файла
        if file_data.startswith("data:image"):
            # Base64 изображение
            img_base64 = file_data.split(",")[1]
            file_bytes = base64.b64decode(img_base64)
        elif file_data.startswith("http"):
            # URL изображения - скачиваем
            async with session.get(file_data) as resp:
                resp.raise_for_status()
                file_bytes = await resp.read()
        else:
            raise ValueError(f"Unknown file format: {file_data[:50]}")
        
        # 3. Загружаем файл
        async with session.put(upload_url, data=file_bytes) as resp:
            resp.raise_for_status()
        
        return len(file_bytes)
    
    async def _get_upload_url(self, path: str) -> str:
        """
        Получает URL для загрузки файла.
        
        Args:
            path: Путь к файлу
        
        Returns:
            URL для загрузки
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/resources/upload"
        params = {"path": path, "overwrite": "true"}
        
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["href"]
    
    async def get_public_url(self, path: str) -> str:
        """
        Получает публичную ссылку на файл/папку.
        
        Args:
            path: Путь к ресурсу
        
        Returns:
            Публичная ссылка
        """
        session = await self._get_session()
        
        # 1. Публикуем ресурс
        url = f"{self.base_url}/resources/publish"
        params = {"path": path}
        
        async with session.put(url, params=params) as resp:
            if resp.status not in (200, 201):
                logger.warning(f"Could not publish {path}")
                return ""
        
        # 2. Получаем метаданные с публичной ссылкой
        url = f"{self.base_url}/resources"
        params = {"path": path}
        
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("public_url", "")
    
    def _generate_folder_path(self, post_id: Optional[int] = None) -> str:
        """
        Генерирует путь к папке.
        
        Format: /Instagram_Content/2026-01/post_12345
        
        Args:
            post_id: ID поста
        
        Returns:
            Путь к папке
        """
        now = datetime.now()
        year_month = now.strftime("%Y-%m")
        
        base_path = f"/Instagram_Content/{year_month}"
        
        if post_id:
            return f"{base_path}/post_{post_id}"
        else:
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            return f"{base_path}/carousel_{timestamp}"
    
    async def get_disk_info(self) -> Dict[str, Any]:
        """
        Получает информацию о диске.
        
        Returns:
            dict: {
                "total_space": int (bytes),
                "used_space": int (bytes),
                "free_space": int (bytes)
            }
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/"
        
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            
            total = data.get("total_space", 0)
            used = data.get("used_space", 0)
            
            return {
                "total_space": total,
                "used_space": used,
                "free_space": total - used,
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round((total - used) / (1024**3), 2)
            }


# ==================== USAGE EXAMPLE ====================

async def main():
    """Пример использования."""
    config = get_config()
    
    uploader = YandexDiskUploader(token=config.YANDEX_DISK_TOKEN)
    
    try:
        # Информация о диске
        disk_info = await uploader.get_disk_info()
        print(f"💾 Disk Info:")
        print(f"   Total: {disk_info['total_gb']} GB")
        print(f"   Used: {disk_info['used_gb']} GB")
        print(f"   Free: {disk_info['free_gb']} GB\n")
        
        # Тестовые изображения (из carousel_output)
        test_images = []
        
        import os
        carousel_dir = "carousel_output"
        if os.path.exists(carousel_dir):
            for filename in sorted(os.listdir(carousel_dir)):
                if filename.endswith(".png"):
                    filepath = os.path.join(carousel_dir, filename)
                    
                    # Конвертируем в base64
                    with open(filepath, "rb") as f:
                        img_bytes = f.read()
                        img_base64 = base64.b64encode(img_bytes).decode()
                        test_images.append(f"data:image/png;base64,{img_base64}")
        
        if not test_images:
            print("⚠️  No images found in carousel_output/")
            print("Run 'python scripts/test_carousel.py' first")
            return
        
        print(f"📤 Uploading {len(test_images)} images...\n")
        
        result = await uploader.upload_images(
            images=test_images,
            post_id=12345
        )
        
        print("✅ Upload completed!")
        print(f"📁 Folder: {result['folder_path']}")
        print(f"🔗 Public URL: {result['folder_url']}")
        print(f"📊 Files: {len(result['uploaded_files'])}")
        print(f"💾 Size: {result['total_size_mb']} MB")
        
    finally:
        await uploader.close()


if __name__ == "__main__":
    from app.utils.logger import setup_logger
    setup_logger()
    asyncio.run(main())
