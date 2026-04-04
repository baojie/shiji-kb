"""
项目路径配置常量

提供统一的路径管理，避免硬编码路径字符串。
所有脚本应优先使用本配置文件中的路径常量。

创建日期: 2026-04-05
维护者: Claude + 用户
"""

from pathlib import Path

# ============================================================================
# 项目根目录
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================================
# 语料库路径 (corpus/)
# ============================================================================

CORPUS_ROOT = PROJECT_ROOT / 'corpus'

# corpus/archive/ - 文本处理历史阶段
ARCHIVE_ROOT = CORPUS_ROOT / 'archive'
CHAPTER_DIR = ARCHIVE_ROOT / 'chapter'                    # 标准底本（130章纯文本）
CHAPTER_IMPROVED_DIR = ARCHIVE_ROOT / 'chapter_improved'  # 改进版（保留空行）
CHAPTER_NUMBERED_DIR = ARCHIVE_ROOT / 'chapter_numbered'  # 编号版（带[N]段落号）

# corpus/shiji/ - 史记各版本语料
SHIJI_ROOT = CORPUS_ROOT / 'shiji'
SHIJI_SIMPLIFIED = SHIJI_ROOT / '史记.简体.txt'
SHIJI_TRADITIONAL = SHIJI_ROOT / '史記正文.繁体.txt'
SHIJI_SANJIA = SHIJI_ROOT / '史記三家注.繁体.txt'
SHIJI_SIKU = SHIJI_ROOT / '史记四库.txt'
WIKISOURCE_SHIJI_DIR = SHIJI_ROOT / 'wikisource_shiji'
WIKISOURCE_SANJIA_DIR = SHIJI_ROOT / 'wikisource_sanjia'

# corpus/other/ - 其他古籍语料
OTHER_ROOT = CORPUS_ROOT / 'other'


# ============================================================================
# 工作目录
# ============================================================================

# chapter_md/ - 当前工作底本（130个标注文件，Base Copy）
BASE_COPY = PROJECT_ROOT / 'chapter_md'

# docs/original_text/ - 独立工作定本
DOCS_ORIGINAL_TEXT_DIR = PROJECT_ROOT / 'docs' / 'original_text'


# ============================================================================
# 数据目录 (data/)
# ============================================================================

DATA_ROOT = PROJECT_ROOT / 'data'

# 多音字数据
POLYPHONE_CONTEXTS_DIR = DATA_ROOT / 'polyphone_contexts'
PRONUNCIATION_TEMPLATES_DIR = DATA_ROOT / 'pronunciation_templates'

# 表格数据
TABLES_DIR = DATA_ROOT / 'tables'

# 笔记数据
NOTES_DIR = DATA_ROOT / 'notes'


# ============================================================================
# 文档目录 (docs/)
# ============================================================================

DOCS_ROOT = PROJECT_ROOT / 'docs'

# docs/data/ - 数据资产
DOCS_DATA_DIR = DOCS_ROOT / 'data'
SPECIAL_PRONUNCIATION_JSON = DOCS_DATA_DIR / 'special-pronunciation.json'
S2T_CUSTOM_VARIANTS_JSON = DOCS_DATA_DIR / 's2t-custom-variants.json'
PINYIN_CUSTOM_DICT_TXT = DOCS_DATA_DIR / 'pinyin-custom-dict.txt'

# docs/chapters/ - HTML展示页面
DOCS_CHAPTERS_DIR = DOCS_ROOT / 'chapters'


# ============================================================================
# 知识图谱目录 (kg/)
# ============================================================================

KG_ROOT = PROJECT_ROOT / 'kg'

# kg/entities/ - 实体数据
KG_ENTITIES_DIR = KG_ROOT / 'entities'
KG_ENTITIES_DATA_DIR = KG_ENTITIES_DIR / 'data'
KG_ENTITIES_SCRIPTS_DIR = KG_ENTITIES_DIR / 'scripts'

# kg/vocabularies/ - 词表数据
KG_VOCABULARIES_DIR = KG_ROOT / 'vocabularies'

# kg/events/ - 事件数据
KG_EVENTS_DIR = KG_ROOT / 'events'

# kg/facts/ - 事实数据
KG_FACTS_DIR = KG_ROOT / 'facts'

# kg/structure/ - 结构数据
KG_STRUCTURE_DIR = KG_ROOT / 'structure'


# ============================================================================
# 日志目录 (logs/)
# ============================================================================

LOGS_ROOT = PROJECT_ROOT / 'logs'

# logs/daily/ - 每日工作日志
LOGS_DAILY_DIR = LOGS_ROOT / 'daily'

# logs/curation/ - 校勘日志
LOGS_CURATION_DIR = LOGS_ROOT / 'curation'
LOGS_CURATION_REPORTS_DIR = LOGS_CURATION_DIR / 'reports'

# logs/lint/ - lint检查日志
LOGS_LINT_DIR = LOGS_ROOT / 'lint'


# ============================================================================
# 技能文档目录 (skills/)
# ============================================================================

SKILLS_ROOT = PROJECT_ROOT / 'skills'
SKILLS_REFERENCES_DIR = SKILLS_ROOT / 'references'


# ============================================================================
# 脚本目录 (scripts/)
# ============================================================================

SCRIPTS_ROOT = PROJECT_ROOT / 'scripts'


# ============================================================================
# 实验室目录 (labs/)
# ============================================================================

LABS_ROOT = PROJECT_ROOT / 'labs'
LABS_PLANNING_DIR = LABS_ROOT / 'planning'
LABS_PROTOTYPES_DIR = LABS_ROOT / 'prototypes'
LABS_RESEARCH_DIR = LABS_ROOT / 'research'


# ============================================================================
# 辅助函数
# ============================================================================

def get_chapter_file(chapter_num: int, directory: Path = CHAPTER_DIR) -> Path:
    """
    获取指定章节的文件路径

    Args:
        chapter_num: 章节号（1-130）
        directory: 目录路径（默认为CHAPTER_DIR）

    Returns:
        Path: 章节文件路径（如果存在多个匹配，返回第一个）

    Raises:
        FileNotFoundError: 如果找不到对应章节文件

    Example:
        >>> get_chapter_file(1)
        PosixPath('/path/to/corpus/archive/chapter/001_五帝本纪.txt')
    """
    pattern = f"{chapter_num:03d}_*.txt"
    matches = list(directory.glob(pattern))

    if not matches:
        raise FileNotFoundError(
            f"未找到章节 {chapter_num:03d} 的文件（目录: {directory}）"
        )

    return matches[0]


def get_chapter_md_file(chapter_num: int) -> Path:
    """
    获取指定章节的标注文件路径

    Args:
        chapter_num: 章节号（1-130）

    Returns:
        Path: 标注文件路径

    Example:
        >>> get_chapter_md_file(1)
        PosixPath('/path/to/chapter_md/001_五帝本纪.tagged.md')
    """
    pattern = f"{chapter_num:03d}_*.tagged.md"
    matches = list(BASE_COPY.glob(pattern))

    if not matches:
        raise FileNotFoundError(
            f"未找到章节 {chapter_num:03d} 的标注文件"
        )

    return matches[0]


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path: 目录路径

    Example:
        >>> ensure_dir(LOGS_DAILY_DIR)
        PosixPath('/path/to/logs/daily')
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


# ============================================================================
# 配置验证
# ============================================================================

def validate_project_structure():
    """
    验证项目目录结构是否完整

    Raises:
        RuntimeError: 如果关键目录不存在
    """
    critical_dirs = [
        CORPUS_ROOT,
        CHAPTER_DIR,
        BASE_COPY,
        DOCS_ROOT,
        SCRIPTS_ROOT,
    ]

    missing_dirs = [d for d in critical_dirs if not d.exists()]

    if missing_dirs:
        missing_paths = '\n  '.join(str(d) for d in missing_dirs)
        raise RuntimeError(
            f"项目关键目录缺失：\n  {missing_paths}\n"
            f"当前工作目录：{Path.cwd()}\n"
            f"请确认在项目根目录下运行脚本"
        )


if __name__ == '__main__':
    # 测试模块：验证项目结构并打印关键路径
    print("=== 项目路径配置验证 ===\n")

    try:
        validate_project_structure()
        print("✓ 项目目录结构验证通过\n")
    except RuntimeError as e:
        print(f"✗ 项目目录结构验证失败：\n{e}\n")
        exit(1)

    print("关键路径：")
    print(f"  项目根目录: {PROJECT_ROOT}")
    print(f"  语料库根目录: {CORPUS_ROOT}")
    print(f"  标准底本: {CHAPTER_DIR}")
    print(f"  工作底本: {BASE_COPY}")
    print(f"  数据目录: {DATA_ROOT}")
    print(f"  文档目录: {DOCS_ROOT}")
    print(f"  脚本目录: {SCRIPTS_ROOT}")

    print("\n示例：获取第1章文件路径")
    try:
        chapter_1 = get_chapter_file(1)
        print(f"  {chapter_1}")
    except FileNotFoundError as e:
        print(f"  错误：{e}")

    print("\n示例：获取第1章标注文件路径")
    try:
        chapter_md_1 = get_chapter_md_file(1)
        print(f"  {chapter_md_1}")
    except FileNotFoundError as e:
        print(f"  错误：{e}")
