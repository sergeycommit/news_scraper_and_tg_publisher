# TechCrunch Auto Scraper & Telegram Publisher

🤖 Автоматический скрапер статей с TechCrunch с публикацией в Telegram канал

## Описание

Этот проект автоматически:
1. Скрапит RSS ленту TechCrunch
2. Выбирает самую интересную статью с помощью AI (Gemini через OpenRouter)
3. Скрапит полное содержимое выбранной статьи
4. Извлекает и скачивает главное изображение статьи
5. Создает виральный пост для Telegram с помощью AI
6. Публикует пост с изображением в указанный Telegram канал

## Особенности

- 🖼️ **Автоматическое извлечение изображений** - находит и скачивает главное изображение статьи
- 🤖 **AI-выбор контента** - использует Gemini для выбора самой интересной статьи
- ✍️ **AI-генерация постов** - создает виральные посты с эмодзи и хештегами
- 📱 **Оптимизация для Telegram** - посты адаптированы для мобильного просмотра
- 📊 **Подробное логирование** - все этапы процесса записываются в лог
- 💾 **Архивирование** - каждая статья сохраняется в JSON с метаданными
- 🔄 **Защита от дублирования** - автоматически отслеживает уже опубликованные статьи
- 🛠️ **Управление URL** - утилита для просмотра и управления списком опубликованных статей

## Требования

- Python 3.8+
- OpenRouter API ключ
- Telegram Bot Token
- Telegram канал для публикации

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd news_scraper_for_tg
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

# TechCrunch RSS Feed
TECHCRUNCH_RSS_URL=https://techcrunch.com/feed/

# AI Model Configuration
AI_MODEL=google/gemini-pro
MAX_TOKENS=4000
TEMPERATURE=0.7
```

## Использование

### Ручной запуск
```bash
python run_scraper.py
```

### Автоматический запуск (cron)

Добавьте в crontab для запуска раз в день в 9:00:
```bash
0 9 * * * cd /path/to/news_scraper_for_tg && python run_scraper.py
```

Или используйте systemd timer (Linux):

1. Создайте файл `/etc/systemd/system/techcrunch-scraper.service`:
```ini
[Unit]
Description=TechCrunch Scraper
After=network.target

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/path/to/news_scraper_for_tg
ExecStart=/usr/bin/python3 run_scraper.py
Environment=PATH=/usr/bin:/usr/local/bin
```

2. Создайте файл `/etc/systemd/system/techcrunch-scraper.timer`:
```ini
[Unit]
Description=Run TechCrunch Scraper daily
Requires=techcrunch-scraper.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

3. Активируйте таймер:
```bash
sudo systemctl enable techcrunch-scraper.timer
sudo systemctl start techcrunch-scraper.timer
```

## Защита от дублирования

Скрипт автоматически отслеживает уже опубликованные статьи, чтобы избежать дублирования контента. Система работает следующим образом:

- 📝 **Автоматическое отслеживание** - каждый опубликованный URL сохраняется в `published_urls.json`
- 🔍 **Фильтрация** - при каждом запуске исключаются уже опубликованные статьи
- 💾 **Персистентность** - список сохраняется между запусками
- 🛡️ **Надежность** - даже при ошибках URL добавляется в список только после успешной публикации

### Управление списком опубликованных URL

Используйте утилиту `manage_published_urls.py` для управления списком:

```bash
# Показать все опубликованные URL
python manage_published_urls.py list

# Показать количество опубликованных URL
python manage_published_urls.py count

# Очистить весь список (с подтверждением)
python manage_published_urls.py clear

# Добавить URL в список
python manage_published_urls.py add "https://techcrunch.com/article/123"

# Удалить URL из списка
python manage_published_urls.py remove "https://techcrunch.com/article/123"

# Найти URL содержащие ключевое слово
python manage_published_urls.py search "ai"

# Показать справку
python manage_published_urls.py help
```

## Структура проекта

```
news_scraper_for_tg/
├── techcrunch_scraper.py    # Основной скрипт скрапера
├── run_scraper.py          # Скрипт запуска
├── manage_published_urls.py # Утилита управления URL
├── test_image_extraction.py # Тест извлечения изображений
├── setup_scheduler.py      # Настройка автозапуска
├── cleanup_archive.py      # Управление архивом статей
├── requirements.txt        # Зависимости Python
├── config.env.example      # Пример конфигурации
├── .env                    # Ваша конфигурация (создать)
├── .gitignore             # Исключения для git
├── scraper.log            # Логи работы (создается автоматически)
├── published_urls.json    # Список опубликованных URL (создается автоматически)
├── articles_archive/      # Папка с архивом статей (создается автоматически)
│   └── article_*.json     # JSON файлы с данными статей
└── QUICK_START.md         # Быстрый старт
```

## Логирование

Скрипт ведет подробные логи в файл `scraper.log` и выводит их в консоль. Логи включают:
- Процесс скрапинга RSS
- Фильтрацию уже опубликованных статей
- Выбор статьи AI
- Скрапинг контента
- Создание поста
- Публикацию в Telegram
- Добавление URL в список опубликованных

## Архив статей

Каждая обработанная статья сохраняется в JSON файл в папке `articles_archive/` с метаданными:
- Временная метка
- Информация о статье (заголовок, ссылка, автор)
- Созданный пост
- URL изображения (если найдено)
- Статус публикации

Файлы именуются по шаблону: `article_YYYYMMDD_HHMMSS.json`

### Управление архивом

Используйте скрипт `cleanup_archive.py` для управления архивом:

```bash
python cleanup_archive.py
```

Возможности:
- 📊 Просмотр статистики архива
- 🗑️ Удаление старых файлов (1, 7, 30 дней)
- 📁 Анализ размера и количества файлов

## Настройка AI

Вы можете настроить параметры AI в файле `.env`:

- `AI_MODEL`: Модель для использования (по умолчанию: google/gemini-pro)
- `MAX_TOKENS`: Максимальное количество токенов для ответа
- `TEMPERATURE`: Креативность ответов (0.0 - 1.0)

## Устранение неполадок

### Ошибка "No articles found"
- Проверьте доступность RSS ленты TechCrunch
- Проверьте интернет-соединение

### Ошибка "All articles have already been published"
- Это нормально, если все статьи из RSS уже были опубликованы
- Подождите следующего обновления RSS ленты
- Или очистите список опубликованных URL: `python manage_published_urls.py clear`

### Ошибка "OpenRouter API"
- Проверьте правильность API ключа
- Убедитесь, что у вас есть кредиты на OpenRouter

### Ошибка "Telegram"
- Проверьте токен бота
- Убедитесь, что бот добавлен в канал как администратор
- Проверьте правильность ID канала

### Ошибка "Article content"
- Некоторые статьи могут быть недоступны для скрапинга
- Проверьте логи для деталей

## Безопасность

- Никогда не коммитьте файл `.env` в git
- Используйте сильные API ключи
- Ограничьте права доступа к серверу
- Файл `published_urls.json` автоматически исключен из git

## Лицензия

MIT License

## Поддержка

При возникновении проблем:
1. Проверьте логи в `scraper.log`
2. Убедитесь в правильности конфигурации
3. Проверьте доступность всех сервисов
4. Используйте утилиту управления URL для диагностики