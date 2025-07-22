#!/usr/bin/env python3
"""
Утилита для управления списком опубликованных URL IEEE Spectrum
Utility for managing IEEE Spectrum published URLs list
"""

import json
import os
import sys
from datetime import datetime

def load_published_urls():
    """Загрузка списка опубликованных URL"""
    file_path = 'ieee_published_urls.json'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('published_urls', [])
    return []

def save_published_urls(urls):
    """Сохранение списка опубликованных URL"""
    file_path = 'ieee_published_urls.json'
    data = {
        'published_urls': urls,
        'last_updated': datetime.now().isoformat(),
        'total_count': len(urls)
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Сохранено {len(urls)} URL в {file_path}")

def show_help():
    """Показать справку"""
    print("""
🔧 Утилита управления опубликованными URL IEEE Spectrum

Использование:
  python manage_ieee_urls.py [команда] [аргументы]

Команды:
  list                    - Показать все опубликованные URL
  count                   - Показать количество опубликованных URL
  clear                   - Очистить весь список опубликованных URL
  add <url>               - Добавить URL в список
  remove <url>            - Удалить URL из списка
  search <keyword>        - Найти URL содержащие ключевое слово
  help                    - Показать эту справку

Примеры:
  python manage_ieee_urls.py list
  python manage_ieee_urls.py count
  python manage_ieee_urls.py clear
  python manage_ieee_urls.py add "https://spectrum.ieee.org/article/123"
  python manage_ieee_urls.py remove "https://spectrum.ieee.org/article/123"
  python manage_ieee_urls.py search "ai"
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    urls = load_published_urls()
    
    if command == 'list':
        if not urls:
            print("📝 Список опубликованных URL IEEE Spectrum пуст")
        else:
            print(f"📝 Опубликованные URL IEEE Spectrum ({len(urls)}):")
            for i, url in enumerate(urls, 1):
                print(f"  {i}. {url}")
    
    elif command == 'count':
        print(f"📊 Количество опубликованных URL IEEE Spectrum: {len(urls)}")
    
    elif command == 'clear':
        if urls:
            confirm = input("⚠️  Вы уверены, что хотите очистить весь список? (y/N): ")
            if confirm.lower() in ['y', 'yes', 'да']:
                save_published_urls([])
                print("🗑️  Список опубликованных URL IEEE Spectrum очищен")
            else:
                print("❌ Операция отменена")
        else:
            print("📝 Список уже пуст")
    
    elif command == 'add':
        if len(sys.argv) < 3:
            print("❌ Ошибка: укажите URL для добавления")
            return
        
        url = sys.argv[2]
        if url in urls:
            print(f"⚠️  URL уже в списке: {url}")
        else:
            urls.append(url)
            save_published_urls(urls)
            print(f"✅ Добавлен URL: {url}")
    
    elif command == 'remove':
        if len(sys.argv) < 3:
            print("❌ Ошибка: укажите URL для удаления")
            return
        
        url = sys.argv[2]
        if url in urls:
            urls.remove(url)
            save_published_urls(urls)
            print(f"✅ Удален URL: {url}")
        else:
            print(f"⚠️  URL не найден в списке: {url}")
    
    elif command == 'search':
        if len(sys.argv) < 3:
            print("❌ Ошибка: укажите ключевое слово для поиска")
            return
        
        keyword = sys.argv[2].lower()
        found_urls = [url for url in urls if keyword in url.lower()]
        
        if found_urls:
            print(f"🔍 Найдено {len(found_urls)} URL содержащих '{keyword}':")
            for i, url in enumerate(found_urls, 1):
                print(f"  {i}. {url}")
        else:
            print(f"🔍 URL содержащие '{keyword}' не найдены")
    
    elif command == 'help':
        show_help()
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        show_help()

if __name__ == "__main__":
    main() 