from playwright.sync_api import sync_playwright

PAGE_URL = "https://outlet.arcteryx.com/ca/zh/c/mens/shell-jackets"

# Config for main.py
NAME = "Arc'teryx Official"
DATA_FILE_NAME = "arcteryx_official_titles.json"
NOTICE_PREFIX = "官网"
BRAND = "Arc'teryx"

def fetch_titles():
    titles = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[{NAME}] 打开页面: {PAGE_URL}")
        page.goto(PAGE_URL, wait_until="load", timeout=45000)

        print(f"[{NAME}] 等待首屏商品渲染…")
        page.wait_for_selector(".product-tile-name", timeout=45000)

        print(f"[{NAME}] 开始自动滚动加载所有商品…")
        previous_height = None
        while True:
            current_height = page.evaluate("document.body.scrollHeight")
            if previous_height == current_height:
                break
            previous_height = current_height
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)

        titles = page.eval_on_selector_all(
            ".product-tile-name",
            "els => els.map(e => e.innerText.trim())"
        )
        browser.close()

    print(f"[{NAME}] 抓取到 {len(titles)} 个商品名称")
    return titles
