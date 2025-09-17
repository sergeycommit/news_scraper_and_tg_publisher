#!/usr/bin/env python3
"""
Модуль для публикации постов в Telegram
Включает функции составления постов и отправки
"""

import os
import logging
import asyncio
import tempfile
from datetime import datetime
from urllib.parse import urljoin
import requests
from openai import OpenAI
from telegram import Bot
from telegram.error import TelegramError
import re
import yt_dlp

# Настройка логирования
logger = logging.getLogger(__name__)

class TelegramPublisher:
    """Класс для публикации постов в Telegram"""
    
    def __init__(self, telegram_token, telegram_channel, openai_api_key, ai_model="openai/gpt-4o-mini"):
        """
        Инициализация издателя
        
        Args:
            telegram_token (str): Токен Telegram бота
            telegram_channel (str): ID канала для публикации
            openai_api_key (str): API ключ OpenAI/OpenRouter
            ai_model (str): Модель AI для генерации постов
        """
        self.telegram_token = telegram_token
        self.telegram_channel = telegram_channel
        self.ai_model = ai_model
        
        # Инициализация клиентов
        self.telegram_bot = Bot(token=telegram_token)
        self.openai_client = OpenAI(
            api_key=openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Настройки AI
        self.max_tokens = 1000
        
        # Загрузка промптов из переменных окружения
        self.custom_prompt = os.getenv('PROMPT', '')
        self.custom_system_prompt = os.getenv('SYSTEM_PROMPT', '')
        
        logger.info("TelegramPublisher initialized successfully")
    
    async def create_and_publish_post(self, title, content, article_url, topic=None, media_url=None, media_type='image'):
        """
        Основной метод: создает пост из исходного текста и публикует с медиа (изображение или видео)
        
        Args:
            title (str): Заголовок статьи
            content (str): Содержимое статьи
            article_url (str): URL статьи
            topic (str): Тема статьи (опционально)
            media_url (str): URL медиа (изображения или видео) (опционально)
            media_type (str): Тип медиа ('image' или 'video') (по умолчанию 'image')
            
        Returns:
            dict: Результат публикации с информацией о посте
        """
        try:
            logger.info(f"Creating and publishing post for: {title[:50]}...")
            
            # Создаем вирусный пост
            post_content = self.create_viral_post(title, content, article_url, topic, media_url, media_type)
            
            if not post_content or len(post_content.strip()) < 50:
                logger.error("Failed to create viral post - content too short or empty")
                return {
                    'success': False,
                    'error': 'Post creation failed',
                    'post_content': None,
                    'media_path': None
                }
            
            logger.info(f"Created post with {len(post_content)} characters")
            
            # Скачиваем медиа если есть URL
            media_path = None
            if media_url:
                media_path = self.download_media(media_url, media_type)
                if media_path:
                    logger.info(f"Downloaded {media_type}: {media_path}")
                else:
                    logger.warning(f"Failed to download {media_type}")
            
            # Публикуем в Telegram
            success = await self.publish_to_telegram(post_content, media_path, media_type)
            
            result = {
                'success': success,
                'post_content': post_content,
                'media_path': media_path,
                'media_url': media_url
            }
            
            if not success:
                result['error'] = 'Telegram publication failed'
                logger.error("Failed to publish to Telegram")
            else:
                logger.info("✅ Post created and published successfully!")
            
            # Очищаем временные файлы
            if media_path:
                self.cleanup_media(media_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in create_and_publish_post: {e}")
            return {
                'success': False,
                'error': str(e),
                'post_content': None,
                'media_path': None
            }
    
    def create_viral_post(self, title, content, article_url, topic=None, media_url=None, media_type='image'):
        """
        Создание вирусного поста с помощью AI
        
        Args:
            title (str): Заголовок статьи
            content (str): Содержимое статьи
            article_url (str): URL статьи
            topic (str): Тема статьи
            media_url (str): URL медиа (видео или изображение)
            media_type (str): Тип медиа ('video' или 'image')
            
        Returns:
            str: Сгенерированный пост или None в случае ошибки
        """
        try:
            logger.info(f"create_viral_post called with URL: {article_url}")
            
            # Определяем промпт
            if self.custom_prompt:
                # Если в кастомном промпте нет переменных, добавляем информацию о статье
                if '{title}' not in self.custom_prompt and '{content}' not in self.custom_prompt:
                    prompt = f"""
{self.custom_prompt}

ЗАГОЛОВОК: {title}
СОДЕРЖАНИЕ: {content[:1000] + "..." if len(content) > 1000 else content}
ССЫЛКА: {article_url}
ТЕМА: {topic or "Technology"}

ВАЖНО: Перед хештегами обязательно добавь ссылку "Read more" в формате: 🔗 <a href="{article_url}">Read more</a>
"""
                    logger.info("Using custom PROMPT from .env file + article info")
                else:
                    # Подставляем переменные в кастомный промпт
                    try:
                        # Заменяем {media_url} на пустую строку, если он есть в промпте
                        custom_prompt = self.custom_prompt.replace('{media_url}', media_url or "")
                        logger.info(f"Custom prompt after media_url replacement: {custom_prompt[:200]}...")
                        # Заменяем все возможные переменные
                        custom_prompt = custom_prompt.replace('{title}', title)
                        custom_prompt = custom_prompt.replace('{content}', content[:1000] + "..." if len(content) > 1000 else content)
                        custom_prompt = custom_prompt.replace('{url}', article_url)
                        custom_prompt = custom_prompt.replace('{topic}', topic or "Technology")
                        # Заменяем все оставшиеся {media_url} на пустую строку
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        # Заменяем все оставшиеся {media_url} на пустую строку еще раз
                        custom_prompt = custom_prompt.replace('{media_url}', "")
                        prompt = custom_prompt
                        logger.info("Using custom PROMPT from .env file with variable substitution")
                    except Exception as e:
                        logger.warning(f"Variable substitution failed: {e}, using fallback")
                        # Обрабатываем custom_prompt перед использованием в f-string
                        safe_custom_prompt = self.custom_prompt.replace('{media_url}', media_url or "")
                        safe_custom_prompt = safe_custom_prompt.replace('{title}', title)
                        safe_custom_prompt = safe_custom_prompt.replace('{content}', content[:1000] + "..." if len(content) > 1000 else content)
                        safe_custom_prompt = safe_custom_prompt.replace('{url}', article_url)
                        safe_custom_prompt = safe_custom_prompt.replace('{topic}', topic or "Technology")
                        prompt = f"""
{safe_custom_prompt}

ЗАГОЛОВОК: {title}
СОДЕРЖАНИЕ: {content[:1000] + "..." if len(content) > 1000 else content}
ССЫЛКА: {article_url}
ТЕМА: {topic or "Technology"}

ВАЖНО: Перед хештегами обязательно добавь ссылку "Read more" в формате: 🔗 <a href="{article_url}">Read more</a>
"""
            else:
                prompt = f"""
                Создай вирусный пост для Telegram на русском языке на основе этой статьи.
                
                Заголовок: {title}
                Содержание: {content[:1000]}...
                
                Пост должен быть:
                - Интересным и привлекающим внимание
                - Написан на русском языке
                - Содержать эмодзи и форматирование
                - Не длиннее 800 символов
                - Перед хештегами обязательно добавь ссылку "Read more" в формате: 🔗 <a href="{article_url}">Read more</a>
                """
            
            # Определяем системный промпт
            if self.custom_system_prompt:
                system_content = self.custom_system_prompt
                logger.info("Using custom SYSTEM_PROMPT from .env file")
            else:
                system_content = """
                Ты - эксперт по созданию вирусных постов для социальных сетей.
                Твоя задача - создавать увлекательные, информативные и вирусные посты на русском языке.
                Используй эмодзи и форматирование для привлечения внимания.
                Создавай посты не длиннее 800 символов, чтобы они поместились в подпись к изображению в Telegram.
                """
            
            # Генерируем пост
            response = self.openai_client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": system_content + " Создавай посты не длиннее 800 символов, чтобы они поместились в подпись к изображению в Telegram."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=1  # Увеличиваем температуру для более креативных постов
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Убираем прямые URL из поста, если AI их добавил
            if article_url and article_url in post_content:
                post_content = post_content.replace(article_url, "").strip()
                logger.info("Removed direct URL from post content")
            
            # Добавляем ссылку на статью перед хештегами
            if article_url:
                post_content = self.add_link_to_post(post_content, article_url)
                logger.info(f"Added link to post: {article_url}")
            
            logger.info(f"Created viral post for article: {title[:50]}... ({len(post_content)} chars)")
            return post_content
            
        except Exception as e:
            logger.error(f"Error creating viral post: {e}")
            return None
    
    def add_link_to_post(self, post_content, article_url):
        """Добавление ссылки на статью в пост перед хештегами"""
        if not article_url:
            return post_content
        
        # Проверяем, есть ли уже ссылка в посте
        if article_url in post_content:
            return post_content
        
        # Ищем хештеги в посте (строки, содержащие хештеги)
        lines = post_content.split('\n')
        hashtag_lines = []
        other_lines = []
        
        for line in lines:
            # Проверяем, содержит ли строка хештеги (начинается с # или содержит #)
            if line.strip().startswith('#') or ('#' in line and any(word.startswith('#') for word in line.split())):
                hashtag_lines.append(line)
            else:
                other_lines.append(line)
        
        # Если есть хештеги, вставляем ссылку перед ними
        if hashtag_lines:
            # Убираем пустые строки в конце основного контента
            while other_lines and not other_lines[-1].strip():
                other_lines.pop()
            
            # Создаем ссылку с отступами
            link_text = f'🔗 <a href="{article_url}">Read more</a>'
            
            # Собираем пост: основной контент + пустая строка + ссылка + пустая строка + хештеги
            result_lines = other_lines + ['', link_text, ''] + hashtag_lines
            return '\n'.join(result_lines)
        else:
            # Если хештегов нет, добавляем ссылку в конец
            link_text = f'\n\n🔗 <a href="{article_url}">Read more</a>'
            return post_content + link_text
    
    def get_hashtags_for_topic(self, topic):
        """Получение хештегов для темы"""
        hashtags_map = {
            'AI': '#ИИ #искусственныйинтеллект #технологии #AI',
            'Robotics': '#роботы #робототехника #автоматизация #Robotics',
            'Latest': '#новости #технологии #последние #Latest',
            'Technology': '#технологии #инновации #гаджеты #Technology',
            'Science': '#наука #исследования #открытия #Science'
        }
        
        return hashtags_map.get(topic, '#новости #технологии')
    
    def translate_to_russian(self, text):
        """Перевод текста на русский язык"""
        try:
            if len(text) > 1000:
                # Если текст слишком длинный, рефакторим его
                logger.info("Text too long, refactoring...")
                text = text[:800] + "..."
            
            prompt = f"Переведи этот текст на русский язык, сохранив смысл и стиль:\n\n{text}"
            
            response = self.openai_client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "Ты - профессиональный переводчик с английского на русский. Переводи точно, сохраняя стиль и смысл."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            logger.info(f"Translated text to Russian: {len(translated_text)} characters")
            return translated_text
            
        except Exception as e:
            logger.error(f"Error translating to Russian: {e}")
            return text
    
    def download_media(self, media_url, media_type='image'):
        """
        Скачивание медиа файла
        
        Args:
            media_url (str): URL медиа файла
            media_type (str): Тип медиа ('image' или 'video')
            
        Returns:
            str: Путь к скачанному файлу или None в случае ошибки
        """
        try:
            if not media_url:
                return None
            
            # Проверяем, является ли это YouTube видео
            if media_type == 'video' and ('youtube.com' in media_url or 'youtu.be' in media_url):
                return self.download_youtube_video(media_url)
            
            # Определяем расширение файла в зависимости от типа
            if media_type == 'video':
                # Для видео определяем расширение по URL
                if any(ext in media_url.lower() for ext in ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv']):
                    # Если расширение есть в URL, используем его
                    suffix = '.' + media_url.split('.')[-1].split('?')[0]  # Убираем параметры URL
                else:
                    # По умолчанию для видео используем mp4
                    suffix = '.mp4'
            else:
                # Для изображений определяем расширение по URL
                if any(ext in media_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                    suffix = '.' + media_url.split('.')[-1].split('?')[0]  # Убираем параметры URL
                else:
                    # По умолчанию для изображений используем webp
                    suffix = '.webp'
            
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = temp_file.name
            temp_file.close()
            
            # Скачиваем файл
            response = requests.get(media_url, timeout=30)
            response.raise_for_status()
            
            # Сохраняем файл
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded {media_type}: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error downloading {media_type}: {e}")
            return None
    
    def download_youtube_video(self, youtube_url):
        """
        Скачивание YouTube видео с помощью yt-dlp и обрезка до 60 секунд если нужно
        
        Args:
            youtube_url (str): URL YouTube видео
            
        Returns:
            str: Путь к скачанному файлу или None в случае ошибки
        """
        try:
            import os
            
            # Создаем временную директорию
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, 'video.%(ext)s')
            
            # Настройки для yt-dlp
            ydl_opts = {
                'outtmpl': temp_path,  # Шаблон имени файла
                'format': 'best[height<=720]',  # Лучшее качество до 720p
                'quiet': True,  # Тихий режим
                'no_warnings': True,  # Без предупреждений
                'extract_flat': False,  # Полное извлечение
                'writesubtitles': False,  # Без субтитров
                'writeautomaticsub': False,  # Без автоподписей
                'ignoreerrors': False,  # Не игнорировать ошибки
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Получаем информацию о видео
                info = ydl.extract_info(youtube_url, download=False)
                video_title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                
                # Скачиваем видео независимо от длительности
                logger.info(f"Downloading YouTube video: {video_title} ({duration}s)")
                
                # Скачиваем видео
                ydl.download([youtube_url])
                
                # Ищем скачанный файл в временной директории
                downloaded_file = None
                logger.info(f"Looking for downloaded file in directory: {temp_dir}")
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        logger.info(f"Found file {file_path} with size: {file_size} bytes")
                        if file_size > 0:
                            logger.info(f"Downloaded YouTube video: {file_path} ({file_size} bytes)")
                            downloaded_file = file_path
                            break
                        else:
                            logger.warning(f"Downloaded video file is empty: {file_path}")
                            os.remove(file_path)  # Удаляем пустой файл
                
                if not downloaded_file:
                    logger.error("Downloaded video file not found or empty")
                    return None
                
                # Видео скачивается полностью без обрезки
                logger.info(f"Video downloaded successfully: {downloaded_file}")
                
                return downloaded_file
                
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {e}")
            return None
    
    async def publish_to_telegram(self, post_content, media_path=None, media_type='image'):
        """
        Публикация поста в Telegram
        
        Args:
            post_content (str): Текст поста
            media_path (str): Путь к медиа файлу (опционально)
            media_type (str): Тип медиа ('image' или 'video') (по умолчанию 'image')
            
        Returns:
            bool: True если публикация успешна, False в противном случае
        """
        try:
            # Конвертируем в HTML
            html_content = self.convert_markdown_to_html(post_content)
            
            # Ограничиваем длину подписи для Telegram (максимум 1024 символа)
            if len(html_content) > 1024:
                # Обрезаем до 1000 символов и добавляем многоточие
                html_content = html_content[:1000] + "..."
                logger.info("Truncated post content to fit Telegram limits")
            
            if media_path and media_type == 'video' and os.path.exists(media_path):
                # Для видео отправляем текстовое сообщение с прикрепленным видео
                try:
                    with open(media_path, 'rb') as video_file:
                        await self.telegram_bot.send_video(
                            chat_id=self.telegram_channel,
                            video=video_file,
                            caption=html_content,
                            parse_mode='HTML'
                        )
                    logger.info("Published text post with attached video file to Telegram")
                    return True
                except Exception as video_error:
                    logger.warning(f"Failed to send video attachment: {video_error}, trying text only")
                    # Если не удалось отправить с видео, отправляем только текст
                    await self.telegram_bot.send_message(
                        chat_id=self.telegram_channel,
                        text=html_content,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                    logger.info("Published text post to Telegram (fallback)")
                    return True
            elif media_path and os.path.exists(media_path):
                # Отправляем изображение
                try:
                    with open(media_path, 'rb') as photo_file:
                        await self.telegram_bot.send_photo(
                            chat_id=self.telegram_channel,
                            photo=photo_file,
                            caption=html_content,
                            parse_mode='HTML'
                        )
                    logger.info("Published post with image to Telegram")
                    return True
                except Exception as media_error:
                    logger.warning(f"Failed to send with image: {media_error}, trying text only")
                    # Если не удалось отправить с изображением, пробуем только текст
                    await self.telegram_bot.send_message(
                        chat_id=self.telegram_channel,
                        text=html_content,
                        parse_mode='HTML',
                        disable_web_page_preview=False
                    )
                    logger.info("Published text post to Telegram (fallback)")
                    return True
            else:
                # Отправляем только текст
                await self.telegram_bot.send_message(
                    chat_id=self.telegram_channel,
                    text=html_content,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                logger.info("Published text post to Telegram")
                return True
            
        except Exception as e:
            logger.error(f"Error publishing to Telegram: {e}")
            return False
    
    def convert_markdown_to_html(self, text):
        """Конвертация простого Markdown в HTML для Telegram"""
        if not text:
            return ""
        
        # Заменяем **текст** на <b>текст</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Заменяем *текст* на <i>текст</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Заменяем переносы строк на \n (Telegram поддерживает \n)
        text = text.replace('\n', '\n')
        
        return text
    
    def cleanup_media(self, media_path):
        """Очистка временных медиа файлов"""
        if media_path and os.path.exists(media_path):
            try:
                os.unlink(media_path)
                logger.info(f"Cleaned up temporary file: {media_path}")
                return True
            except Exception as e:
                logger.warning(f"Could not delete temporary file: {e}")
                return False
        return True
