import requests
import time
import os
import logging
from playwright.sync_api import sync_playwright

# ========== 设置日志 ==========
log_dir = os.path.join(os.getcwd(), "tmp/good-monitor")  # 使用绝对路径更安全
os.makedirs(log_dir, exist_ok=True)         # 如果目录不存在则创建
log_path = os.path.join(log_dir, "arcteryx-offical.logo")

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

# ========== 推送通知 ==========
def send_notice_new(content):
    token = "d25f816e481b40aaaa239e0eb551aa1e"  # 你的 PushPlus Token
    title = "官网上新Arc'teryx了"
    push_url = f"http://www.pushplus.plus/send?token={token}&title={title}&content={content}&template=html"
    response = requests.get(push_url)
    log.info(f"推送结果: {response.text}")

def send_notice_old(content):
    token = "d25f816e481b40aaaa239e0eb551aa1e"  # 你的 PushPlus Token
    title = "官网下架Arc'teryx了"
    push_url = f"http://www.pushplus.plus/send?token={token}&title={title}&content={content}&template=html"
    response = requests.get(push_url)
    log.info(f"推送结果: {response.text}")
# ========== 循环监控 ==========
def monitor(keyword: str, page_url: str):
    log.info("=== 获取初始商品标题（基准） ===")
    base_url = get_target_url(keyword, page_url)
    if not base_url:
        log.warning("未捕获到初始 URL，退出监控")
        return

    titles_first = fetch_analytics_names(base_url)

    while True:
        log.info("等待 30 分钟后进行检查...")
        time.sleep(1800)

        log.info("=== 重新获取 target_url ===")
        new_url = get_target_url(keyword, page_url)
        if not new_url:
            log.warning("未捕获到新的 URL，本轮跳过")
            continue

        log.info("=== 检查商品标题 ===")
        titles_check = fetch_analytics_names(new_url)

        new_items = [t for t in titles_check if t not in titles_first]
        old_items = [t for t in titles_first if t not in titles_check]
        if new_items:
            log.info(f"发现新品: {new_items}")
            send_notice_new(new_items)
            titles_first = titles_check
        elif old_items:
            log.info(f"下架商品: {old_items}")
            send_notice_old(old_items)
            titles_first = titles_check        
        else:
            log.info("暂无更新，继续监控...")

# ========== 主程序入口 ==========
if __name__ == "__main__":
    keyword = "dxpapi"
    page_url = "https://outlet.arcteryx.com/ca/zh/c/mens/shell-jackets"
    monitor(keyword, page_url)