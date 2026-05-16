# AI Chip Index - 独立部署版

AI 芯片等权重指数生成工具 - 可在任何 Python 环境中独立运行

## 快速开始

```bash
# 1. 克隆或下载本文件夹
cd ai-chip-index

# 2. 安装依赖
pip install -r requirements.txt

# 3. 获取数据并计算指数
python main.py fetch

# 4. 生成 K 线图
python main.py chart

# 5. 查看结果
# 打开 output/AI_CHIP_INDEX_kline.html
```

## 文件结构

```
ai-chip-index/
├── main.py                 # 主程序
├── requirements.txt        # Python 依赖
├── config.yaml            # 配置文件
├── README.md              # 使用说明
└── output/                # 输出目录 (自动生成)
    ├── AI_CHIP_INDEX_stocks.csv
    ├── AI_CHIP_INDEX_detail.csv
    └── AI_CHIP_INDEX_kline.html
```

## 配置说明

编辑 `config.yaml` 自定义：

```yaml
# 成分股配置
stocks:
  - {name: "中际旭创", code: "sz300308"}
  - {name: "新易盛", code: "sz300502"}
  # ... 更多股票

# 指数配置
index:
  base_date: "2024-01-02"
  base_value: 1000.0

# 输出配置
output:
  dir: "./output"
  start_date: "2024-01-01"
  end_date: null  # null 表示今天
```

## 命令行用法

```bash
# 获取数据
python main.py fetch --start 2024-01-01 --end 2026-05-13

# 生成 K 线图
python main.py chart --title "我的 AI 芯片指数"

# 一键完成 (获取数据 + 生成图表)
python main.py all

# 使用自定义配置
python main.py fetch --config /path/to/config.yaml
```

## API 用法

```python
from ai_chip_index import IndexGenerator

# 创建生成器
generator = IndexGenerator()

# 获取数据
stocks_df = generator.fetch_data(start="2024-01-01", end="2026-05-13")

# 计算指数
index_df = generator.calculate_index(stocks_df)

# 生成 K 线图 HTML
html = generator.generate_kline_html(index_df)

# 保存
index_df.to_csv("index.csv", index=False)
with open("kline.html", "w") as f:
    f.write(html)
```

## 数据源

默认使用**网易财经**接口：
- ✅ 无需 API Key
- ✅ 稳定可靠
- ✅ 数据免费

## 依赖环境

- Python 3.8+
- pandas
- numpy
- requests
- PyYAML

## 部署到服务器

```bash
# 1. 上传整个文件夹到服务器
scp -r ai-chip-index user@server:/path/to/

# 2. SSH 登录服务器
ssh user@server

# 3. 安装依赖
cd /path/to/ai-chip-index
pip install -r requirements.txt

# 4. 运行
python main.py all

# 5. 设置定时任务 (每日更新)
crontab -e
# 添加：0 16 * * 1-5 cd /path/to/ai-chip-index && python main.py all
```

## Docker 部署

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app/

RUN pip install -r requirements.txt

CMD ["python", "main.py", "all"]
```

```bash
# 构建镜像
docker build -t ai-chip-index .

# 运行
docker run -v $(pwd)/output:/app/output ai-chip-index
```

## 常见问题

**Q: 数据获取失败？**
A: 检查网络连接，网易财经接口需要能访问外网

**Q: 如何添加/删除成分股？**
A: 编辑 `config.yaml` 中的 `stocks` 列表

**Q: 如何更改基期？**
A: 编辑 `config.yaml` 中的 `index.base_date` 和 `index.base_value`

**Q: 如何自定义 K 线图样式？**
A: 编辑 `main.py` 中的 `generate_kline_html()` 函数

## License

MIT
