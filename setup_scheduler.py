#!/usr/bin/env python3
"""
Setup Scheduler for TechCrunch Scraper
Скрипт для настройки автоматического запуска на Windows
"""

import os
import sys
import subprocess
from datetime import datetime

def create_batch_file():
    """Создает bat файл для запуска скрапера"""
    current_dir = os.getcwd()
    python_path = sys.executable
    script_path = os.path.join(current_dir, 'run_scraper.py')
    
    batch_content = f'''@echo off
cd /d "{current_dir}"
"{python_path}" "{script_path}"
'''
    
    batch_file = os.path.join(current_dir, 'run_scraper.bat')
    
    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"✅ Создан bat файл: {batch_file}")
    return batch_file

def setup_windows_task():
    """Настройка Windows Task Scheduler"""
    try:
        batch_file = create_batch_file()
        
        # Команда для создания задачи
        task_name = "TechCrunchScraper"
        command = f'''schtasks /create /tn "{task_name}" /tr "{batch_file}" /sc daily /st 09:00 /f'''
        
        print("🔧 Настройка Windows Task Scheduler...")
        print(f"Команда: {command}")
        
        # Выполняем команду
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Задача успешно создана в Windows Task Scheduler")
            print(f"📅 Задача будет запускаться ежедневно в 09:00")
            print(f"📝 Имя задачи: {task_name}")
        else:
            print("❌ Ошибка при создании задачи:")
            print(result.stderr)
            print("\n🔧 Попробуйте запустить от имени администратора:")
            print(f"schtasks /create /tn \"{task_name}\" /tr \"{batch_file}\" /sc daily /st 09:00 /f")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def show_manual_instructions():
    """Показывает инструкции для ручной настройки"""
    print("\n📋 РУЧНАЯ НАСТРОЙКА WINDOWS TASK SCHEDULER:")
    print("1. Откройте 'Планировщик задач' (Task Scheduler)")
    print("2. Нажмите 'Создать задачу'")
    print("3. Введите имя: TechCrunchScraper")
    print("4. Перейдите на вкладку 'Триггеры'")
    print("5. Нажмите 'Создать'")
    print("6. Выберите 'Ежедневно'")
    print("7. Установите время: 09:00")
    print("8. Перейдите на вкладку 'Действия'")
    print("9. Нажмите 'Создать'")
    print("10. В поле 'Программа' введите путь к Python")
    print("11. В поле 'Аргументы' введите: run_scraper.py")
    print("12. В поле 'Рабочая папка' введите путь к проекту")
    print("13. Нажмите 'ОК'")

def main():
    """Главная функция"""
    print("🚀 Настройка автоматического запуска TechCrunch Scraper")
    print("=" * 50)
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📝 Создайте файл .env на основе config.env.example")
        return
    
    print("✅ Файл .env найден")
    
    # Создаем bat файл
    batch_file = create_batch_file()
    
    print("\n🔧 Настройка автоматического запуска...")
    print("Выберите способ настройки:")
    print("1. Автоматическая настройка (требует права администратора)")
    print("2. Показать инструкции для ручной настройки")
    print("3. Только создать bat файл")
    
    choice = input("\nВведите номер (1-3): ").strip()
    
    if choice == "1":
        setup_windows_task()
    elif choice == "2":
        show_manual_instructions()
    elif choice == "3":
        print(f"✅ Bat файл создан: {batch_file}")
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    main() 