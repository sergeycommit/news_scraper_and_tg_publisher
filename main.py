import asyncio
from datetime import datetime

from robotreport_scraper import RobotReportScraper
from arstechnica_scraper import ArsTechnicaScraper
from techxplore_scraper import TechxploreScraper
from theverge_scraper import TheVergeAIScraper
from zdnet_scraper import ZDNetScraper
from wired_scraper import WiredRobotsScraper
from sciencedaily_scraper import ScienceDailyScraper
from article_selector import ArticleSelector


async def run_all_scrapers_with_llm_selection():
    """Запуск скраперов с использованием LLM для выбора лучшей статьи"""
    print("🚀 Starting intelligent article scraping with LLM selection...")
    
    # Инициализируем все скраперы
    scrapers = []
    
    # 1. The Robot Report Scraper (AI/Cognition) - только по четным числам
    current_day = datetime.now().day
    if current_day % 2 == 0:
        print(f"\n🤖 Initializing The Robot Report scraper... (Day {current_day} is even)")
        scrapers.append(RobotReportScraper())
    else:
        print(f"\n⏭️ The Robot Report: Skipped (Day {current_day} is odd, only runs on even days)")
    
    # 2. Ars Technica Scraper
    print("\n📰 Initializing Ars Technica scraper...")
    scrapers.append(ArsTechnicaScraper())
    
    # 3. Techxplore Scraper
    print("\n🔬 Initializing Techxplore scraper...")
    scrapers.append(TechxploreScraper())
    
    # 4. Wired Robots Scraper
    print("\n🤖 Initializing Wired Robots scraper...")
    scrapers.append(WiredRobotsScraper())
    
    # 5. The Verge AI Scraper
    print("\n📰 Initializing The Verge AI scraper...")
    scrapers.append(TheVergeAIScraper())
    
    # 6. ZDNet Scraper
    print("\n🔬 Initializing ZDNet scraper...")
    scrapers.append(ZDNetScraper())
    
    # ScienceDaily закомментирован
    # print("\n🔬 Initializing ScienceDaily scraper...")
    # scrapers.append(ScienceDailyScraper())
    
    # Инициализируем селектор статей
    print("\n🤖 Initializing Article Selector with LLM...")
    selector = ArticleSelector()
    
    # Собираем статьи со всех источников и выбираем лучшую
    print("\n📊 Collecting articles from all sources...")
    best_article = await selector.get_best_article(scrapers)
    
    if not best_article:
        print("❌ No suitable article found from any source")
        return None
    
    print(f"\n✅ Best article selected by LLM:")
    print(f"   Source: {best_article['source']}")
    print(f"   Title: {best_article['title']}")
    print(f"   URL: {best_article['url']}")
    print(f"   Date: {best_article['date']}")
    
    # Получаем скрапер для выбранной статьи
    scraper = best_article['scraper']
    
    # Теперь скрапим полное содержимое выбранной статьи
    print(f"\n📄 Scraping full content of selected article...")
    
    # Скрапим содержимое статьи и медиа
    if hasattr(scraper, 'scrape_article_content_and_media'):
        article_data = scraper.scrape_article_content_and_media(best_article['url'])
        
        if not article_data.get('content'):
            print("❌ Failed to scrape article content")
            return None
        
        if len(article_data['content']) < 100:
            print("⚠️ Article content too short, skipping")
            return None
        
        print(f"✅ Successfully scraped {len(article_data['content'])} characters")
        
        # Публикуем статью через Telegram Publisher
        print(f"\n📤 Publishing article to Telegram...")
        
        result = await scraper.telegram_publisher.create_and_publish_post(
            title=best_article['title'],
            content=article_data['content'],
            article_url=best_article['url'],
            topic=best_article.get('topic', 'Tech'),
            media_url=article_data.get('media_url'),
            media_type=article_data.get('media_type', 'image')
        )
        
        if result['success']:
            # Сохраняем данные и добавляем URL в опубликованные
            scraper.add_published_url(best_article['url'])
            scraper.save_article_data(best_article, result['post_content'], result.get('media_url'))
            print("✅ Article published successfully!")
            return best_article
        else:
            print(f"❌ Failed to publish article: {result.get('error')}")
            return None
    else:
        print(f"❌ Scraper {best_article['source']} doesn't support content scraping")
        return None


async def run_all_scrapers_legacy():
    """Старый метод запуска скраперов последовательно (для совместимости)"""
    print("🚀 Starting all scrapers (legacy mode)...")

    # 0. The Robot Report Scraper (AI/Cognition) - FIRST PRIORITY (только по четным числам)
    current_day = datetime.now().day
    if current_day % 2 == 0:
        print(f"\n🤖 Exploring The Robot Report for AI/Cognition articles... (Day {current_day} is even)")
        robotreport_scraper = RobotReportScraper()
        robotreport_result = await robotreport_scraper.run_daily_scraping()

        if robotreport_result:
            print(f"✅ The Robot Report: Published article: {robotreport_result['title']}")
            return
        else:
            print("ℹ️ The Robot Report: No new articles to publish")
    else:
        print(f"\n⏭️ The Robot Report: Skipped (Day {current_day} is odd, only runs on even days)")

    # 1. Ars Technica Scraper
    print("\nExploring Ars Technica for new articles...")
    arstechnica_scraper = ArsTechnicaScraper()
    arstechnica_result = await arstechnica_scraper.run_daily_scraping()

    if arstechnica_result:
        print(f"✅ Ars Technica: Published article: {arstechnica_result['title']}")
        return
    else:
        print("ℹ️ Ars Technica: No new articles to publish")

    # 2. Techxplore Scraper
    print("\nExploring Techxplore for new articles...")
    techxplore_scraper = TechxploreScraper()
    techxplore_result = await techxplore_scraper.run_daily_scraping()
    
    if techxplore_result:
        print(f"✅ Techxplore: Published article: {techxplore_result['title']}")
        return
    else:
        print("ℹ️ Techxplore: No new articles to publish")

    # 3. Wired Robots Scraper
    print("\n🤖 Starting Wired Robots scraper...")
    wired_scraper = WiredRobotsScraper()
    wired_result = await wired_scraper.run_daily_scraping()
    
    if wired_result:
        print(f"✅ Wired: Published article: {wired_result['title']}")
        return
    else:
        print("ℹ️ Wired: No new articles to publish")
    
    # 4. The Verge AI Scraper
    print("\n📰 Starting The Verge AI scraper...")
    verge_scraper = TheVergeAIScraper()
    verge_result = await verge_scraper.run_daily_scraping()
    
    if verge_result:
        print(f"✅ The Verge: Published article: {verge_result['title']}")
        return
    else:
        print("ℹ️ The Verge: No new articles to publish")
    
    # 5. ZDNet Scraper
    print("\n🔬 Starting ZDNet scraper...")
    zdnet_scraper = ZDNetScraper()
    zdnet_result = await zdnet_scraper.run_daily_scraping()
    
    if zdnet_result:
        print(f"✅ ZDNet: Published article: {zdnet_result['title']}")
    else:
        print("ℹ️ ZDNet: No new articles to publish")


if __name__ == "__main__":
    # По умолчанию используем новый метод с LLM-селектором
    # Для использования старого метода замените на: asyncio.run(run_all_scrapers_legacy())
    asyncio.run(run_all_scrapers_with_llm_selection())
