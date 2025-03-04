from playwright.async_api import async_playwright 
import asyncio
from bs4 import BeautifulSoup
import re
import numpy as np

class DogProductsScraper:
    def __init__(self, max_tabs: int):
        self.sem =  asyncio.Semaphore(max_tabs)

    async def scrape_products_from_category(self, context, category_link):
        async with self.sem:
            page = await context.new_page()  
            await page.goto(category_link)
            next_page_number = 2
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            html = await page.content() 
            soup = BeautifulSoup(html, "html.parser")
            page_container = soup.select_one(".pagination")   
            if page_container is None:
                max_page_number = 0 
            else:
                a_tags = page_container.find_all("a")
                if len(a_tags) > 1:
                    max_page_number = int(a_tags[-2].text)
                else:
                    max_page_number = 0
            print(max_page_number)
            all_page_product_urls = []
            while True:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                product_urls = [c.find_all("a")[-1]["href"] for c in soup.select(".product-image")]
                all_page_product_urls.extend(product_urls)
                if next_page_number > max_page_number:
                    break
                page_container = page.locator(".pagination")
                next_page = page_container.locator(f"text={next_page_number}").nth(0)
                page_number = await next_page.text_content()
                page_number = int(re.findall(r"\d+", page_number)[0])
                await next_page.click() 
                next_page_number += 1
            await page.close()
            return all_page_product_urls


    async def run_scraper(self):
        async with async_playwright() as playwright:
            chromium = playwright.chromium
            browser = await chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page() 
            await page.goto("https://www.absolutepets.com/shop/category/dog")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            category_links = [c.find("a")["href"] for c in soup.select(".category-item")]
            all_product_urls = []
            for category_link in category_links: 
                 product_urls = await self.scrape_products_from_category(context, category_link)
                 all_product_urls.extend(product_urls)
            product_urls = list(set(all_product_urls))


                




asyncio.run(DogProductsScraper(max_tabs=10).run_scraper())