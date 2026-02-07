#!/bin/bash
#
# 《史记》084-095章节批量处理 - 快速启动脚本
#
# 使用方法：
#   ./start_processing_084_095.sh
#
# 或者指定API密钥：
#   ANTHROPIC_API_KEY="your_key" ./start_processing_084_095.sh
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}《史记》084-095章节批量处理（列传）${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到 python3${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python3: $(python3 --version)"

# 检查anthropic库
if ! python3 -c "import anthropic" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  警告: 未安装 anthropic 库${NC}"
    echo -e "${YELLOW}   安装命令: pip3 install anthropic${NC}"
    read -p "是否现在安装? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install anthropic
    else
        echo -e "${RED}❌ 需要安装 anthropic 库才能继续${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} anthropic 库已安装"

# 检查API密钥
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  未设置 ANTHROPIC_API_KEY 环境变量${NC}"
    echo ""
    echo -e "请设置API密钥："
    echo -e "${BLUE}export ANTHROPIC_API_KEY=\"your_api_key_here\"${NC}"
    echo ""
    read -p "是否现在输入API密钥? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -n "请输入API密钥: "
        read -s api_key
        echo
        export ANTHROPIC_API_KEY="$api_key"
    else
        echo -e "${RED}❌ 需要API密钥才能继续${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} API密钥已设置"

# 检查目录
if [ ! -d "$PROJECT_DIR/docs/original_text" ]; then
    echo -e "${RED}❌ 错误: 未找到原始文本目录${NC}"
    echo -e "   预期路径: $PROJECT_DIR/docs/original_text"
    exit 1
fi

echo -e "${GREEN}✓${NC} 原始文本目录: $PROJECT_DIR/docs/original_text"

# 检查输出目录
mkdir -p "$PROJECT_DIR/chapter_md"
echo -e "${GREEN}✓${NC} 输出目录: $PROJECT_DIR/chapter_md"

# 显示统计
total_files=12  # 084-095共12个章节
completed_files=$(ls -1 "$PROJECT_DIR/chapter_md/0"[89]"?"_*.tagged.md 2>/dev/null | wc -l)

echo ""
echo -e "${BLUE}当前状态:${NC}"
echo -e "  总章节数: ${total_files}"
echo -e "  已完成: ${completed_files}"
echo -e "  待处理: $((total_files - completed_files))"
echo ""

# 列出待处理章节
echo -e "${BLUE}待处理章节列表:${NC}"
echo "  084_屈原贾生列传"
echo "  085_吕不韦列传"
echo "  086_刺客列传"
echo "  087_李斯列传"
echo "  088_蒙恬列传"
echo "  089_张耳陈馀列传"
echo "  090_魏豹彭越列传"
echo "  091_黥布列传"
echo "  092_淮阴侯列传"
echo "  093_韩信卢绾列传"
echo "  094_田儋列传"
echo "  095_樊郦滕灌列传"
echo ""

read -p "是否开始处理? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}已取消${NC}"
    exit 0
fi

echo -e "${GREEN}开始处理章节...${NC}"
cd "$PROJECT_DIR"
python3 scripts/process_chapters_084_095.py

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}处理完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "处理结果保存在: ${BLUE}$PROJECT_DIR/chapter_md/${NC}"
echo ""
echo -e "查看输出文件："
echo -e "${BLUE}ls -lh $PROJECT_DIR/chapter_md/0[89]?_*.tagged.md${NC}"
