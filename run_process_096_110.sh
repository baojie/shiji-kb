#!/bin/bash

# 《史记》096-110列传批量处理快速启动脚本

echo "=============================================================================="
echo "《史记》096-110列传批量标注工具"
echo "=============================================================================="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"
echo ""

# 检查anthropic库
if ! python3 -c "import anthropic" 2>/dev/null; then
    echo "⚠️  警告: 未安装 anthropic 库"
    echo "正在安装..."
    pip install anthropic
    echo ""
fi

# 检查API密钥
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量"
    echo ""
    echo "请先设置API密钥:"
    echo "  export ANTHROPIC_API_KEY=\"your_api_key_here\""
    echo ""
    echo "或者在脚本中直接设置:"
    echo "  ANTHROPIC_API_KEY=\"your_api_key_here\" bash run_process_096_110.sh"
    echo ""
    exit 1
fi

echo "✅ API密钥已设置"
echo ""

# 显示任务信息
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "任务信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "章节范围: 096-110（共15个列传）"
echo "输入目录: docs/original_text/"
echo "输出目录: chapter_md/"
echo "进度文件: progress_096_110.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查进度文件
if [ -f "progress_096_110.json" ]; then
    completed=$(python3 -c "import json; data=json.load(open('progress_096_110.json')); print(len(data['completed']))")
    echo "📊 已完成章节: $completed/15"
    echo ""
fi

# 询问是否继续
read -p "是否开始处理? (y/n, 默认y): " confirm
confirm=${confirm:-y}

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "=============================================================================="
echo "开始批量处理..."
echo "=============================================================================="
echo ""

# 运行Python脚本
python3 process_096_110_manual.py

# 检查执行结果
if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================================================="
    echo "✅ 处理完成！"
    echo "=============================================================================="
    echo ""
    echo "输出文件位置: chapter_md/"
    echo "进度文件: progress_096_110.json"
    echo ""

    # 显示文件列表
    echo "生成的文件:"
    ls -lh chapter_md/{096..110}_*.tagged.md 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    echo ""

    # 统计总行数
    total_lines=$(wc -l chapter_md/{096..110}_*.tagged.md 2>/dev/null | tail -1 | awk '{print $1}')
    echo "总行数: $total_lines"
    echo ""
else
    echo ""
    echo "=============================================================================="
    echo "⚠️  处理过程中出现错误"
    echo "=============================================================================="
    echo ""
    echo "请检查:"
    echo "  1. progress_096_110.json 查看进度"
    echo "  2. 终端输出的错误信息"
    echo "  3. 网络连接和API状态"
    echo ""
    echo "可以重新运行脚本继续处理未完成的章节"
    echo ""
    exit 1
fi
