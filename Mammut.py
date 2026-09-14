import requests
from bs4 import BeautifulSoup

URL = "https://www.thelasthunt.com/search?query=mammut%20men"
CSS_SELECTOR = "h3.css-eiojhb"

# Config for main.py
NAME = "TheLastHunt Mammut"
DATA_FILE_NAME = "mammut_titles.json"
NOTICE_PREFIX = "TheLastHunt"
BRAND = "Mammut"

def fetch_titles():
    print(f"[{NAME}] 正在请求页面: {URL}")
    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    titles = [el.get_text(strip=True) for el in soup.select(CSS_SELECTOR)]
    print(f"[{NAME}] 获取到 {len(titles)} 个商品标题")
    return titles
