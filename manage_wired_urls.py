#!/usr/bin/env python3
"""
Управление опубликованными URL-ами Wired
Позволяет просматривать, добавлять и удалять URL-ы из списка опубликованных
"""

import json
import os
import sys
from datetime import datetime

class WiredURLManager:
    def __init__(self):
        self.published_urls_file = 'wired_published_urls.json'
        self.published_urls = self.load_published_urls()
    
    def load_published_urls(self):
        """Загрузка списка опубликованных URL"""
        try:
            if os.path.exists(self.published_urls_file):
                with open(self.published_urls_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('published_urls', [])
            else:
                print(f"Published URLs file not found: {self.published_urls_file}")
                return []
        except Exception as e:
            print(f"Error loading published URLs: {e}")
            return []
    
    def save_published_urls(self):
        """Сохранение списка опубликованных URL"""
        try:
            data = {'published_urls': self.published_urls}
            with open(self.published_urls_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.published_urls)} published URLs")
        except Exception as e:
            print(f"Error saving published URLs: {e}")
    
    def add_url(self, url):
        """Добавление URL в список опубликованных"""
        if url not in self.published_urls:
            self.published_urls.append(url)
            self.save_published_urls()
            print(f"Added URL: {url}")
        else:
            print(f"URL already exists: {url}")
    
    def remove_url(self, url):
        """Удаление URL из списка опубликованных"""
        if url in self.published_urls:
            self.published_urls.remove(url)
            self.save_published_urls()
            print(f"Removed URL: {url}")
        else:
            print(f"URL not found: {url}")
    
    def list_urls(self):
        """Просмотр всех опубликованных URL"""
        if not self.published_urls:
            print("No published URLs found")
            return
        
        print(f"\n📋 Published URLs ({len(self.published_urls)}):")
        print("-" * 80)
        for i, url in enumerate(self.published_urls, 1):
            print(f"{i:3d}. {url}")
    
    def search_urls(self, query):
        """Поиск URL по ключевому слову"""
        matching_urls = [url for url in self.published_urls if query.lower() in url.lower()]
        
        if not matching_urls:
            print(f"No URLs found matching '{query}'")
            return
        
        print(f"\n🔍 URLs matching '{query}' ({len(matching_urls)}):")
        print("-" * 80)
        for i, url in enumerate(matching_urls, 1):
            print(f"{i:3d}. {url}")
    
    def clear_all(self):
        """Очистка всех опубликованных URL"""
        if not self.published_urls:
            print("No URLs to clear")
            return
        
        confirm = input(f"Are you sure you want to clear all {len(self.published_urls)} URLs? (y/N): ")
        if confirm.lower() == 'y':
            self.published_urls = []
            self.save_published_urls()
            print("All URLs cleared")
        else:
            print("Operation cancelled")
    
    def export_urls(self, filename=None):
        """Экспорт URL в файл"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'wired_published_urls_export_{timestamp}.txt'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Wired Published URLs Export - {datetime.now().isoformat()}\n")
                f.write(f"Total URLs: {len(self.published_urls)}\n")
                f.write("-" * 80 + "\n\n")
                for url in self.published_urls:
                    f.write(f"{url}\n")
            
            print(f"URLs exported to: {filename}")
        except Exception as e:
            print(f"Error exporting URLs: {e}")
    
    def import_urls(self, filename):
        """Импорт URL из файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Пропускаем заголовки и пустые строки
            urls = [line.strip() for line in lines if line.strip() and not line.startswith('-') and not line.startswith('Wired') and not line.startswith('Total')]
            
            if not urls:
                print("No valid URLs found in file")
                return
            
            # Добавляем новые URL
            added_count = 0
            for url in urls:
                if url not in self.published_urls:
                    self.published_urls.append(url)
                    added_count += 1
            
            self.save_published_urls()
            print(f"Imported {added_count} new URLs from {filename}")
            
        except Exception as e:
            print(f"Error importing URLs: {e}")
    
    def show_stats(self):
        """Показать статистику"""
        print(f"\n📊 Wired URL Manager Statistics:")
        print("-" * 40)
        print(f"Total published URLs: {len(self.published_urls)}")
        print(f"Published URLs file: {self.published_urls_file}")
        
        if self.published_urls:
            # Анализ доменов
            domains = {}
            for url in self.published_urls:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domains[domain] = domains.get(domain, 0) + 1
                except:
                    pass
            
            if domains:
                print(f"\nDomain breakdown:")
                for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {domain}: {count} URLs")
    
    def show_help(self):
        """Показать справку"""
        help_text = """
🤖 Wired URL Manager - Справка

Команды:
  list, l          - Показать все опубликованные URL
  add <url>        - Добавить URL в список опубликованных
  remove <url>     - Удалить URL из списка опубликованных
  search <query>   - Поиск URL по ключевому слову
  clear            - Очистить все URL
  export [file]    - Экспорт URL в файл
  import <file>    - Импорт URL из файла
  stats            - Показать статистику
  help, h          - Показать эту справку
  quit, q          - Выйти

Примеры:
  add https://www.wired.com/article/example
  search robots
  export my_urls.txt
  import backup_urls.txt
        """
        print(help_text)

def main():
    """Основная функция"""
    manager = WiredURLManager()
    
    print("🤖 Wired URL Manager")
    print("Type 'help' for commands or 'quit' to exit")
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if not command:
                continue
            
            parts = command.split()
            cmd = parts[0].lower()
            
            if cmd in ['quit', 'q', 'exit']:
                print("Goodbye!")
                break
            elif cmd in ['help', 'h', '?']:
                manager.show_help()
            elif cmd in ['list', 'l']:
                manager.list_urls()
            elif cmd in ['stats']:
                manager.show_stats()
            elif cmd == 'add' and len(parts) > 1:
                url = parts[1]
                manager.add_url(url)
            elif cmd == 'remove' and len(parts) > 1:
                url = parts[1]
                manager.remove_url(url)
            elif cmd == 'search' and len(parts) > 1:
                query = ' '.join(parts[1:])
                manager.search_urls(query)
            elif cmd == 'clear':
                manager.clear_all()
            elif cmd == 'export':
                filename = parts[1] if len(parts) > 1 else None
                manager.export_urls(filename)
            elif cmd == 'import' and len(parts) > 1:
                filename = parts[1]
                manager.import_urls(filename)
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
