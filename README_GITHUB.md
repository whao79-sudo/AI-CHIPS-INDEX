# 🦞 AI Chip Index

**AI 芯片等权重指数生成工具** - 自动获取数据、计算指数、生成交互式 K 线图

[![Update Index](https://github.com/YOUR_USERNAME/ai-chip-index/actions/workflows/update-index.yml/badge.svg)](https://github.com/YOUR_USERNAME/ai-chip-index/actions/workflows/update-index.yml)
[![Pages](https://img.shields.io/badge/pages-deploy-blue)](https://YOUR_USERNAME.github.io/ai-chip-index/AI_CHIP_INDEX_kline.html)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 📈 实时查看

**K 线图:** [https://YOUR_USERNAME.github.io/ai-chip-index/AI_CHIP_INDEX_kline.html](https://YOUR_USERNAME.github.io/ai-chip-index/AI_CHIP_INDEX_kline.html)

---

## ✨ 特性

- 🔄 **自动更新** - GitHub Actions 每日自动获取最新数据
- 📊 **交互式图表** - 基于 Plotly.js 的专业 K 线图
- ☁️ **技术指标** - 一目均衡表、布林带、MA300 等
- 📱 **响应式设计** - 支持手机、平板、桌面
- 🎯 **等权重策略** - 14 只 AI 芯片成分股等权重配置
- 🚀 **一键部署** - 支持 GitHub Pages 自动部署

---

## 🎯 成分股

| # | 股票名称 | 代码 | 权重 |
|---|----------|------|------|
| 1 | 中际旭创 | 300308.SZ | 7.14% |
| 2 | 新易盛 | 300502.SZ | 7.14% |
| 3 | 天孚通信 | 300394.SZ | 7.14% |
| 4 | 海光信息 | 688041.SH | 7.14% |
| 5 | 寒武纪 | 688256.SH | 7.14% |
| 6 | 龙芯中科 | 688047.SH | 7.14% |
| 7 | 工业富联 | 601138.SH | 7.14% |
| 8 | 浪潮信息 | 000977.SZ | 7.14% |
| 9 | 中科曙光 | 603019.SH | 7.14% |
| 10 | 香农芯创 | 300475.SZ | 7.14% |
| 11 | 佰维存储 | 688525.SH | 7.14% |
| 12 | 德明利 | 001309.SZ | 7.14% |
| 13 | 江波龙 | 301308.SZ | 7.14% |
| 14 | 兆易创新 | 603986.SH | 7.14% |

---

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/ai-chip-index.git
cd ai-chip-index/standalone

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py all
```

### GitHub 部署

详见 [GitHub 部署指南](GITHUB_DEPLOYMENT.md)

---

## 📊 技术指标

K 线图包含以下指标：

- 🕯️ **K 线蜡烛图** - 红涨绿跌
- ☁️ **一目均衡表** - 转换线、基准线、先行带 A/B
- 📈 **布林带** - 20 日 SMA ±2 标准差
- 📉 **MA300** - 300 日均线及 ±1/±2 标准带
- 📏 **均线组** - EMA5、MA50、MA100
- 🎯 **交叉信号** - 金叉 (↑)、死叉 (↓)

---

## ⚙️ 配置

编辑 `config.yaml` 自定义：

```yaml
# 成分股
stocks:
  - {name: "中际旭创", code: "sz300308"}
  # ... 更多股票

# 指数配置
index:
  base_date: "2024-01-02"
  base_value: 1000.0

# 输出
output:
  dir: "./output"
  start_date: "2024-01-01"
  chart_title: "AI CHIP INDEX K 线图"
```

---

## 📁 输出文件

运行后在 `output/` 目录生成：

| 文件 | 说明 |
|------|------|
| `AI_CHIP_INDEX_stocks.csv` | 成分股 OHLCV 数据 |
| `AI_CHIP_INDEX_detail.csv` | 指数详细数据 |
| `AI_CHIP_INDEX.csv` | 指数简表 |
| `AI_CHIP_INDEX_kline.html` | 交互式 K 线图 |

---

## 🔧 命令行用法

```bash
# 获取数据
python main.py fetch --start 2024-01-01 --end 2026-05-13

# 生成 K 线图
python main.py chart --title "我的指数"

# 一键完成
python main.py all

# 使用自定义配置
python main.py all --config /path/to/config.yaml
```

---

## 📅 自动更新

GitHub Actions 配置为每个交易日下午 4 点 (北京时间) 自动更新。

**手动触发:**
1. 进入仓库 **Actions** 标签
2. 选择 "Daily Index Update"
3. 点击 "Run workflow"

---

## 🌐 数据源

- **网易财经** - 稳定可靠，无需 API Key
- 接口：`http://money.finance.sina.com.cn/quotes_service/`
- 数据：日线 OHLCV (前复权)

---

## 📦 依赖

```txt
pandas>=1.5.0
numpy>=1.20.0
requests>=2.28.0
PyYAML>=6.0
```

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📞 支持

- 📖 详细文档：[GITHUB_DEPLOYMENT.md](GITHUB_DEPLOYMENT.md)
- 🐛 问题反馈：[Issues](https://github.com/YOUR_USERNAME/ai-chip-index/issues)
- 📧 联系：[YOUR_EMAIL]

---

<div align="center">

**🦞 Made with ❤️ for AI Chip Investors**

[⭐ Star this repo](https://github.com/YOUR_USERNAME/ai-chip-index) if you find it useful!

</div>
