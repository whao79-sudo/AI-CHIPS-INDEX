#!/bin/bash
# GitHub 部署快速设置脚本

set -e

echo "🦞 AI Chip Index - GitHub 部署向导"
echo "======================================"
echo ""

# 检查是否已安装 git
if ! command -v git &> /dev/null; then
    echo "❌ 未检测到 git，请先安装 git"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "main.py" ]; then
    echo "❌ 请在 standalone 目录下运行此脚本"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 获取 GitHub 用户名
read -p "请输入你的 GitHub 用户名：" GITHUB_USERNAME
if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ GitHub 用户名不能为空"
    exit 1
fi

REPO_NAME="ai-chip-index"
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo ""
echo "📦 仓库信息:"
echo "   用户名：$GITHUB_USERNAME"
echo "   仓库名：$REPO_NAME"
echo "   仓库 URL: $REPO_URL"
echo ""

# 确认
read -p "确认继续？(y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "❌ 已取消"
    exit 0
fi

echo ""
echo "🚀 开始部署..."

# 初始化 git
if [ ! -d ".git" ]; then
    echo "   初始化 git 仓库..."
    git init
fi

# 添加所有文件
echo "   添加文件..."
git add .

# 首次提交
echo "   创建首次提交..."
git commit -m "🎉 Initial commit: AI Chip Index" || true

# 检查远程仓库
if ! git remote | grep -q "origin"; then
    echo "   添加远程仓库..."
    git remote add origin "$REPO_URL"
fi

# 设置分支
echo "   设置主分支..."
git branch -M main

echo ""
echo "======================================"
echo "✅ 本地设置完成！"
echo ""
echo "📋 下一步操作:"
echo ""
echo "1️⃣  在 GitHub 创建仓库:"
echo "   https://github.com/new"
echo "   仓库名：$REPO_NAME"
echo "   可见性：公开/私有 (自行选择)"
echo "   ⚠️  不要勾选 'Initialize with README'"
echo ""
echo "2️⃣  推送代码到 GitHub:"
echo "   git push -u origin main"
echo ""
echo "3️⃣  配置 GitHub Pages:"
echo "   - 进入仓库 Settings → Pages"
echo "   - Source 选择 'GitHub Actions'"
echo "   - 保存"
echo ""
echo "4️⃣  启用 Actions:"
echo "   - 进入仓库 Actions 标签"
echo "   - 找到 'Daily Index Update'"
echo "   - 点击 'Enable workflow'"
echo ""
echo "5️⃣  手动触发首次运行:"
echo "   - Actions → Daily Index Update"
echo "   - Run workflow → Run workflow"
echo ""
echo "6️⃣  等待部署完成 (约 5-10 分钟)"
echo "   访问：https://${GITHUB_USERNAME}.github.io/${REPO_NAME}/AI_CHIP_INDEX_kline.html"
echo ""
echo "======================================"
echo "📖 详细文档：GITHUB_DEPLOYMENT.md"
echo ""
