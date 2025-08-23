# News Scrapers & Telegram Publisher

🤖 Автоматические скраперы новостей с публикацией в Telegram канал

## Описание

Этот проект содержит автоматические скраперы для нескольких новостных сайтов:

### The Verge AI Scraper 📰
- Скрапит статьи с The Verge по теме AI и искусственного интеллекта
- Фильтрует статьи не старше 2 дней от текущей даты
- Автоматически выбирает лучшие статьи с помощью AI
- Извлекает высококачественные изображения
- Создает виральные посты на русском языке
- Публикует в Telegram канал с медиафайлами

### ZDNet Scraper 🔬
- Скрапит статьи с ZDNet по темам AI и Robotics
- Фильтрует статьи не старше 2 дней от текущей даты
- Автоматически выбирает лучшие статьи с помощью AI
- Извлекает высококачественные изображения
- Создает виральные посты на русском языке
- Публикует в Telegram канал с медиафайлами

### Wired Robots Scraper 🤖
- Скрапит статьи с Wired по теме роботов и автоматизации
- Фильтрует статьи не старше 2 дней от текущей даты
- Автоматически выбирает лучшие статьи с помощью AI
- Извлекает высококачественные изображения
- Создает виральные посты на русском языке
- Публикует в Telegram канал с медиафайлами

## Особенности

### Общие возможности для всех скраперов
- 🧠 **ИИ-анализ контента** - использует AI для выбора лучших статей
- 📅 **Фильтрация по дате** - показывает только статьи не старше 2 дней
- 🎯 **Умная фильтрация** - исключает служебные страницы и дубликаты
- 🤖 **AI-генерация постов** - создает виральные посты на русском языке
- 📱 **Оптимизация для Telegram** - посты адаптированы для мобильного просмотра
- 🖼️ **Высококачественные изображения** - автоматически выбирает лучшие медиафайлы
- 🎨 **Правильное форматирование** - автоматическая конвертация Markdown в HTML
- 📊 **Подробное логирование** - все этапы процесса записываются в лог
- 💾 **Архивирование** - каждая статья сохраняется в JSON с метаданными
- 🔄 **Защита от дублирования** - автоматически отслеживает уже опубликованные статьи
- 🛠️ **Управление URL** - утилиты для просмотра и управления списками

### The Verge AI Scraper 📰
- 🧠 **AI-тематика** - специализируется на статьях об искусственном интеллекте
- 📊 **Технологические новости** - охватывает последние достижения в AI

### ZDNet Scraper 🔬
- 📊 **Множественные темы** - анализирует AI и Robotics разделы
- 🔬 **Технические статьи** - фокус на технических аспектах технологий

### Wired Robots Scraper 🤖
- 🤖 **Робототехника** - специализируется на статьях о роботах и автоматизации
- 🚀 **Инновации** - охватывает последние достижения в робототехнике

## Быстрый старт

### Запуск всех скраперов
```bash
# Запуск всех скраперов одновременно
python main.py
```

### Запуск отдельных скраперов
```bash
# The Verge AI Scraper
python run_theverge_scraper.py

# ZDNet Scraper
python run_zdnet_scraper.py

# Wired Robots Scraper
python run_wired_scraper.py

# ScienceDaily RSS Scraper
python run_sciencedaily_scraper.py

# ScienceDaily Summary Scraper
python run_sciencedaily_summary.py
```

### Управление URL-ами
```bash
# The Verge URL management
python manage_theverge_urls.py help

# ZDNet URL management
python manage_zdnet_urls.py help

# Wired URL management
python manage_wired_urls.py help

# ScienceDaily URL management
python manage_sciencedaily_urls.py help

# ScienceDaily Summary URL management
python manage_sciencedaily_summary_urls.py help
```

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
├── main.py                    # Основной скрипт для запуска всех скраперов
├── theverge_scraper.py        # The Verge AI скрапер
├── run_theverge_scraper.py    # Запуск The Verge
├── manage_theverge_urls.py    # Управление The Verge URL
├── zdnet_scraper.py           # ZDNet скрапер
├── run_zdnet_scraper.py       # Запуск ZDNet
├── manage_zdnet_urls.py       # Управление ZDNet URL
├── wired_scraper.py           # Wired Robots скрапер
├── run_wired_scraper.py       # Запуск Wired
├── manage_wired_urls.py       # Управление Wired URL
├── sciencedaily_scraper.py    # ScienceDaily RSS скрапер
├── run_sciencedaily_scraper.py # Запуск ScienceDaily
├── manage_sciencedaily_urls.py # Управление ScienceDaily URL
├── sciencedaily_summary_scraper.py # ScienceDaily Summary скрапер ⭐
├── run_sciencedaily_summary.py    # Запуск ScienceDaily Summary ⭐
├── manage_sciencedaily_summary_urls.py # Управление Summary URL ⭐
├── telegram_publisher.py      # Класс для публикации в Telegram
├── requirements.txt           # Зависимости Python
├── config.env.example         # Пример конфигурации
├── .env                       # Ваша конфигурация (создать)
├── .gitignore                # Исключения для git
├── theverge_articles_archive/ # Архив The Verge статей
├── zdnet_articles_archive/    # Архив ZDNet статей
├── wired_articles_archive/    # Архив Wired статей
├── sciencedaily_articles_archive/ # Архив ScienceDaily статей
├── sciencedaily_summary_archive/  # Архив ScienceDaily Summary ⭐
└── README.md                 # Этот файл
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

## 🔬 ScienceDaily Summary Scraper

Скрапер для [ScienceDaily RSS](https://www.sciencedaily.com/rss/all.xml) - создает краткое резюме всех научных новостей за сегодня.

**Особенности:**
- Скрапинг всех новостей за текущий день
- Создание краткого резюме в одном посте
- Публикация в Telegram с изображением
- Собственный промпт для создания постов (без хэштегов)
- Отслеживание уже опубликованных URL
- Архивирование данных в JSON формате

**Использование:**
```bash
# Запуск модуля
python3 run_sciencedaily_summary.py

# Управление URL
python3 manage_sciencedaily_summary_urls.py help
python3 manage_sciencedaily_summary_urls.py show
python3 manage_sciencedaily_summary_urls.py clear
```
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