#!/usr/bin/env python3
"""
Тестовый скрипт для проверки валидности GIF файлов
"""

import requests
import tempfile
import os
from urllib.parse import urlparse
from PIL import Image
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gif_download_and_validation():
    """Тестирование скачивания и валидации GIF файла"""
    
    # URL GIF файла из логов
    gif_url = "https://spectrum.ieee.org/media-library/robots-playing-ping-pong-on-an-automated-table-in-a-tech-lab-setting.gif?id=61214827&width=3600&height=2025"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        logger.info(f"Downloading GIF from: {gif_url}")
        
        response = requests.get(gif_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Проверяем content-type
        content_type = response.headers.get('content-type', '')
        logger.info(f"Content-Type: {content_type}")
        
        # Проверяем размер
        file_size = len(response.content)
        logger.info(f"File size: {file_size} bytes")
        
        # Создаем временный файл
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.gif')
        temp_file.write(response.content)
        temp_file.close()
        
        logger.info(f"Saved to: {temp_file.name}")
        
        # Проверяем файл с помощью file command
        import subprocess
        try:
            result = subprocess.run(['file', temp_file.name], capture_output=True, text=True)
            logger.info(f"File type: {result.stdout.strip()}")
        except Exception as e:
            logger.warning(f"Could not run 'file' command: {e}")
        
        # Проверяем с помощью PIL
        try:
            with Image.open(temp_file.name) as img:
                logger.info(f"PIL Image format: {img.format}")
                logger.info(f"PIL Image mode: {img.mode}")
                logger.info(f"PIL Image size: {img.size}")
                
                # Проверяем, является ли это анимированным GIF
                if hasattr(img, 'n_frames') and img.n_frames > 1:
                    logger.info(f"Animated GIF with {img.n_frames} frames")
                else:
                    logger.warning("Not an animated GIF or PIL cannot detect frames")
                
                # Пробуем прочитать первый кадр
                img.seek(0)
                logger.info(f"First frame info: {img.size}, {img.mode}")
                
        except Exception as e:
            logger.error(f"PIL error: {e}")
        
        # Проверяем первые байты файла
        with open(temp_file.name, 'rb') as f:
            header = f.read(10)
            logger.info(f"File header (hex): {header.hex()}")
            
            # GIF должен начинаться с GIF87a или GIF89a
            if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                logger.info("Valid GIF header detected")
            else:
                logger.error("Invalid GIF header")
        
        # Очистка
        try:
            os.unlink(temp_file.name)
            logger.info("Temporary file deleted")
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    test_gif_download_and_validation() 