#!/usr/bin/env python3
"""
Тест загрузки медиафайлов для IEEE Spectrum Scraper
Test script for media download functionality
"""

import sys
import os
import requests
from urllib.parse import urlparse

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_media_download():
    """Тест загрузки медиафайлов"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        print("🧪 Тестирование загрузки медиафайлов")
        print("=" * 60)
        
        # Тестовый URL медиафайла из логов
        test_media_url = "https://spectrum.ieee.org/media-library/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbWFnZSI6Imh0dHBzOi8vYXNzZXRzLnJibC5tcy8yNjg4NDUyMC9vcmlnaW4ucG5nIiwiZXhwaXJlc19hdCI6MTc2MzA3MTQzOX0.SxRBIud_XE2YWQFaIJD9BPB1w-3JsFhiRkJIIe9Yq-g/image.png?width=210"
        
        print(f"🔗 Тестовый URL: {test_media_url}")
        
        # Проверяем доступность URL
        print("\n🔍 Проверка доступности URL...")
        try:
            response = requests.head(test_media_url, headers=scraper.headers, timeout=10)
            print(f"   Статус: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"   Content-Length: {response.headers.get('content-length', 'Unknown')}")
            
            if response.status_code == 200:
                print("   ✅ URL доступен")
            else:
                print("   ❌ URL недоступен")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки URL: {e}")
            return False
        
        # Тестируем загрузку медиафайла
        print("\n📥 Тестирование загрузки...")
        try:
            media_path = scraper.download_media(test_media_url)
            
            if media_path and os.path.exists(media_path):
                file_size = os.path.getsize(media_path)
                print(f"   ✅ Файл загружен: {media_path}")
                print(f"   📏 Размер: {file_size} байт")
                print(f"   🔧 Расширение: {os.path.splitext(media_path)[1]}")
                
                # Проверяем, что файл не пустой
                if file_size > 0:
                    print("   ✅ Файл не пустой")
                    
                    # Удаляем тестовый файл
                    try:
                        os.unlink(media_path)
                        print("   🗑️ Тестовый файл удален")
                    except:
                        print("   ⚠️ Не удалось удалить тестовый файл")
                    
                    return True
                else:
                    print("   ❌ Файл пустой")
                    return False
            else:
                print("   ❌ Файл не загружен")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка загрузки: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_media_extraction():
    """Тест извлечения медиафайлов из статьи"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        print("\n🔍 Тестирование извлечения медиафайлов из статьи:")
        
        # Тестовая статья
        test_article_url = "https://spectrum.ieee.org/topic/robotics/"
        
        print(f"📰 URL статьи: {test_article_url}")
        
        try:
            # Скрапим контент и медиа
            content, media_url = scraper.scrape_article_content_and_media(test_article_url)
            
            print(f"📝 Контент: {len(content)} символов")
            print(f"🖼️ Медиа URL: {media_url}")
            
            if media_url:
                print("   ✅ Медиафайл найден")
                
                # Проверяем тип медиа
                parsed_url = urlparse(media_url)
                path = parsed_url.path.lower()
                
                if any(ext in path for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    print("   🖼️ Тип: Изображение")
                elif any(ext in path for ext in ['.mp4', '.webm', '.avi']):
                    print("   🎥 Тип: Видео")
                else:
                    print("   ❓ Тип: Неизвестный")
                
                return True
            else:
                print("   ❌ Медиафайл не найден")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка скрапинга: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_telegram_media_send():
    """Тест отправки медиафайла в Telegram"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        print("\n📱 Тестирование отправки медиафайла в Telegram:")
        
        # Проверяем настройки Telegram
        if not scraper.telegram_token:
            print("   ❌ Telegram токен не настроен")
            return False
        
        if not scraper.telegram_channel:
            print("   ❌ Telegram канал не настроен")
            return False
        
        print(f"   ✅ Telegram токен: {scraper.telegram_token[:10]}...")
        print(f"   ✅ Telegram канал: {scraper.telegram_channel}")
        
        # Тестируем подключение к Telegram
        try:
            import asyncio
            
            async def test_connection():
                try:
                    me = await scraper.telegram_bot.get_me()
                    print(f"   ✅ Бот подключен: @{me.username}")
                    return True
                except Exception as e:
                    print(f"   ❌ Ошибка подключения к боту: {e}")
                    return False
            
            result = asyncio.run(test_connection())
            return result
            
        except Exception as e:
            print(f"   ❌ Ошибка тестирования Telegram: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование загрузки медиафайлов IEEE Spectrum Scraper")
    print("=" * 70)
    
    tests = [
        ("Загрузка медиафайла", test_media_download),
        ("Извлечение медиа из статьи", test_media_extraction),
        ("Подключение к Telegram", test_telegram_media_send),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ Тест '{test_name}' не прошел")
    
    print("\n" + "=" * 70)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
        print("✅ Загрузка медиафайлов работает корректно")
        print("✅ Telegram подключение работает")
    else:
        print("⚠️  Некоторые тесты не прошли")
        print("❌ Проверьте функциональность загрузки медиафайлов")
    
    print("\n📝 Возможные проблемы:")
    print("1. Медиафайл загружается, но не отображается в Telegram")
    print("2. Проблемы с форматом файла")
    print("3. Ограничения Telegram на размер файла")
    print("4. Проблемы с правами доступа к файлу")

if __name__ == "__main__":
    main() 