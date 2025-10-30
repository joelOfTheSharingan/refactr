import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def get_page_content(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        html = await page.content()
        await browser.close()
        return html

def analyze_website(url):
    html = asyncio.run(get_page_content(url))
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    num_scripts = len(soup.find_all("script"))
    num_images = len(soup.find_all("img"))

    return {
        "url": url,
        "title": title,
        "script_count": num_scripts,
        "image_count": num_images,
        "summary": f"Found {num_scripts} scripts and {num_images} images on the page."
    }
