#!/usr/bin/env python3
"""
IEEE Spectrum Scraper Runner
Запуск скрапера IEEE Spectrum
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ieee_spectrum_scraper import run_with_proper_cleanup

if __name__ == "__main__":
    print("🚀 Запуск IEEE Spectrum Scraper...")
    run_with_proper_cleanup() 