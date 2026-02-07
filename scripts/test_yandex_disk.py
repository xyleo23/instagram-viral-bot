"""
Тестирование сервиса загрузки на Яндекс.Диск.
"""
import asyncio
import base64
import os
from pathlib import Path

from app.config import get_config
from app.services.yandex_disk import YandexDiskUploader
from app.utils.logger import setup_logger


async def main():
    """Тестирует Yandex.Disk uploader."""
    config = get_config()
    setup_logger(config.LOG_FILE, "DEBUG")
    
    print("☁️  Testing Yandex.Disk Uploader\n")
    
    uploader = YandexDiskUploader(token=config.YANDEX_DISK_TOKEN)
    
    try:
        # Информация о диске
        disk_info = await uploader.get_disk_info()
        print("💾 Disk Information:")
        print(f"   Total: {disk_info['total_gb']} GB")
        print(f"   Used: {disk_info['used_gb']} GB ({disk_info['used_space']:,} bytes)")
        print(f"   Free: {disk_info['free_gb']} GB\n")
        
        # Загружаем изображения из carousel_output
        carousel_dir = "carousel_output"
        
        if not os.path.exists(carousel_dir):
            print(f"⚠️  Directory {carousel_dir}/ not found")
            print("Run 'python scripts/test_carousel.py' first")
            return
        
        images = []
        for filename in sorted(os.listdir(carousel_dir)):
            if filename.endswith(".png"):
                filepath = os.path.join(carousel_dir, filename)
                
                with open(filepath, "rb") as f:
                    img_bytes = f.read()
                    img_base64 = base64.b64encode(img_bytes).decode()
                    images.append(f"data:image/png;base64,{img_base64}")
        
        print(f"📤 Uploading {len(images)} images to Yandex.Disk...\n")
        
        result = await uploader.upload_images(
            images=images,
            post_id=999
        )
        
        print("\n✅ Upload Successful!\n")
        print("=" * 60)
        print(f"📁 Folder Path: {result['folder_path']}")
        print(f"🔗 Public URL: {result['folder_url']}")
        print(f"📊 Uploaded Files: {len(result['uploaded_files'])}")
        print(f"💾 Total Size: {result['total_size_mb']} MB")
        print("=" * 60)
        
        print("\nUploaded files:")
        for filepath in result['uploaded_files']:
            print(f"  ✓ {filepath}")
        
    finally:
        await uploader.close()


if __name__ == "__main__":
    asyncio.run(main())
