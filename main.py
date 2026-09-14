import os
import json
import urllib.parse
from collections import Counter
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import traceback

import Mammut
import arcteryx_offical
import arcteryx_sportinglife

DATA_DIR = os.path.join(os.getcwd(), "good-monitor")

def setup_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def save_titles_to_file(filename, titles):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(titles, f, ensure_ascii=False, indent=2)
    print(f"商品标题已保存到文件: {path}")

def load_titles_from_file(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"商品标题文件不存在，返回空列表: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        titles = json.load(f)
    print(f"从文件加载商品标题，共 {len(titles)} 项")
    return titles

def send_notice(content, title):
    if not content:
        return

    # Bark 路径中不能有原生斜杠，替换为全角
    content = content.replace("/", "／")

    content_encoded = urllib.parse.quote(content)
    title_encoded = urllib.parse.quote(title)

    bark_host = os.getenv("BARK_HOST")
    bark_key = os.getenv("BARK_KEY")

    if not bark_host or not bark_key:
        print("未配置 BARK_HOST 或 BARK_KEY，跳过 Bark 推送。")
        print(f"【模拟推送】标题: {title}")
        print(f"【模拟推送】正文:\n{content}")
        return

    url = (
        f"https://{bark_host}/{bark_key}/"
        f"{title_encoded}/{content_encoded}?group=Product monitor"
    )

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"推送结果: {response.text}")
    except Exception as e:
        print(f"推送失败: {e}")

def run_monitor_task(module):
    name = getattr(module, 'NAME', module.__name__)
    print(f"\n=== 开始监控: {name} ===")
    
    try:
        current_titles = module.fetch_titles()
    except Exception as e:
        print(f"[{name}] 抓取失败: {e}")
        traceback.print_exc()
        # 发生异常时直接跳过，不发送通知
        return None

    data_file_name = module.DATA_FILE_NAME
    # 使用 配置中的 前缀 和 品牌名 拼接作为商家的标识
    merchant_prefix = f"{module.NOTICE_PREFIX} {module.BRAND}"

    previous_titles = load_titles_from_file(data_file_name)

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

    updates = []
    if new_items:
        print(f"发现新品: {new_items}")
        updates.append(f"{merchant_prefix} 上架了\n" + "\n".join(new_items))
    if old_items:
        print(f"下架商品: {old_items}")
        updates.append(f"{merchant_prefix} 下架了\n" + "\n".join(old_items))

    save_titles_to_file(data_file_name, current_titles)
    print(f"=== 完成监控: {name} ===")

    if updates:
        # 如果同一个商家既有上架又有下架，两者之间空一行
        return "\n\n".join(updates)
    return None

def main():
    setup_data_dir()
    
    tasks = [
        Mammut,
        arcteryx_offical,
        arcteryx_sportinglife
    ]

    all_updates = []
    for task in tasks:
        result = run_monitor_task(task)
        if result:
            all_updates.append(result)
            
    if all_updates:
        # 所有商家的更新汇总，每个商家之间空一行
        final_content = "\n\n".join(all_updates)
        send_notice(final_content, "商品有更新")

if __name__ == "__main__":
    main()
