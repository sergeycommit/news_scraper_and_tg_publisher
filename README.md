# ZDNet Scraper & Telegram Publisher

🤖 Автоматический скрапер статей ZDNet с публикацией в Telegram канал

## Описание

Этот проект содержит автоматический скрапер ZDNet:

### ZDNet Scraper ⭐ **ОСНОВНОЙ СКРАПЕР**
- Скрапит статьи с ZDNet по темам AI и Robotics
- Автоматически выбирает лучшие статьи с помощью AI
- Извлекает высококачественные изображения
- Создает виральные посты на русском языке
- Публикует в Telegram канал с медиафайлами

## Особенности

### ZDNet Scraper ⭐ **ОСНОВНОЙ**
- 🧠 **ИИ-анализ контента** - использует AI для выбора лучших статей
- 📊 **Множественные темы** - анализирует AI и Robotics разделы
- 🎯 **Умная фильтрация** - исключает служебные страницы и дубликаты
- 🤖 **AI-генерация постов** - создает виральные посты на русском языке
- 📱 **Оптимизация для Telegram** - посты адаптированы для мобильного просмотра
- 🖼️ **Высококачественные изображения** - автоматически выбирает лучшие медиафайлы
- 🎨 **Правильное форматирование** - автоматическая конвертация Markdown в HTML
- 📊 **Подробное логирование** - все этапы процесса записываются в лог
- 💾 **Архивирование** - каждая статья сохраняется в JSON с метаданными
- 🔄 **Защита от дублирования** - автоматически отслеживает уже опубликованные статьи
- 🛠️ **Управление URL** - утилиты для просмотра и управления списками

## Быстрый старт

### ZDNet Scraper ⭐ **ОСНОВНОЙ**
```bash
# Запуск скрапера
python run_zdnet_scraper.py

# Управление URL
python manage_zdnet_urls.py help
```

Подробные инструкции:
- [QUICK_START_ZDNET.md](QUICK_START_ZDNET.md) - для ZDNet

## Требования

- Python 3.8+
- OpenRouter API ключ
- Telegram Bot Token
- Telegram канал для публикации

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd news_scraper_and_tg_publisher
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `config.env.example`:
```bash
cp config.env.example .env
```

4. Настройте переменные окружения в файле `.env`:

### Получение OpenRouter API ключа
1. Зарегистрируйтесь на [OpenRouter](https://openrouter.ai/)
2. Получите API ключ в разделе API Keys
3. Добавьте ключ в `.env` файл

### Настройка Telegram бота
1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Получите токен бота
3. Добавьте бота администратором в ваш канал
4. Укажите токен и ID канала в `.env` файле

## Конфигурация

Отредактируйте файл `.env`:

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

# RSS Feeds for AI Article Selection
# The scraper will automatically use multiple TechCrunch RSS feeds
# to find the best AI-related articles
```

## Использование

### Ручной запуск

**AI TechCrunch (ИИ-скрапер):**
```bash
python run_ai_scraper.py
```

**TechCrunch:**
```bash
python run_scraper.py
```

**IEEE Spectrum:**
```bash
python run_ieee_scraper.py
```

### Автоматический запуск (cron)

**AI TechCrunch (каждый день в 8:00):**
```bash
0 8 * * * cd /path/to/news_scraper_and_tg_publisher && python run_ai_scraper.py
```

**TechCrunch (каждый день в 9:00):**
```bash
0 9 * * * cd /path/to/news_scraper_and_tg_publisher && python run_scraper.py
```

**IEEE Spectrum (каждый день в 10:00):**
```bash
0 10 * * * cd /path/to/news_scraper_and_tg_publisher && python run_ieee_scraper.py
```

## Защита от дублирования

Все скраперы автоматически отслеживают уже опубликованные статьи:

- 📝 **Автоматическое отслеживание** - каждый опубликованный URL сохраняется в JSON файл
- 🔍 **Фильтрация** - при каждом запуске исключаются уже опубликованные статьи
- 💾 **Персистентность** - списки сохраняются между запусками
- 🛡️ **Надежность** - URL добавляется только после успешной публикации

### Управление списками URL

**AI TechCrunch & TechCrunch:**
```bash
python manage_published_urls.py list
python manage_published_urls.py clear
```

**IEEE Spectrum:**
```bash
python manage_ieee_urls.py list
python manage_ieee_urls.py clear
```

## Структура проекта

```
news_scraper_and_tg_publisher/
├── techcrunch_scraper.py    # AI TechCrunch скрапер ⭐
├── run_ai_scraper.py       # Запуск AI TechCrunch ⭐
├── run_scraper.py          # Запуск обычного TechCrunch
├── manage_published_urls.py # Управление TechCrunch URL
├── ieee_spectrum_scraper.py # IEEE Spectrum скрапер
├── run_ieee_scraper.py     # Запуск IEEE Spectrum
├── manage_ieee_urls.py     # Управление IEEE URL
├── requirements.txt        # Зависимости Python
├── config.env.example      # Пример конфигурации
├── .env                    # Ваша конфигурация (создать)
├── .gitignore             # Исключения для git
├── scraper.log            # Логи TechCrunch
├── ieee_scraper.log       # Логи IEEE Spectrum
├── published_urls.json    # Список TechCrunch URL
├── ieee_published_urls.json # Список IEEE URL
├── articles_archive/      # Архив TechCrunch статей
├── ieee_articles_archive/ # Архив IEEE статей
├── QUICK_START.md         # Быстрый старт TechCrunch
├── QUICK_START_IEEE.md    # Быстрый старт IEEE
├── README_IEEE.md         # Документация IEEE
└── README.md              # Этот файл
```

## Логирование

Каждый скрапер ведет отдельные логи:

- **AI TechCrunch:** `scraper.log`
- **IEEE Spectrum:** `ieee_scraper.log`

Логи включают:
- Процесс скрапинга статей
- Фильтрацию уже опубликованных статей
- ИИ-выбор статьи
- Скрапинг контента и медиафайлов
- Создание поста
- Публикацию в Telegram
- Добавление URL в список опубликованных

## Архив статей

Каждая обработанная статья сохраняется в JSON файл:

- **AI TechCrunch:** `articles_archive/ai_article_YYYYMMDD_HHMMSS.json`
- **TechCrunch:** `articles_archive/article_YYYYMMDD_HHMMSS.json`
- **IEEE Spectrum:** `ieee_articles_archive/ieee_article_YYYYMMDD_HHMMSS.json`

Метаданные включают:
- Временная метка
- Информация о статье (заголовок, ссылка, автор, тема)
- Созданный пост
- URL медиафайла (если найдено)
- Статус публикации
- Флаг ИИ-выбора (для AI TechCrunch)

## Настройка AI

Вы можете настроить параметры AI в файле `.env`:

- `AI_MODEL`: Модель для использования (по умолчанию: google/gemini-pro)
- `MAX_TOKENS`: Максимальное количество токенов для ответа
- `TEMPERATURE`: Креативность ответов (0.0 - 1.0)

## RSS ленты для AI TechCrunch

ИИ-скрапер автоматически анализирует следующие RSS ленты TechCrunch:

1. **Основная лента** - `https://techcrunch.com/feed/`
2. **ИИ категория** - `https://techcrunch.com/category/artificial-intelligence/feed/`
3. **Startups** - `https://techcrunch.com/category/startups/feed/`
4. **Enterprise** - `https://techcrunch.com/category/enterprise/feed/`
5. **Security** - `https://techcrunch.com/category/security/feed/`
6. **Fintech** - `https://techcrunch.com/category/fintech/feed/`
7. **Transportation** - `https://techcrunch.com/category/transportation/feed/`

## Устранение неполадок

### Общие проблемы

**Ошибка "No articles found"**
- Проверьте доступность сайтов
- Проверьте интернет-соединение
- Возможно, изменилась структура сайта

**Ошибка "All articles have already been published"**
- Это нормально, если все статьи уже были опубликованы
- Подождите следующего обновления сайта
- Или очистите список опубликованных URL

**Ошибка "No suitable AI article found" (AI TechCrunch)**
- ИИ не нашел подходящих статей об ИИ
- Это может быть временным явлением
- Попробуйте запустить позже

**Ошибка "OpenRouter API"**
- Проверьте правильность API ключа
- Убедитесь, что у вас есть кредиты на OpenRouter

**Ошибка "Telegram"**
- Проверьте токен бота
- Убедитесь, что бот добавлен в канал как администратор
- Проверьте правильность ID канала

### Специфичные проблемы

**IEEE Spectrum - "Media download"**
- Некоторые медиафайлы могут быть недоступны
- Скрипт продолжит работу без медиафайла

## Безопасность

- Никогда не коммитьте файл `.env` в git
- Используйте сильные API ключи
- Ограничьте права доступа к серверу
- Файлы с URL автоматически исключены из git

## Лицензия

MIT License

## Поддержка

При возникновении проблем:
1. Проверьте соответствующие логи (`scraper.log` или `ieee_scraper.log`)
2. Убедитесь в правильности конфигурации
3. Проверьте доступность всех сервисов
4. Используйте утилиты управления URL для диагностики

## Документация

- [README_IEEE.md](README_IEEE.md) - Подробная документация IEEE Spectrum скрапера
- [QUICK_START.md](QUICK_START.md) - Быстрый старт TechCrunch
- [QUICK_START_IEEE.md](QUICK_START_IEEE.md) - Быстрый старт IEEE Spectrum