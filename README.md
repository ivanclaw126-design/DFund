# DFund

DFund 是一个面向私募基金净值跟踪的本地自动化项目。它会在 macOS 上从 Apple Mail 中提取指定基金的净值邮件，补充市场基准指数数据，生成静态数据文件，并把可视化看板发布到 GitHub Pages。

当前仓库主要服务于两只基金：

- `SBFZ85`，衍盛天璇 CTA 一号私募证券投资基金
- `SBFZ95`，衍盛开阳多策略混合私募证券投资基金

## 项目能力

- 从 macOS 的 Apple Mail 收件箱抓取指定主题的净值邮件
- 解析邮件正文中的估值日期、单位净值、累计净值、净资产与实缴资本
- 对重复估值日数据去重，并优先保留原始邮件与较新的记录
- 使用 `akshare` 拉取上证指数、沪深 300、中证 500、中证 1000 作为比较基准
- 生成 `data/*.json` 与 `docs/data/*.json`
- 更新 `docs/index.html` 所需数据，让 GitHub Pages 直接展示最新看板
- 在更新成功或失败时发送飞书通知

## 目录结构

```text
DFund/
├── data/                     # 原始输出数据与增强后的基金/指数 JSON
├── docs/                     # GitHub Pages 静态站点
│   ├── data/                 # 前端消费的 JSON 数据
│   └── index.html            # 看板页面
├── scripts/
│   ├── update_data.py        # 主更新脚本：抓邮件、算指标、拉指数、同步 docs
│   ├── publish.sh            # 更新后提交并推送
│   └── notify_feishu.py      # 飞书通知
├── update-now.sh             # 一键触发更新
└── requirements.txt          # Python 依赖
```

## 运行环境

- macOS
- Python 3
- Apple Mail 已登录并能访问目标邮箱
- `osascript` 可用
- 已安装 Git

Python 依赖安装：

```bash
python3 -m pip install -r requirements.txt
```

## 数据来源

### 基金净值

基金净值来自 Apple Mail 收件箱中的目标邮件。脚本会根据预设主题匹配邮件，再从正文中用正则抽取净值字段。

当前内置匹配项位于 [scripts/update_data.py](/Users/spicyclaw/MyProjects/DFund/scripts/update_data.py)：

- `SBFZ85` 对应主题 `【基金净值】SBFZ85(总)_衍盛天璇CTA一号私募证券投资基金`
- `SBFZ95` 对应主题 `【基金净值】SBFZ95(总)_衍盛开阳多策略混合私募证券投资基金`

### 基准指数

基准指数通过 `akshare` 获取，当前包含：

- 上证指数
- 沪深 300
- 中证 500
- 中证 1000

## 使用方式

### 1. 仅更新本地数据

```bash
python3 scripts/update_data.py
```

脚本会完成这些工作：

1. 从 Apple Mail 提取基金净值邮件
2. 生成增强后的基金数据 JSON
3. 拉取区间内指数数据
4. 把数据同步到 `docs/data/`
5. 给 `docs/index.html` 注入“最后更新时间”显示

### 2. 一键更新并发布

```bash
./update-now.sh
```

这个命令会进一步调用 [scripts/publish.sh](/Users/spicyclaw/MyProjects/DFund/scripts/publish.sh)，默认流程是：

1. 运行 `python3 scripts/update_data.py`
2. 暂存 `data`、`docs`、`README.md`、`scripts`、`update-now.sh`
3. 如果有变更则自动提交
4. 推送到 `origin main`
5. 发送飞书成功通知

## 输出文件说明

### `data/*.json`

基金增强数据文件包含：

- `rows`：按估值日排序的净值明细
- `metrics.latest_nav`：最新单位净值
- `metrics.latest_date`：最新估值日
- `metrics.since_inception`：成立以来收益
- `metrics.annualized_return_since_inception`：成立以来年化收益
- `metrics.last_5d`、`last_20d`、`last_60d`：短期区间收益
- `metrics.annualized_vol`：年化波动率
- `metrics.max_drawdown`：最大回撤及区间

### `docs/`

`docs/` 是最终发布目录，适合直接接到 GitHub Pages。页面会读取 `docs/data/*.json`，展示基金净值走势、阶段收益与关键指标。

## 自动化发布建议

如果你希望每天固定时间自动更新，可以在 macOS 上配合 `launchd`、`cron` 或其他调度器执行：

```bash
/Users/spicyclaw/MyProjects/DFund/update-now.sh
```

项目原始设计目标是按上海时区每日晚间定时刷新。

## 飞书通知

更新成功或失败后，脚本会通过 [scripts/notify_feishu.py](/Users/spicyclaw/MyProjects/DFund/scripts/notify_feishu.py) 发送消息到预设飞书会话。当前脚本依赖本地 `openclaw` 命令。

如果本机没有 `openclaw`，数据更新仍可执行，但飞书发送会退化为日志输出。

## 注意事项

- 这个项目依赖本地 Apple Mail，因此不适合直接搬到无桌面环境的 Linux 服务器
- 邮件解析使用固定主题和正则格式，如果基金邮件模板变化，需要同步修改脚本
- `publish.sh` 默认直接推送 `main`，适合个人仓库或低协作场景；多人协作时建议改成分支加 Pull Request 流程
- 仓库中的 `docs/` 是发布产物，通常应视为可生成文件

## 常用命令

```bash
# 安装依赖
python3 -m pip install -r requirements.txt

# 本地生成数据
python3 scripts/update_data.py

# 更新并发布
./update-now.sh
```

## 后续可优化方向

- 把基金列表、邮件主题和通知目标抽成配置文件
- 为邮件解析与指标计算补充单元测试
- 把自动提交范围收窄，避免把无关文件一并提交
- 为 GitHub Pages 页面增加更多对比分析与筛选能力
