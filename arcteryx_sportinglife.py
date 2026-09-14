import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

URL = "https://www.sportinglife.ca/en-CA/arcteryx/sale/?prefn1=gender&prefv1=Men%27s"
CSS_SELECTOR = ".product-name"

# Config for main.py
NAME = "SportingLife Arc'teryx"
DATA_FILE_NAME = "arcteryx_sportinglife_titles.json"
NOTICE_PREFIX = "SportingLife"
BRAND = "Arc'teryx"

async def fetch_titles_async():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        await stealth_async(page)

        print(f"[{NAME}] 访问页面: {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=30000)

        await page.wait_for_selector(CSS_SELECTOR, timeout=15000)

        titles = await page.eval_on_selector_all(
            CSS_SELECTOR,
            "nodes => nodes.map(n => n.innerText.trim())"
        )

        await browser.close()
        print(f"[{NAME}] 获取到 {len(titles)} 个商品标题")
        return titles

def fetch_titles():
    return asyncio.run(fetch_titles_async())
