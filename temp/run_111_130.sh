#!/bin/bash
# 运行111-130章节批量处理脚本

# 检查是否设置了API密钥
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量"
    echo ""
    echo "请设置API密钥后再运行此脚本："
    echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
    echo ""
    echo "或者创建 ~/.anthropic_key 文件保存API密钥"
    exit 1
fi

# 检查API密钥文件（备用方案）
if [ -f ~/.anthropic_key ]; then
    export ANTHROPIC_API_KEY=$(cat ~/.anthropic_key)
    echo "✅ 从 ~/.anthropic_key 加载API密钥"
fi

# 切换到项目目录
cd /home/baojie/work/shiji-kb

# 运行处理脚本
echo "=================================="
echo "开始处理《史记》111-130列传章节"
echo "=================================="
python3 scripts/process_chapters_111_130.py

echo ""
echo "处理完成！"
