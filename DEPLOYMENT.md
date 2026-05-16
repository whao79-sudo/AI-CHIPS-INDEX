# AI Chip Index - 外部网络部署指南

## 📦 完整文件包

独立部署版已创建在：
```
~/.openclaw/workspace/skills/ai-chip-index/standalone/
├── main.py              # 主程序
├── config.yaml          # 配置文件
├── requirements.txt     # Python 依赖
├── README.md            # 使用说明
└── output/              # 输出目录 (运行后生成)
```

## 🚀 部署方式

### 方式 1: 直接复制 (推荐)

```bash
# 1. 打包
cd ~/.openclaw/workspace/skills/ai-chip-index/
tar -czf ai-chip-index-standalone.tar.gz standalone/

# 2. 传输到目标服务器
scp ai-chip-index-standalone.tar.gz user@remote-server:/path/to/

# 3. 在目标服务器解压
ssh user@remote-server
cd /path/to/
tar -xzf ai-chip-index-standalone.tar.gz
cd standalone/

# 4. 安装依赖并运行
pip install -r requirements.txt
python main.py all
```

### 方式 2: Git 仓库

```bash
# 1. 在目标服务器克隆
git clone <your-repo-url> ai-chip-index
cd ai-chip-index/standalone

# 2. 安装依赖并运行
pip install -r requirements.txt
python main.py all
```

### 方式 3: Docker 部署

创建 `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY standalone/ /app/

RUN pip install -r requirements.txt

CMD ["python", "main.py", "all"]
```

```bash
# 构建和运行
docker build -t ai-chip-index .
docker run -v $(pwd)/output:/app/output ai-chip-index
```

## 📋 配置说明

编辑 `config.yaml`:

```yaml
# 修改成分股
stocks:
  - {name: "你的股票", code: "sz000001"}
  # ...

# 修改基期
index:
  base_date: "2024-01-02"
  base_value: 1000.0

# 修改输出
output:
  dir: "./output"
  start_date: "2024-01-01"
  end_date: null  # null=今天
```

## ⏰ 定时任务 (每日更新)

```bash
# 编辑 crontab
crontab -e

# 添加每日下午 4 点更新 (A 股收盘后)
0 16 * * 1-5 cd /path/to/standalone && python main.py all >> update.log 2>&1
```

## 🌐 网络要求

**需要访问的外部资源:**
- `money.finance.sina.com.cn` - 网易财经数据接口
- `cdn.plot.ly` - K 线图 JavaScript 库 (可选，可下载到本地)

**防火墙规则:**
```bash
# 允许出站 HTTPS
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
```

## 📊 输出文件

运行后生成在 `output/` 目录:

| 文件 | 说明 | 用途 |
|------|------|------|
| `AI_CHIP_INDEX_stocks.csv` | 成分股 OHLCV 数据 | 原始数据 |
| `AI_CHIP_INDEX_detail.csv` | 指数详细数据 | 分析使用 |
| `AI_CHIP_INDEX.csv` | 指数简表 | 快速查看 |
| `AI_CHIP_INDEX_kline.html` | 交互式 K 线图 | 可视化 |

## 🔧 常用命令

```bash
# 获取数据
python main.py fetch --start 2024-01-01 --end 2026-05-13

# 生成 K 线图
python main.py chart --title "我的指数"

# 一键完成
python main.py all

# 使用自定义配置
python main.py all --config /path/to/custom.yaml
```

## 📱 Web 访问 (可选)

如果需要让其他人通过浏览器查看:

```bash
# 简单方式：Python 内置服务器
cd output/
python -m http.server 8000

# 访问：http://your-server-ip:8000/AI_CHIP_INDEX_kline.html
```

**生产环境建议:**
```bash
# 使用 Nginx
sudo apt install nginx
sudo cp output/*.html /var/www/html/
# 访问：http://your-server-ip/AI_CHIP_INDEX_kline.html
```

## ⚠️ 注意事项

1. **网络环境**: 确保服务器能访问外网 (网易财经接口)
2. **Python 版本**: 需要 Python 3.8+
3. **依赖安装**: 首次运行需要安装依赖 (`pip install -r requirements.txt`)
4. **数据更新**: 网易接口返回约 1000 条数据 (约 4 年历史)
5. **时区**: 服务器时区建议设为 Asia/Shanghai

## 🆘 故障排查

**Q: 数据获取失败？**
```bash
# 测试网络
curl "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sz300308&scale=240&ma=no&datalen=10"

# 如果失败，检查防火墙/代理设置
```

**Q: 依赖安装失败？**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Q: 图表无法加载？**
```bash
# 下载 Plotly.js 到本地
wget https://cdn.plot.ly/plotly-2.27.0.min.js -O output/plotly.min.js
# 修改 main.py 中的 CDN 链接为本地路径
```

## 📞 支持

如有问题，检查:
1. `output/` 目录是否有写入权限
2. 网络连接是否正常
3. Python 版本是否 >= 3.8
4. 依赖是否全部安装
