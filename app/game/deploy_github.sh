#!/bin/bash

# 史记争霸 - GitHub Pages 一键部署脚本

echo "🎮 史记争霸 - GitHub Pages 部署"
echo "================================"
echo ""

# 检查是否在正确的目录
if [ ! -f "index.html" ]; then
    echo "❌ 错误：请在game目录下运行此脚本"
    exit 1
fi

# 检查git是否已初始化
if [ ! -d "../.git" ]; then
    echo "📦 初始化Git仓库..."
    cd ..
    git init
    git add game/
    git commit -m "Initial commit: 史记争霸游戏"
    echo "✅ Git仓库初始化完成"
    echo ""
    echo "⚠️  下一步："
    echo "1. 在GitHub上创建新仓库（例如：shiji-game）"
    echo "2. 运行以下命令："
    echo "   git remote add origin https://github.com/你的用户名/shiji-game.git"
    echo "   git push -u origin main"
    echo "3. 在GitHub仓库设置中启用Pages（选择main分支的/game文件夹）"
    echo ""
else
    echo "📤 提交更新到GitHub..."
    cd ..
    git add game/
    git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
    echo ""
    echo "✅ 部署完成！"
    echo ""
    echo "🌐 访问地址："
    echo "https://你的GitHub用户名.github.io/仓库名/"
fi
