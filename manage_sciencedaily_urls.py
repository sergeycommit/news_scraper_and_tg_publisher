#!/usr/bin/env python3
"""
Управление опубликованными URL-ами ScienceDaily
Позволяет просматривать, добавлять и удалять URL-ы из списка опубликованных
"""

import json
import os
import sys
from datetime import datetime

class ScienceDailyURLManager:
    def __init__(self):
        self.published_urls_file = 'sciencedaily_published_urls.json'
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
            data = {
                'published_urls': self.published_urls,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.published_urls_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved {len(self.published_urls)} published URLs")
        except Exception as e:
            print(f"❌ Error saving published URLs: {e}")
    
    def show_all_urls(self):
        """Показать все опубликованные URL"""
        if not self.published_urls:
            print("📭 No published URLs found")
            return
        
        print(f"📚 Found {len(self.published_urls)} published URLs:")
        print("-" * 80)
        
        for i, url in enumerate(self.published_urls, 1):
            print(f"{i:3d}. {url}")
        
        print("-" * 80)
    
    def add_url(self, url):
        """Добавить URL в список опубликованных"""
        if url in self.published_urls:
            print(f"⚠️  URL already exists: {url}")
            return
        
        self.published_urls.append(url)
        self.save_published_urls()
        print(f"✅ Added URL: {url}")
    
    def remove_url(self, url):
        """Удалить URL из списка опубликованных"""
        if url not in self.published_urls:
            print(f"⚠️  URL not found: {url}")
            return
        
        self.published_urls.remove(url)
        self.save_published_urls()
        print(f"✅ Removed URL: {url}")
    
    def remove_url_by_index(self, index):
        """Удалить URL по индексу"""
        try:
            index = int(index) - 1
            if 0 <= index < len(self.published_urls):
                url = self.published_urls.pop(index)
                self.save_published_urls()
                print(f"✅ Removed URL: {url}")
            else:
                print(f"❌ Invalid index: {index + 1}")
        except ValueError:
            print("❌ Invalid index format")
    
    def search_urls(self, query):
        """Поиск URL по ключевым словам"""
        if not query:
            print("❌ Please provide a search query")
            return
        
        query = query.lower()
        found_urls = []
        
        for url in self.published_urls:
            if query in url.lower():
                found_urls.append(url)
        
        if found_urls:
            print(f"🔍 Found {len(found_urls)} URLs matching '{query}':")
            print("-" * 80)
            for i, url in enumerate(found_urls, 1):
                print(f"{i:3d}. {url}")
            print("-" * 80)
        else:
            print(f"🔍 No URLs found matching '{query}'")
    
    def clear_all_urls(self):
        """Очистить все опубликованные URL"""
        if not self.published_urls:
            print("📭 No URLs to clear")
            return
        
        confirm = input(f"⚠️  Are you sure you want to clear all {len(self.published_urls)} URLs? (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            self.published_urls.clear()
            self.save_published_urls()
            print("✅ All URLs cleared")
        else:
            print("❌ Operation cancelled")
    
    def export_urls(self, filename=None):
        """Экспорт списка URL в файл"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sciencedaily_urls_export_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"ScienceDaily Published URLs Export\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Total URLs: {len(self.published_urls)}\n")
                f.write("-" * 80 + "\n\n")
                
                for i, url in enumerate(self.published_urls, 1):
                    f.write(f"{i:3d}. {url}\n")
            
            print(f"✅ Exported {len(self.published_urls)} URLs to: {filename}")
        except Exception as e:
            print(f"❌ Error exporting URLs: {e}")
    
    def import_urls(self, filename):
        """Импорт списка URL из файла"""
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            imported_urls = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Извлекаем URL из строки (формат: "1. https://...")
                    if '. ' in line:
                        url = line.split('. ', 1)[1]
                    else:
                        url = line
                    
                    if url.startswith('http'):
                        imported_urls.append(url)
            
            if imported_urls:
                self.published_urls.extend(imported_urls)
                # Убираем дубликаты
                self.published_urls = list(dict.fromkeys(self.published_urls))
                self.save_published_urls()
                print(f"✅ Imported {len(imported_urls)} URLs from: {filename}")
            else:
                print("⚠️  No valid URLs found in file")
                
        except Exception as e:
            print(f"❌ Error importing URLs: {e}")
    
    def show_stats(self):
        """Показать статистику"""
        total_urls = len(self.published_urls)
        
        if os.path.exists(self.published_urls_file):
            file_size = os.path.getsize(self.published_urls_file)
            file_size_kb = file_size / 1024
            last_modified = datetime.fromtimestamp(os.path.getmtime(self.published_urls_file))
        else:
            file_size_kb = 0
            last_modified = None
        
        print("📊 ScienceDaily URL Manager Statistics")
        print("-" * 50)
        print(f"Total published URLs: {total_urls}")
        print(f"File size: {file_size_kb:.1f} KB")
        if last_modified:
            print(f"Last modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
    
    def show_help(self):
        """Показать справку"""
        print("🔧 ScienceDaily URL Manager - Help")
        print("=" * 50)
        print("Commands:")
        print("  show                    - Show all published URLs")
        print("  add <url>              - Add URL to published list")
        print("  remove <url>           - Remove URL from published list")
        print("  remove-index <number>  - Remove URL by index number")
        print("  search <query>         - Search URLs by keyword")
        print("  clear                  - Clear all URLs (with confirmation)")
        print("  export [filename]      - Export URLs to file")
        print("  import <filename>      - Import URLs from file")
        print("  stats                  - Show statistics")
        print("  help                   - Show this help")
        print("  quit                   - Exit program")
        print("=" * 50)
        print("Examples:")
        print("  add https://www.sciencedaily.com/releases/2025/08/230823123456.htm")
        print("  remove-index 5")
        print("  search 'releases'")
        print("  export my_urls.txt")
        print("  import backup_urls.txt")
    
    def run_interactive(self):
        """Интерактивный режим"""
        print("🔧 ScienceDaily URL Manager")
        print("Type 'help' for available commands, 'quit' to exit")
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif command.lower() == 'help':
                    self.show_help()
                
                elif command.lower() == 'show':
                    self.show_all_urls()
                
                elif command.lower() == 'stats':
                    self.show_stats()
                
                elif command.lower() == 'clear':
                    self.clear_all_urls()
                
                elif command.lower().startswith('add '):
                    url = command[4:].strip()
                    if url:
                        self.add_url(url)
                    else:
                        print("❌ Please provide a URL")
                
                elif command.lower().startswith('remove '):
                    url = command[7:].strip()
                    if url:
                        self.remove_url(url)
                    else:
                        print("❌ Please provide a URL")
                
                elif command.lower().startswith('remove-index '):
                    index = command[13:].strip()
                    if index:
                        self.remove_url_by_index(index)
                    else:
                        print("❌ Please provide an index number")
                
                elif command.lower().startswith('search '):
                    query = command[7:].strip()
                    if query:
                        self.search_urls(query)
                    else:
                        print("❌ Please provide a search query")
                
                elif command.lower().startswith('export'):
                    parts = command.split(' ', 1)
                    filename = parts[1] if len(parts) > 1 else None
                    self.export_urls(filename)
                
                elif command.lower().startswith('import '):
                    filename = command[7:].strip()
                    if filename:
                        self.import_urls(filename)
                    else:
                        print("❌ Please provide a filename")
                
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        # Интерактивный режим
        manager = ScienceDailyURLManager()
        manager.run_interactive()
    else:
        # Командный режим
        command = sys.argv[1].lower()
        manager = ScienceDailyURLManager()
        
        if command == 'show':
            manager.show_all_urls()
        elif command == 'stats':
            manager.show_stats()
        elif command == 'help':
            manager.show_help()
        elif command == 'add' and len(sys.argv) > 2:
            manager.add_url(sys.argv[2])
        elif command == 'remove' and len(sys.argv) > 2:
            manager.remove_url(sys.argv[2])
        elif command == 'search' and len(sys.argv) > 2:
            manager.search_urls(sys.argv[2])
        else:
            print("🔧 ScienceDaily URL Manager")
            print("Usage: python manage_sciencedaily_urls.py [command] [args]")
            print("Commands: show, stats, help, add <url>, remove <url>, search <query>")
            print("For interactive mode, run without arguments")

if __name__ == "__main__":
    main()
