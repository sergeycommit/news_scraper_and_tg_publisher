#!/usr/bin/env python3
"""
Тестовый скрипт для скачивания настоящего GIF файла
"""

import requests
import tempfile
import os
from urllib.parse import urlparse, urlencode, parse_qs
from PIL import Image
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gif_download_methods():
    """Тестирование различных методов скачивания GIF"""
    
    # Базовый URL
    base_url = "https://spectrum.ieee.org/media-library/robots-playing-ping-pong-on-an-automated-table-in-a-tech-lab-setting.gif"
    
    # Различные варианты заголовков
    headers_variants = [
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/gif,image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/gif,*/*',
            'Accept-Encoding': 'identity',
            'Accept-Language': 'en-US,en;q=0.9'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/gif,image/png,image/jpeg,image/webp,*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://spectrum.ieee.org/'
        }
    ]
    
    # Различные варианты параметров
    params_variants = [
        {'id': '61214827', 'width': '3600', 'height': '2025'},
        {'id': '61214827', 'width': '800', 'height': '450'},
        {'id': '61214827', 'width': '1200', 'height': '675'},
        {'id': '61214827', 'format': 'gif'},
        {'id': '61214827', 'format': 'gif', 'width': '800', 'height': '450'},
        {'id': '61214827', 'type': 'gif'},
        {'id': '61214827', 'type': 'gif', 'width': '800', 'height': '450'},
        {}  # Без параметров
    ]
    
    for i, headers in enumerate(headers_variants):
        for j, params in enumerate(params_variants):
            logger.info(f"\n=== Тест {i+1}.{j+1}: Headers {i+1}, Params {j+1} ===")
            
            # Формируем URL
            if params:
                url = f"{base_url}?{urlencode(params)}"
            else:
                url = base_url
            
            logger.info(f"URL: {url}")
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
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
                
                # Проверяем файл с помощью PIL
                try:
                    with Image.open(temp_file.name) as img:
                        logger.info(f"PIL Image format: {img.format}")
                        logger.info(f"PIL Image mode: {img.mode}")
                        logger.info(f"PIL Image size: {img.size}")
                        
                        if img.format == 'GIF':
                            if hasattr(img, 'n_frames') and img.n_frames > 1:
                                logger.info(f"✅ SUCCESS! Animated GIF with {img.n_frames} frames")
                                logger.info(f"File: {temp_file.name}")
                                return temp_file.name
                            else:
                                logger.info("GIF file is not animated")
                        else:
                            logger.info(f"Not a GIF file, format: {img.format}")
                            
                except Exception as e:
                    logger.error(f"PIL error: {e}")
                
                # Очистка
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                    
            except Exception as e:
                logger.error(f"Request error: {e}")
    
    logger.error("❌ Не удалось найти настоящий GIF файл")
    return None

if __name__ == "__main__":
    result = test_gif_download_methods()
    if result:
        logger.info(f"🎉 Найден настоящий GIF: {result}")
    else:
        logger.error("😞 Настоящий GIF не найден") 