# 🚀 Быстрый старт TechCrunch Scraper

## ✨ Новые возможности
- 🖼️ **Автоматическое извлечение изображений** из статей
- 📱 **Публикация с картинками** в Telegram
- 🤖 **Улучшенные AI-промпты** для создания постов

## 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 2. Настройка конфигурации
```bash
# Скопируйте пример конфигурации
cp config.env.example .env

# Отредактируйте .env файл и добавьте ваши ключи:
# - OPENROUTER_API_KEY (получите на openrouter.ai)
# - TELEGRAM_BOT_TOKEN (создайте через @BotFather)
# - TELEGRAM_CHANNEL_ID (ID вашего канала)
```

## 3. Тестовый запуск
```bash
python run_scraper.py
```

## 4. Настройка автоматического запуска (Windows)
```bash
python setup_scheduler.py
```

## 5. Проверка работы
- Проверьте логи в `scraper.log`
- Посмотрите архив статей в папке `articles_archive/`
- Проверьте публикацию в Telegram канале (с изображениями!)

## 🔧 Получение ключей

### OpenRouter API Key
1. Зайдите на [openrouter.ai](https://openrouter.ai/)
2. Зарегистрируйтесь и получите API ключ
3. Добавьте в `.env`: `OPENROUTER_API_KEY=ваш_ключ`

### Telegram Bot
1. Напишите [@BotFather](https://t.me/botfather)
2. Создайте бота: `/newbot`
3. Получите токен и добавьте в `.env`: `TELEGRAM_BOT_TOKEN=ваш_токен`
4. Добавьте бота в канал как администратора
5. Добавьте ID канала в `.env`: `TELEGRAM_CHANNEL_ID=@ваш_канал`

## 📝 Пример .env файла
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
TELEGRAM_CHANNEL_ID=@your_channel
```

## 🖼️ Работа с изображениями

Скрипт автоматически:
- Извлекает главное изображение статьи из meta-тегов или HTML
- Скачивает изображение во временный файл
- Прикрепляет к посту в Telegram
- Удаляет временный файл после публикации

Поддерживаемые форматы: JPG, PNG, GIF, WebP

## ❗ Важно
- Никогда не коммитьте `.env` файл в git
- Убедитесь, что бот добавлен в канал как администратор
- Проверьте наличие кредитов на OpenRouter
- Для работы с изображениями нужен стабильный интернет 