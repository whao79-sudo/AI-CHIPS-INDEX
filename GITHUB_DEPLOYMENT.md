# AI Chip Index - GitHub 部署指南

## 📦 GitHub 部署方案

本工具支持三种 GitHub 部署方式：

| 方式 | 适合场景 | 自动化程度 |
|------|----------|------------|
| **GitHub Pages** | 公开展示 K 线图 | ⭐⭐⭐ 全自动 |
| **GitHub Actions** | 每日自动更新数据 | ⭐⭐⭐ 全自动 |
| **GitHub Releases** | 发布安装包 | ⭐⭐ 半自动 |

---

## 🚀 方式 1: GitHub Pages + Actions (推荐)

### 步骤

#### 1. 创建仓库

```bash
# 在本地初始化 git
cd ~/.openclaw/workspace/skills/ai-chip-index/standalone/
git init
git add .
git commit -m "Initial commit: AI Chip Index"

# 在 GitHub 创建新仓库 (例如：ai-chip-index)
# 然后关联远程仓库
git remote add origin https://github.com/YOUR_USERNAME/ai-chip-index.git
git branch -M main
git push -u origin main
```

#### 2. 配置 GitHub Pages

1. 进入仓库 **Settings** → **Pages**
2. **Source** 选择 `GitHub Actions`
3. 保存

#### 3. 启用 Actions

1. 进入仓库 **Actions** 标签
2. 找到 "Daily Index Update" workflow
3. 点击 "Enable workflow"

#### 4. 手动触发首次运行

1. 在 **Actions** → "Daily Index Update"
2. 点击 "Run workflow"
3. 可选：输入日期范围
4. 点击 "Run workflow" 按钮

#### 5. 访问页面

等待 Actions 运行完成后，访问：
```
https://YOUR_USERNAME.github.io/ai-chip-index/AI_CHIP_INDEX_kline.html
```

---

## ⚙️ Actions 配置说明

### 定时任务时间

默认配置（在 `.github/workflows/update-index.yml` 中）：

```yaml
schedule:
  # 每个交易日下午 4 点 (北京时间)
  - cron: '0 8 * * 1-5'
```

**时区转换：**
- GitHub Actions 使用 UTC 时间
- 北京时间 = UTC + 8
- 所以下午 4 点 (16:00) = UTC 8:00

**修改时间：**
```yaml
# 改为每天早上 9 点 (北京时间)
- cron: '1 1 * * 1-5'

# 改为每周一上午 9 点
- cron: '1 1 * * 1'
```

### 手动触发

支持通过 GitHub UI 手动触发，可自定义日期范围：

```yaml
workflow_dispatch:
  inputs:
    start_date:
      description: '开始日期 (YYYY-MM-DD)'
      required: false
      default: '2024-01-01'
    end_date:
      description: '结束日期 (YYYY-MM-DD)'
      required: false
      default: ''
```

---

## 📦 方式 2: GitHub Releases

### 创建 Release

```bash
# 1. 打包
cd ~/.openclaw/workspace/skills/ai-chip-index/
tar -czf ai-chip-index-v1.0.tar.gz standalone/

# 2. 创建 tag
git tag -a v1.0 -m "Release v1.0"
git push origin v1.0

# 3. 在 GitHub 创建 Release
# - 进入仓库 → Releases → Create new release
# - 选择 tag v1.0
# - 上传 ai-chip-index-v1.0.tar.gz
```

### 自动 Release (可选)

添加 Release workflow：

```yaml
# .github/workflows/release.yml
name: Create Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: ai-chip-index-*.tar.gz
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 🔒 私有仓库 vs 公开仓库

### 公开仓库 (Public)
- ✅ 任何人都可以查看 K 线图
- ✅ GitHub Pages 免费
- ✅ Actions 每月 2000 分钟免费额度
- ❌ 代码和数据完全公开

### 私有仓库 (Private)
- ✅ 代码和数据私密
- ✅ GitHub Actions 每月 500 分钟免费额度
- ❌ GitHub Pages 需要公开访问需额外配置
- ❌ 超出免费额度需付费

**建议：**
- 个人使用 → 私有仓库
- 公开展示 → 公开仓库

---

## 📊 查看运行状态

### Actions 日志

1. 进入仓库 **Actions** 标签
2. 点击 workflow 名称
3. 查看每次运行的详细日志

### 输出文件

运行成功后，`output/` 目录会包含：
- `AI_CHIP_INDEX_stocks.csv` - 成分股数据
- `AI_CHIP_INDEX_detail.csv` - 指数数据
- `AI_CHIP_INDEX_kline.html` - K 线图

这些文件会自动提交到仓库并部署到 Pages。

---

## 🔧 自定义配置

### 修改成分股

编辑 `config.yaml` 后提交：

```bash
# 编辑配置文件
vim config.yaml

# 提交
git add config.yaml
git commit -m "Update stock list"
git push
```

### 修改图表样式

编辑 `main.py` 中的 `generate_kline_html()` 函数：

```python
# 修改颜色、字体、布局等
def generate_kline_html(self, df, title="AI CHIP INDEX K 线图"):
    # ... 自定义你的样式
```

### 添加其他指标

在 `main.py` 中添加新的技术指标计算逻辑。

---

## ⚠️ 注意事项

### 1. GitHub Actions 限制

- **免费额度**: 每月 2000 分钟 (公开仓库) / 500 分钟 (私有仓库)
- **单次运行**: 最长 6 小时
- **并发**: 免费账户最多 3 个并发任务

### 2. 数据源限制

- 网易财经接口返回约 1000 条数据 (约 4 年)
- 如需更长历史，需修改代码分段获取

### 3. Pages 部署延迟

- 首次部署可能需要 5-10 分钟
- 后续更新通常 1-2 分钟

### 4. 网络问题

如果 Actions 无法访问网易财经：
- 尝试使用其他数据源
- 或在 workflow 中添加代理配置

---

## 📱 手机查看

部署成功后，用手机浏览器访问：
```
https://YOUR_USERNAME.github.io/ai-chip-index/AI_CHIP_INDEX_kline.html
```

K 线图支持触摸缩放和滑动！

---

## 🆘 故障排查

### Actions 运行失败

1. 检查日志中的错误信息
2. 确认 `requirements.txt` 包含所有依赖
3. 测试本地运行：`python main.py all`

### Pages 无法访问

1. 确认 Pages 已启用
2. 检查 `output/` 目录是否有 HTML 文件
3. 等待 5-10 分钟部署完成

### 数据未更新

1. 检查 cron 表达式时区是否正确
2. 查看 Actions 是否被禁用
3. 手动触发一次 workflow

---

## 📞 支持

如有问题：
1. 查看 `.github/workflows/update-index.yml` 日志
2. 检查 `config.yaml` 配置
3. 本地测试运行

**示例仓库:**
```
https://github.com/YOUR_USERNAME/ai-chip-index
```
