#!/bin/bash

# 史记争霸 - 创建Netlify部署包

echo "📦 创建Netlify部署包..."
echo "================================"

# 创建临时部署目录
DEPLOY_DIR="/tmp/shiji-game-deploy"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# 复制所有文件
echo "📋 复制文件..."
cp /home/baojie/work/shiji-kb/game/index.html $DEPLOY_DIR/
cp /home/baojie/work/shiji-kb/game/styles.css $DEPLOY_DIR/
cp /home/baojie/work/shiji-kb/game/game.js $DEPLOY_DIR/
cp /home/baojie/work/shiji-kb/game/README.md $DEPLOY_DIR/

# 创建netlify配置
echo "⚙️  创建配置文件..."
cat > $DEPLOY_DIR/netlify.toml << 'EOF'
[build]
  publish = "."

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
EOF

# 创建压缩包
echo "🗜️  创建压缩包..."
cd $DEPLOY_DIR
zip -r shiji-game.zip *
mv shiji-game.zip /home/baojie/work/shiji-kb/game/

echo ""
echo "✅ 部署包创建完成！"
echo ""
echo "📦 文件位置："
echo "   /home/baojie/work/shiji-kb/game/shiji-game.zip"
echo ""
echo "🚀 部署步骤："
echo "1. 访问 https://app.netlify.com/drop"
echo "2. 拖拽 shiji-game.zip 文件"
echo "3. 等待部署完成"
echo ""
echo "或者直接拖拽整个文件夹："
echo "   $DEPLOY_DIR"
