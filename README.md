# good-monitor# Good Monitor

一个基于 Python、Playwright 和 GitHub Actions 的商品变化监控工具。

项目会抓取指定电商网站的商品名称，将本次结果与上一次保存的商品列表进行比较，并通过 Bark 推送新品上架和商品下架提醒。当前主要用于监控 Mammut 和 Arc'teryx 相关商品。

## 功能特性

- 监控多个电商网站的商品列表
- 自动识别新品上架
- 自动识别商品下架或从列表中消失
- 使用 Bark 推送通知到手机
- 使用本地 JSON 文件保存上一次监控结果
- 使用 GitHub Actions 自动安装依赖并执行监控脚本
- 自动提交商品数据和日志变化到仓库
- 对网络请求配置重试机制，提高监控稳定性
- 支持静态网页和动态渲染网页

## 当前监控来源

| 脚本 | 监控来源 | 监控内容 | 抓取方式 |
| --- | --- | --- | --- |
| `Mammut.py` | TheLastHunt | Mammut 男士商品 | Requests + BeautifulSoup |
| `arcteryx-offical.py` | Arc'teryx 官方 Outlet | 男士 Shell Jackets | Playwright |
| `arcteryx-sportinglife.py` | Sporting Life | 男士 Arc'teryx 折扣商品 | Playwright |

监控页面和 CSS 选择器目前直接写在 Python 脚本中。如网站页面结构发生变化，可能需要同步更新脚本配置。

## 项目结构

```text
.
├── .github/
│   └── workflows/
│       └── monitor.yml                 # GitHub Actions 工作流
├── Mammut.py                           # TheLastHunt Mammut 监控
├── arcteryx-offical.py                 # Arc'teryx 官方 Outlet 监控
├── arcteryx-sportinglife.py            # Sporting Life Arc'teryx 监控
├── requirements.txt                    # Python 依赖
├── README.md                           # 项目说明
└── tmp/
    └── good-monitor/
        ├── mammut_titles.json          # Mammut 历史商品列表
        ├── arcteryx_official_titles.json
        ├── arcteryx_sportinglife_titles.json
        └── *.log                       # 运行日志
```

## 工作原理

每个监控脚本都会执行以下步骤：

1. 访问指定的商品列表页面
2. 提取页面中的商品名称
3. 读取上一次执行时保存的商品名称
4. 对比本次和上次的商品列表
5. 发现新品时发送上新通知
6. 发现商品消失时发送下架通知
7. 保存本次商品列表，供下一次执行使用

项目使用 `Counter` 比较商品标题数量，因此同一个商品标题出现次数发生变化时，也可以被识别为列表变化。

## 使用方法

### 1. Fork 仓库

点击 GitHub 仓库右上角的 **Fork**，将项目复制到自己的 GitHub 账号下。

### 2. 配置 Bark

进入自己的仓库：

```text
Settings → Secrets and variables → Actions → New repository secret
```

添加以下两个 Repository Secrets：

| 名称 | 说明 | 示例 |
| --- | --- | --- |
| `BARK_HOST` | Bark 服务域名 | `api.day.app` |
| `BARK_KEY` | Bark 设备 Key | `xxxxxxxxxxxxxxxx` |

建议只填写 Bark 的域名，不要填写 `https://` 或末尾的 `/`。

不要将 `BARK_KEY` 直接写入 Python 脚本或提交到公开仓库。

### 3. 手动运行监控

进入仓库的 **Actions** 页面，选择：

```text
Website Product Monitor
```

然后点击：

```text
Run workflow
```

当前工作流使用 `workflow_dispatch`，默认只能通过 GitHub Actions 页面手动触发。

### 4. 查看运行结果

每次运行完成后，可以在以下位置查看结果：

- GitHub Actions 日志：查看抓取、对比和推送过程
- `tmp/good-monitor/*.log`：查看脚本运行日志
- `tmp/good-monitor/*_titles.json`：查看最近一次保存的商品列表
- Bark：查看新品和下架提醒

工作流具有 `contents: write` 权限。当商品数据或日志发生变化时，GitHub Actions 会自动提交并推送更新。

## 本地运行

### 环境要求

- Python 3.10 或更高版本
- 可访问目标网站的网络环境
- Bark 设备 Key

### 安装依赖

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install
```

### 配置环境变量

Linux/macOS：

```bash
export BARK_HOST="api.day.app"
export BARK_KEY="your-bark-key"
```

Windows PowerShell：

```powershell
$env:BARK_HOST="api.day.app"
$env:BARK_KEY="your-bark-key"
```

### 执行脚本

```bash
python Mammut.py
python arcteryx-offical.py
python arcteryx-sportinglife.py
```

首次运行时，历史商品数据文件可能不存在，程序会将当前抓取结果作为初始基准。首次运行通常不会产生新品或下架通知；从第二次运行开始，程序才会基于历史数据识别变化。

## Bark 通知

通知使用以下分组：

```text
Product monitor
```

不同监控来源使用不同通知标题：

- `TheLastHunt 上新 Mammut 了`
- `TheLastHunt 下架 Mammut 了`
- `官网上新 Arc'teryx 了`
- `官网下架 Arc'teryx 了`
- `SportingLife 上新 Arc'teryx 了`
- `SportingLife 下架 Arc'teryx 了`

通知正文为发生变化的商品名称，每个商品占一行。

## 修改监控目标

如果需要监控其他商品或页面，通常需要修改对应脚本中的以下配置：

```python
URL = "商品列表页面地址"
CSS_SELECTOR = "商品标题对应的 CSS 选择器"
DATA_FILE = "历史数据保存路径"
```

对于使用 Playwright 的脚本，还需要根据页面实际情况调整页面加载等待条件、自动滚动逻辑和浏览器 User-Agent。

网站页面结构、接口或反爬策略变化后，原有选择器可能失效。此时应先检查 Actions 日志，确认是页面访问失败、等待超时还是商品选择器没有匹配到内容。

## 注意事项

- 当前工作流没有配置自动定时任务，需要手动点击运行
- 目标网站可能存在访问频率限制、地区限制或反爬机制
- 动态页面依赖 Playwright 浏览器，必须执行 `python -m playwright install`
- 商品名称发生变化时，程序可能将旧名称识别为下架、新名称识别为上架
- 历史商品列表和日志会被 GitHub Actions 提交到仓库，仓库会持续产生自动提交
- 工作流需要 `contents: write` 权限才能自动提交数据
- Bark 服务异常时，监控数据仍会保存，但通知可能发送失败
- 请遵守目标网站的服务条款和访问规则，不要过度频繁地请求网站

## 技术栈

- Python
- Requests
- BeautifulSoup 4
- Playwright
- lxml
- pandas
- urllib3
- GitHub Actions
- Bark

## 许可证

本项目当前未指定开源许可证。若希望明确允许其他人使用、修改和分发代码，建议根据实际需求添加 MIT 或 Apache-2.0 等许可证。
