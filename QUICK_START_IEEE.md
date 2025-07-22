# 🚀 Быстрый старт IEEE Spectrum Scraper

## Шаг 1: Настройка окружения

1. **Создайте файл `.env`:**
```bash
cp config.env.example .env
```

2. **Заполните `.env` файл:**
```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel_username_here

# AI Model Configuration
AI_MODEL=google/gemini-pro
MAX_TOKENS=4000
TEMPERATURE=0.7
```

## Шаг 2: Получение API ключей

### OpenRouter API
1. Зарегистрируйтесь на [OpenRouter](https://openrouter.ai/)
2. Получите API ключ в разделе API Keys
3. Добавьте ключ в `.env` файл

### Telegram Bot
1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Получите токен бота
3. Добавьте бота администратором в ваш канал
4. Укажите токен и ID канала в `.env` файле

## Шаг 3: Тестирование

### Проверка конфигурации
```bash
python manage_ieee_urls.py count
```

### Запуск скрапера
```bash
python run_ieee_scraper.py
```

## Шаг 4: Автоматизация

### Cron (Linux/Mac)
```bash
# Добавьте в crontab для запуска каждый день в 9:00
0 9 * * * cd /path/to/news_scraper_and_tg_publisher && python run_ieee_scraper.py
```

### Systemd (Linux)
1. Создайте файл `/etc/systemd/system/ieee-scraper.service`:
```ini
[Unit]
Description=IEEE Spectrum Scraper
After=network.target

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/path/to/news_scraper_and_tg_publisher
ExecStart=/usr/bin/python3 run_ieee_scraper.py
Environment=PATH=/usr/bin:/usr/local/bin
```

2. Создайте файл `/etc/systemd/system/ieee-scraper.timer`:
```ini
[Unit]
Description=Run IEEE Spectrum Scraper daily
Requires=ieee-scraper.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

3. Активируйте таймер:
```bash
sudo systemctl enable ieee-scraper.timer
sudo systemctl start ieee-scraper.timer
```

## Управление опубликованными URL

```bash
# Показать все опубликованные URL
python manage_ieee_urls.py list

# Очистить список (если нужно начать заново)
python manage_ieee_urls.py clear

# Поиск конкретных URL
python manage_ieee_urls.py search "ai"
```

## Логи

Проверьте логи в файле `ieee_scraper.log` для диагностики проблем.

## Что делает скрапер

1. 🎯 Скрапит статьи с IEEE Spectrum по темам AI и Robotics
2. 🤖 Выбирает самую интересную статью с помощью AI
3. 📄 Скрапит полное содержимое статьи
4. 🖼️ Извлекает и скачивает медиафайлы (изображения/видео)
5. ✍️ Создает виральный пост для Telegram
6. 📱 Публикует пост с медиафайлом в канал
7. 🔄 Отслеживает опубликованные URL для избежания дублирования

## Структура файлов

```
├── ieee_spectrum_scraper.py  # Основной скрипт
├── run_ieee_scraper.py      # Скрипт запуска
├── manage_ieee_urls.py      # Управление URL
├── ieee_scraper.log         # Логи
├── ieee_published_urls.json # Список опубликованных URL
├── ieee_articles_archive/   # Архив статей
└── README_IEEE.md          # Подробная документация
```

## Поддержка

При проблемах:
1. Проверьте логи в `ieee_scraper.log`
2. Убедитесь в правильности API ключей
3. Проверьте доступность сайта IEEE Spectrum
4. Используйте `python manage_ieee_urls.py help` для справки 