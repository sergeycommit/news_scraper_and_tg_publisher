# News Scraper & Telegram Publisher

🤖 Автоматические скраперы статей с публикацией в Telegram канал

## Описание

Этот проект содержит два автоматических скрапера:

### 1. TechCrunch Scraper
- Скрапит RSS ленту TechCrunch
- Выбирает самую интересную статью с помощью AI
- Извлекает изображения и создает виральные посты

### 2. IEEE Spectrum Scraper ⭐ **НОВЫЙ**
- Скрапит статьи с IEEE Spectrum по темам AI и Robotics
- Извлекает медиафайлы (изображения и видео)
- Создает виральные посты с прикрепленными файлами

## Особенности

- 🎯 **Фильтрация по темам** - IEEE скрапер работает только с AI и Robotics
- 🖼️ **Автоматическое извлечение медиа** - изображения и видео
- 🤖 **AI-выбор контента** - использует Gemini для выбора лучших статей
- ✍️ **AI-генерация постов** - создает виральные посты с эмодзи
- 📱 **Оптимизация для Telegram** - посты адаптированы для мобильного просмотра
- 🎨 **Правильное форматирование** - автоматическая конвертация Markdown в HTML
- 📊 **Подробное логирование** - все этапы процесса записываются в лог
- 💾 **Архивирование** - каждая статья сохраняется в JSON с метаданными
- 🔄 **Защита от дублирования** - автоматически отслеживает уже опубликованные статьи
- 🛠️ **Управление URL** - утилиты для просмотра и управления списками

## Быстрый старт

### TechCrunch Scraper
```bash
# Запуск
python run_scraper.py

# Управление URL
python manage_published_urls.py help
```

### IEEE Spectrum Scraper
```bash
# Запуск
python run_ieee_scraper.py

# Управление URL
python manage_ieee_urls.py help
```

Подробные инструкции:
- [QUICK_START.md](QUICK_START.md) - для TechCrunch
- [QUICK_START_IEEE.md](QUICK_START_IEEE.md) - для IEEE Spectrum

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
```

## Использование

### Ручной запуск

**TechCrunch:**
```bash
python run_scraper.py
```

**IEEE Spectrum:**
```bash
python run_ieee_scraper.py
```

### Автоматический запуск (cron)

**TechCrunch (каждый день в 9:00):**
```bash
0 9 * * * cd /path/to/news_scraper_and_tg_publisher && python run_scraper.py
```

**IEEE Spectrum (каждый день в 10:00):**
```bash
0 10 * * * cd /path/to/news_scraper_and_tg_publisher && python run_ieee_scraper.py
```

## Защита от дублирования

Оба скрапера автоматически отслеживают уже опубликованные статьи:

- 📝 **Автоматическое отслеживание** - каждый опубликованный URL сохраняется в JSON файл
- 🔍 **Фильтрация** - при каждом запуске исключаются уже опубликованные статьи
- 💾 **Персистентность** - списки сохраняются между запусками
- 🛡️ **Надежность** - URL добавляется только после успешной публикации

### Управление списками URL

**TechCrunch:**
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
├── techcrunch_scraper.py    # TechCrunch скрапер
├── run_scraper.py          # Запуск TechCrunch
├── manage_published_urls.py # Управление TechCrunch URL
├── ieee_spectrum_scraper.py # IEEE Spectrum скрапер ⭐
├── run_ieee_scraper.py     # Запуск IEEE Spectrum ⭐
├── manage_ieee_urls.py     # Управление IEEE URL ⭐
├── requirements.txt        # Зависимости Python
├── config.env.example      # Пример конфигурации
├── .env                    # Ваша конфигурация (создать)
├── .gitignore             # Исключения для git
├── scraper.log            # Логи TechCrunch
├── ieee_scraper.log       # Логи IEEE Spectrum ⭐
├── published_urls.json    # Список TechCrunch URL
├── ieee_published_urls.json # Список IEEE URL ⭐
├── articles_archive/      # Архив TechCrunch статей
├── ieee_articles_archive/ # Архив IEEE статей ⭐
├── QUICK_START.md         # Быстрый старт TechCrunch
├── QUICK_START_IEEE.md    # Быстрый старт IEEE ⭐
├── README_IEEE.md         # Документация IEEE ⭐
└── README.md              # Этот файл
```

## Логирование

Каждый скрапер ведет отдельные логи:

- **TechCrunch:** `scraper.log`
- **IEEE Spectrum:** `ieee_scraper.log`

Логи включают:
- Процесс скрапинга статей
- Фильтрацию уже опубликованных статей
- Выбор статьи AI
- Скрапинг контента и медиафайлов
- Создание поста
- Публикацию в Telegram
- Добавление URL в список опубликованных

## Архив статей

Каждая обработанная статья сохраняется в JSON файл:

- **TechCrunch:** `articles_archive/article_YYYYMMDD_HHMMSS.json`
- **IEEE Spectrum:** `ieee_articles_archive/ieee_article_YYYYMMDD_HHMMSS.json`

Метаданные включают:
- Временная метка
- Информация о статье (заголовок, ссылка, автор, тема)
- Созданный пост
- URL медиафайла (если найдено)
- Статус публикации

## Настройка AI

Вы можете настроить параметры AI в файле `.env`:

- `AI_MODEL`: Модель для использования (по умолчанию: google/gemini-pro)
- `MAX_TOKENS`: Максимальное количество токенов для ответа
- `TEMPERATURE`: Креативность ответов (0.0 - 1.0)

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