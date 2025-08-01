#!/usr/bin/env python3
"""
ZDNet Scraper Runner
Запуск скрапера ZDNet
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zdnet_scraper import run_with_proper_cleanup

if __name__ == "__main__":
    print("🚀 Запуск ZDNet Scraper...")
    run_with_proper_cleanup() 