import requests
import os
import json
import logging
import urllib.parse
from playwright.sync_api import sync_playwright
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import Counter

# ========== 设置日志 ==========
log_dir = os.path.join(os.getcwd(), "tmp/good-monitor")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "ArcTeryx-Official.log")

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
PAGE_URL = "https://outlet.arcteryx.com/ca/zh/c/mens/shell-jackets"
DATA_FILE = os.path.join(log_dir, "arcteryx_official_titles.json")

# ========== Playwright 抓取商品名称 ==========
def get_titles_by_playwright(page_url: str):
    titles = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        log.info(f"打开页面: {page_url}")
        page.goto(page_url, wait_until="load", timeout=45000)

        # 关键：等待首屏商品真正渲染出来（避免骨架屏）
        log.info("等待首屏商品渲染…")
        page.wait_for_selector(".product-tile-name", timeout=45000)

        # 再开始滚动加载剩余商品
        log.info("开始自动滚动加载所有商品…")
        previous_height = None
        while True:
            current_height = page.evaluate("document.body.scrollHeight")
            if previous_height == current_height:
                break
            previous_height = current_height
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)

        # 抓取所有商品名称
        titles = page.eval_on_selector_all(
            ".product-tile-name",
            "els => els.map(e => e.innerText.trim())"
        )

        browser.close()

    log.info(f"抓取到 {len(titles)} 个商品名称")
    return titles

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

    current_titles = get_titles_by_playwright(PAGE_URL)
    previous_titles = load_titles_from_file()

    curr = Counter(current_titles)
    prev = Counter(previous_titles)

    new_items = []
    for item in curr:
        if curr[item] > prev[item]:
            diff = curr[item] - prev[item]
            new_items.extend([item] * diff)

    old_items = []
    for item in prev:
        if prev[item] > curr[item]:
            diff = prev[item] - curr[item]
            old_items.extend([item] * diff)

    if new_items:
        log.info(f"发现新品: {new_items}")
        send_notice(new_items, "官网上新 Arc'teryx 了")
    if old_items:
        log.info(f"下架商品: {old_items}")
        send_notice(old_items, "官网下架 Arc'teryx 了")

    save_titles_to_file(current_titles)

# ========== 主程序入口 ==========
if __name__ == "__main__":
    monitor()
