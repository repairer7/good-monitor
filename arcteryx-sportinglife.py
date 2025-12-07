import requests
from bs4 import BeautifulSoup
import os
import json
import logging
import urllib.parse

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
CSS_SELECTOR = "span.product-name"
DATA_FILE = os.path.join(log_dir, "arcteryx_sportinglife_titles.json")


# ========== 抓取商品标题 ==========
def fetch_titles():
    log.info(f"正在请求页面: {URL}")
    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    titles = [el.get_text(strip=True) for el in soup.select(CSS_SELECTOR)]
    log.info(f"获取到 {len(titles)} 个商品标题")
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
    content = "\n".join(content_list)
    # 对内容和标题进行 URL 编码，避免中文或特殊字符报错
    content_encoded = urllib.parse.quote(content)
    title_encoded = urllib.parse.quote(title)
    bark_url = f"https://bark.imtsui.com/wjZcttgVejaMMHZRGyDmLm/{title_encoded}/{content_encoded}?group=商品监控"
    response = requests.get(bark_url)
    log.info(f"推送结果: {response.text}")

# ========== 主监控逻辑 ==========
def monitor():
    log.info("=== 开始一次商品监控 ===")
    current_titles = fetch_titles()
    previous_titles = load_titles_from_file()

    new_items = [t for t in current_titles if t not in previous_titles]
    old_items = [t for t in previous_titles if t not in current_titles]

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
