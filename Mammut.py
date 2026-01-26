import requests
from bs4 import BeautifulSoup
import os
import json
import logging

# ========== 设置日志 ==========
log_dir = os.path.join(os.getcwd(), "tmp/good-monitor")
os.makedirs(log_dir, exist_ok=True)
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

# ========== 配置参数 ==========
URL = "https://www.thelasthunt.com/search?query=mammut%20men"
CSS_SELECTOR = "h3.css-eiojhb"
DATA_FILE = os.path.join(log_dir, "mammut_titles.json")

# Bark 的 device_key（替换成你自己的）
BARK_KEY = "你的Bark密钥"

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

    url = "https://bark.imtsui.com/push"
    payload = {
        "title": title,
        "body": content,
        "device_key": BwjZcttgVejaMMHZRGyDmLm,
        "group": "Product monitor"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        log.info(f"推送成功: {response.text}")
    except requests.exceptions.RequestException as e:
        log.error(f"推送失败: {e}")

# ========== 主监控逻辑 ==========
def monitor():
    log.info("=== 开始一次商品监控 ===")
    current_titles = fetch_titles()
    previous_titles = load_titles_from_file()

    new_items = [t for t in current_titles if t not in previous_titles]
    old_items = [t for t in previous_titles if t not in current_titles]

    if new_items:
        log.info(f"发现新品: {new_items}")
        send_notice(new_items, "TheLastHunt 上新 Mammut 了")
    if old_items:
        log.info(f"下架商品: {old_items}")
        send_notice(old_items, "TheLastHunt 下架 Mammut 了")

    save_titles_to_file(current_titles)

# ========== 主程序入口 ==========
if __name__ == "__main__":
    monitor()
