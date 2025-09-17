import asyncio
from datetime import datetime

from robotreport_scraper import RobotReportScraper
from arstechnica_scraper import ArsTechnicaScraper
from techxplore_scraper import TechxploreScraper
from theverge_scraper import TheVergeAIScraper
from zdnet_scraper import ZDNetScraper
from wired_scraper import WiredRobotsScraper
from sciencedaily_scraper import ScienceDailyScraper


async def run_all_scrapers():
    """Запуск всех скраперов последовательно"""
    print("🚀 Starting all scrapers...")

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
    #
    # # 4. ScienceDaily RSS Scraper
    # print("\n🔬 Starting ScienceDaily RSS scraper...")
    # sciencedaily_scraper = ScienceDailyScraper()
    # sciencedaily_result = await sciencedaily_scraper.run_daily_scraping()
    #
    # if sciencedaily_result:
    #     print(f"✅ ScienceDaily: Published article: {sciencedaily_result['title']}")
    #     return
    # else:
    #     print("ℹ️ ScienceDaily: No new articles to publish")
    
    # 5. The Verge AI Scraper
    print("\n📰 Starting The Verge AI scraper...")
    verge_scraper = TheVergeAIScraper()
    verge_result = await verge_scraper.run_daily_scraping()
    
    if verge_result:
        print(f"✅ The Verge: Published article: {verge_result['title']}")
        return
    else:
        print("ℹ️ The Verge: No new articles to publish")
    
    # 6. ZDNet Scraper
    print("\n🔬 Starting ZDNet scraper...")
    zdnet_scraper = ZDNetScraper()
    zdnet_result = await zdnet_scraper.run_daily_scraping()
    
    if zdnet_result:
        print(f"✅ ZDNet: Published article: {zdnet_result['title']}")
    else:
        print("ℹ️ ZDNet: No new articles to publish")


if __name__ == "__main__":
    asyncio.run(run_all_scrapers())