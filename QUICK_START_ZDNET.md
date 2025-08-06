# ZDNet Scraper - Быстрый старт

Этот скраппер автоматически собирает статьи с ZDNet и публикует их в Telegram канал с помощью AI.

## 🚀 Быстрый запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Скопируйте файл конфигурации:
```bash
cp config.env.example config.env
```

Отредактируйте `config.env`:
```env
# OpenRouter API (для AI)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=google/gemini-pro
MAX_TOKENS=4000
TEMPERATURE=0.7

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=@your_channel_username

# Опционально: кастомный промпт для AI
PROMPT=Create a viral social media post about this tech article...
```

### 3. Запуск скраппера

```bash
python run_zdnet_scraper.py
```

## 📁 Структура файлов

- `zdnet_scraper.py` - Основной скраппер
- `run_zdnet_scraper.py` - Файл запуска
- `manage_zdnet_urls.py` - Управление опубликованными URL
- `zdnet_articles_archive/` - Архив статей в JSON
- `zdnet_published_urls.json` - Список опубликованных URL
- `zdnet_scraper.log` - Лог файл

## 🔧 Управление URL

### Показать все опубликованные URL:
```bash
python manage_zdnet_urls.py show
```

### Добавить URL в список опубликованных:
```bash
python manage_zdnet_urls.py add "https://www.zdnet.com/article/example"
```

### Удалить URL:
```bash
python manage_zdnet_urls.py remove "https://www.zdnet.com/article/example"
# или по индексу
python manage_zdnet_urls.py remove 1
```

### Очистить все URL:
```bash
python manage_zdnet_urls.py clear
```

### Поиск URL:
```bash
python manage_zdnet_urls.py search "ai"
```

### Статистика:
```bash
python manage_zdnet_urls.py stats
```

## 📊 Что делает скраппер

1. **Скрапит статьи** с разделов ZDNet:
   - Artificial Intelligence
   - Tech
   - Innovation

2. **Фильтрует статьи** по дате (не старше 2 дней от текущей даты)

3. **Проверяет** не публиковались ли уже

4. **Выбирает лучшую статью** для публикации

5. **Извлекает контент** и медиа из статьи

6. **Создает вирусный пост** с помощью AI

7. **Публикует в Telegram** с изображением

8. **Сохраняет данные** в JSON архив

## 🎯 Особенности

- ✅ Автоматическая фильтрация по дате (не старше 2 дней)
- ✅ Предотвращение дублирования публикаций
- ✅ AI-генерация вирусных постов
- ✅ Извлечение и публикация медиа
- ✅ Сохранение архива статей
- ✅ Подробное логирование
- ✅ Управление URL через CLI

## 🔍 Логирование

Все действия записываются в `zdnet_scraper.log`:
- Информация о найденных статьях
- Ошибки скрапинга
- Статус публикации
- Очистка временных файлов

## 📝 Примеры использования

### Запуск в фоновом режиме:
```bash
nohup python run_zdnet_scraper.py > zdnet_output.log 2>&1 &
```

### Проверка логов:
```bash
tail -f zdnet_scraper.log
```

### Просмотр архива статей:
```bash
ls -la zdnet_articles_archive/
```

## 🛠️ Устранение неполадок

### Ошибка "No articles found"
- Проверьте интернет соединение
- Убедитесь, что сайт ZDNet доступен
- Проверьте заголовки запросов в коде

### Ошибка Telegram API
- Проверьте токен бота
- Убедитесь, что бот добавлен в канал
- Проверьте права бота на отправку сообщений

### Ошибка OpenRouter API
- Проверьте API ключ
- Убедитесь в наличии средств на балансе
- Проверьте лимиты запросов

## 📈 Мониторинг

### Проверка статуса:
```bash
# Количество опубликованных URL
python manage_zdnet_urls.py stats

# Последние логи
tail -20 zdnet_scraper.log
```

### Автоматический запуск (cron):
```bash
# Добавить в crontab для запуска каждый час
0 * * * * cd /path/to/project && python run_zdnet_scraper.py
```

## 🔄 Обновления

Для обновления скраппера:
1. Сохраните резервную копию конфигурации
2. Обновите код
3. Проверьте совместимость с новыми версиями библиотек

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `zdnet_scraper.log`
2. Убедитесь в правильности конфигурации
3. Проверьте доступность внешних сервисов
4. Обратитесь к документации библиотек 