import asyncio
from playwright.async_api import async_playwright
import os
import json
import logging
import urllib.parse
from collections import Counter

# ========== 设置日志 ==========
log_dir = os.path.join(os.getcwd(), "tmp/good-monitor")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "ArcTeryx_Sportinglife.logo")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

log = logging.getLogger()
log.info("日志系统初始化完成")

# ========== 配置参数 ==========
URL = "https://www.sportinglife.ca/en-CA/arcteryx/sale/?prefn1=gender&prefv1=Men%27s"
CSS_SELECTOR = ".product-tile-name"
DATA_FILE = os.path.join(log_dir, "arcteryx_sportinglife_titles.json")


# ========== Playwright 抓取商品标题 ==========
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

        log.info(f"访问页面: {URL}")
        await page.goto(URL, wait_until="networkidle")

        # SportingLife 的商品是动态渲染的，必须等待 DOM
        await page.wait_for_selector(CSS_SELECTOR, timeout=15000)

        titles = await page.eval_on_selector_all(
            CSS_SELECTOR,
            "nodes => nodes.map(n => n.innerText.trim())"
        )

        await browser.close()
        log.info(f"获取到 {len(titles)} 个商品标题")
        return titles


def fetch_titles():
    return asyncio.run(fetch_titles_async())


# ========== 文件读写 ==========
def save_titles_to_file(titles):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(titles, f, ensure_ascii=False, indent=2)
    log.info(f"商品标题已保存到文件: {DATA_FILE}")


def load_titles_from_file():
    if not os.path.exists(DATA_FILE):
        log.warning("商品标题文件不存在，返回空列表")
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        titles = json.load(f)
    log.info(f"从文件加载商品标题，共 {len(titles)} 项")
    return titles


# ========== Bark 推送通知 ==========
def send_notice(content_list, title):
    if not content_list:
        return

    safe_list = [t.replace("/", "／") for t in content_list]

    content = "\n".join(safe_list)
    content_encoded = urllib.parse.quote(content)
    title_encoded = urllib.parse.quote(title)

    bark_host = os.getenv("BARK_HOST")
    bark_key = os.getenv("BARK_KEY")

    url = (
        f"https://{bark_host}/{bark_key}/"
        f"{title_encoded}/{content_encoded}?group=Product monitor"
    )

    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        log.info(f"推送结果: {response.text}")
    except Exception as e:
        log.error(f"推送失败: {e}")


# ========== 主监控逻辑 ==========
def monitor():
    log.info("=== 开始一次商品监控 ===")
    current_titles = fetch_titles()
    previous_titles = load_titles_from_file()

    curr = Counter(current_titles)
    prev = Counter(previous_titles)

    # 新增商品（计数增加）
    new_items = []
    for item in curr:
        if curr[item] > prev[item]:
            diff = curr[item] - prev[item]
            new_items.extend([item] * diff)

    # 下架商品（计数减少）
    old_items = []
    for item in prev:
        if prev[item] > curr[item]:
            diff = prev[item] - curr[item]
            old_items.extend([item] * diff)

    if new_items:
        log.info(f"发现新品: {new_items}")
        send_notice(new_items, "SportingLife 上新 Arc'teryx 了")

    if old_items:
        log.info(f"下架商品: {old_items}")
        send_notice(old_items, "SportingLife 下架 Arc'teryx 了")

    save_titles_to_file(current_titles)


# ========== 主程序入口 ==========
if __name__ == "__main__":
    monitor()
