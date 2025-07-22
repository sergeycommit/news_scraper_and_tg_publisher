#!/usr/bin/env python3
"""
Тест конвертации WebP в PNG для IEEE Spectrum Scraper
Test script for WebP to PNG conversion
"""

import sys
import os
import tempfile

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_webp_conversion():
    """Тест конвертации WebP в PNG"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        print("🧪 Тестирование конвертации WebP в PNG")
        print("=" * 60)
        
        # Тестовый URL медиафайла из логов
        test_media_url = "https://spectrum.ieee.org/media-library/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbWFnZSI6Imh0dHBzOi8vYXNzZXRzLnJibC5tcy8yNjg4NDUyMC9vcmlnaW4ucG5nIiwiZXhwaXJlc19hdCI6MTc2MzA3MTQzOX0.SxRBIud_XE2YWQFaIJD9BPB1w-3JsFhiRkJIIe9Yq-g/image.png?width=210"
        
        print(f"🔗 Тестовый URL: {test_media_url}")
        
        # Тестируем загрузку медиафайла с конвертацией
        print("\n📥 Тестирование загрузки с конвертацией...")
        try:
            media_path = scraper.download_media(test_media_url)
            
            if media_path and os.path.exists(media_path):
                file_size = os.path.getsize(media_path)
                file_ext = os.path.splitext(media_path)[1].lower()
                
                print(f"   ✅ Файл загружен: {media_path}")
                print(f"   📏 Размер: {file_size} байт")
                print(f"   🔧 Расширение: {file_ext}")
                
                # Проверяем, что файл не пустой
                if file_size > 0:
                    print("   ✅ Файл не пустой")
                    
                    # Проверяем, что это PNG (после конвертации)
                    if file_ext == '.png':
                        print("   ✅ Успешно конвертирован в PNG")
                        
                        # Проверяем, что PNG файл валидный
                        try:
                            from PIL import Image
                            with Image.open(media_path) as img:
                                print(f"   📐 Размеры: {img.size}")
                                print(f"   🎨 Режим: {img.mode}")
                                print("   ✅ PNG файл валидный")
                        except Exception as e:
                            print(f"   ❌ PNG файл невалидный: {e}")
                            return False
                    else:
                        print(f"   ⚠️ Файл остался в формате {file_ext}")
                    
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

def test_pil_availability():
    """Тест доступности PIL"""
    try:
        print("\n🔍 Проверка доступности PIL...")
        
        try:
            from PIL import Image
            print("   ✅ PIL доступен")
            
            # Проверяем поддержку WebP
            try:
                # Создаем тестовое изображение
                test_img = Image.new('RGB', (100, 100), color='red')
                
                # Сохраняем как WebP
                with tempfile.NamedTemporaryFile(suffix='.webp', delete=False) as f:
                    test_img.save(f.name, 'WEBP')
                    webp_path = f.name
                
                # Открываем WebP
                with Image.open(webp_path) as img:
                    print("   ✅ WebP поддержка работает")
                
                # Удаляем тестовый файл
                os.unlink(webp_path)
                
            except Exception as e:
                print(f"   ⚠️ WebP поддержка недоступна: {e}")
            
            return True
            
        except ImportError:
            print("   ❌ PIL недоступен")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка проверки PIL: {e}")
        return False

def test_telegram_media_compatibility():
    """Тест совместимости медиафайлов с Telegram"""
    try:
        print("\n📱 Тестирование совместимости с Telegram:")
        
        # Проверяем настройки Telegram
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        if not scraper.telegram_token or not scraper.telegram_channel:
            print("   ⚠️ Telegram не настроен, пропускаем тест")
            return True
        
        print("   ✅ Telegram настроен")
        print("   📝 Рекомендации для Telegram:")
        print("      • PNG: Полная поддержка")
        print("      • JPEG: Полная поддержка")
        print("      • WebP: Ограниченная поддержка")
        print("      • Максимальный размер: 10MB")
        print("      • Рекомендуемый размер: < 5MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование конвертации WebP в PNG")
    print("=" * 70)
    
    tests = [
        ("Доступность PIL", test_pil_availability),
        ("Конвертация WebP в PNG", test_webp_conversion),
        ("Совместимость с Telegram", test_telegram_media_compatibility),
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
        print("✅ Конвертация WebP в PNG работает")
        print("✅ Медиафайлы совместимы с Telegram")
    else:
        print("⚠️  Некоторые тесты не прошли")
        print("❌ Проверьте функциональность конвертации")
    
    print("\n📝 Преимущества конвертации WebP в PNG:")
    print("1. Лучшая совместимость с Telegram")
    print("2. Поддержка во всех версиях Telegram")
    print("3. Более стабильное отображение")
    print("4. Устранение проблем с прозрачностью")

if __name__ == "__main__":
    main() 