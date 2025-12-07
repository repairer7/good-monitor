import requests
import os
import json
import logging
import urllib.parse
from playwright.sync_api import sync_playwright

# ========== 设置日志 ==========
log_dir = os.path.join(os.getcwd(), "tmp/good-monitor")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "ArcTeryx-Offical.logo")

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
KEYWORD = "dxpapi"
PAGE_URL = "https://outlet.arcteryx.com/ca/zh/c/mens/shell-jackets"
DATA_FILE = os.path.join(log_dir, "arcteryx_official_titles.json")

# ========== 获取页面加载过程中的目标 API URL ==========
def get_target_url(keyword: str, page_url: str) -> str:
    target = [None]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        def handle_request(request):
            if keyword in request.url and target[0] is None:
                target[0] = request.url
                log.info(f"捕获到目标 URL: {target[0]}")

        context.on("request", handle_request)
        page = context.new_page()
        page.goto(page_url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        browser.close()
    return target[0]

# ========== 从 API 获取 analytics_name 字段 ==========
def fetch_analytics_names(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    analytics_names = []
    docs = data.get("response", {}).get("docs", [])
    for item in docs:
        if "analytics_name" in item:
            analytics_names.append(item["analytics_name"])

    log.info(f"获取到 {len(analytics_names)} 个商品标题")
    return analytics_names

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
    content = "\n".join(content_list)
    # 对内容和标题进行 URL 编码，避免中文或特殊字符报错
    content_encoded = urllib.parse.quote(content)
    title_encoded = urllib.parse.quote(title)
    bark_url = f"https://bark.imtsui.com/wjZcttgVejaMMHZRGyDmLm/{title_encoded}/{content_encoded}"
    response = requests.get(bark_url)
    log.info(f"推送结果: {response.text}")

# ========== 主监控逻辑 ==========
def monitor():
    log.info("=== 开始一次商品监控 ===")
    target_url = get_target_url(KEYWORD, PAGE_URL)
    if not target_url:
        log.warning("未捕获到目标 URL，退出本次监控")
        return

    current_titles = fetch_analytics_names(target_url)
    previous_titles = load_titles_from_file()

    new_items = [t for t in current_titles if t not in previous_titles]
    old_items = [t for t in previous_titles if t not in current_titles]

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
