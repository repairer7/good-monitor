import requests
from bs4 import BeautifulSoup
import time
import os
import logging
# ========== 设置日志 ==========
log_dir = os.path.join(os.getcwd(), "tmp/good-monitor")  # 使用绝对路径更安全
os.makedirs(log_dir, exist_ok=True)         # 如果目录不存在则创建
log_path = os.path.join(log_dir, "Mammut.logo")

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


URL = "https://www.thelasthunt.com/search?query=mammut%20men"
CSS_SELECTOR = "h3.chakra-text.css-z3x98r"


def fetch_titles():
    """抓取商品标题列表"""
    log.info(f"正在请求 {URL} ...")
    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    titles = [el.get_text(strip=True) for el in soup.select(CSS_SELECTOR)]
    log.info(f"获取到 {len(titles)} 个商品标题")
    return titles


def monitor():
        log.info("\n=== 第一次获取商品标题（基准） ===")
        titles_first = fetch_titles()

        while True:
            log.info("\n等待 30 分钟后进行检查...")
            time.sleep(1800)  # 等待 30 分钟
            log.info("\n=== 检查商品标题 ===")
            titles_check = fetch_titles()
            new_items = [t for t in titles_check if t not in titles_first]
            old_items = [t for t in titles_first if t not in titles_check]
            if new_items:
                def send_notice(content):
                    token = "d25f816e481b40aaaa239e0eb551aa1e"
                    title = "Thelasthunt上新Mammut了"
                    url = f"http://www.pushplus.plus/send?token={token}&title={title}&content={content}&template=html"
                    response = requests.request("GET", url)
                    log.info(response.text)
                send_notice(new_items)
                titles_first = titles_check
            elif old_items:
                def send_notice(content):
                    token = "d25f816e481b40aaaa239e0eb551aa1e"
                    title = "Thelasthunt下架Mammut了"
                    url = f"http://www.pushplus.plus/send?token={token}&title={title}&content={content}&template=html"
                    response = requests.request("GET", url)
                    log.info(response.text)
                send_notice(old_items)
                titles_first = titles_check          
            else:
                log.info("暂无更新，继续监控...")


if __name__ == "__main__":
    monitor()
