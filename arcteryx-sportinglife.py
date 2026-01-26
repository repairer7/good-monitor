import requests
from bs4 import BeautifulSoup
import os
import json
import logging
import urllib.parse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
    # 对内容和标题进行 URL 编码
    content_encoded = urllib.parse.quote(content)
    title_encoded = urllib.parse.quote(title)
    
    # 构造 URL
    url = f"https://bark.imtsui.com/wjZcttgVejaMMHZRGyDmLm/{title_encoded}/{content_encoded}?group=Product monitor"
    
    # === 关键修改 1: 设置 Session 和 重试策略 ===
    # 建立一个 Session 对象，比直接用 requests.get 更稳定
    session = requests.Session()
    
    # 设置重试机制：
    # total=3: 最多重试3次
    # backoff_factor=1: 每次重试间隔时间增加 (0s, 2s, 4s...)
    # status_forcelist: 遇到这些状态码也重试
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    
    # 将重试策略挂载到 https 和 http 协议上
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    
    # === 关键修改 2: 伪装 User-Agent ===
    # 很多服务器会拦截默认的 "python-requests/x.x.x" 标识
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # === 关键修改 3: 增加 timeout ===
        # timeout=10 表示如果 10 秒内服务器没响应就报错（配合重试机制使用）
        response = session.get(url, headers=headers, timeout=10)
        
        # 检查响应状态码，如果是 4xx 或 5xx 会抛出异常
        response.raise_for_status() 
        
        log.info(f"推送结果: {response.text}")
        
    except requests.exceptions.RequestException as e:
        # 捕获所有请求相关的异常（连接错误、超时、DNS错误等）
        log.error(f"推送失败，已达到最大重试次数。错误信息: {e}")

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
