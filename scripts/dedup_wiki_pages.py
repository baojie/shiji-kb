#!/usr/bin/env python3
"""
Wiki页面去重脚本
把同一主题的多个版本合并为一个规范文件
"""

import os
import subprocess
import sys
from pathlib import Path

PAGES_DIR = Path("/home/baojie/work/knowledge/shiji-kb/wiki/public/pages")
HISTORY_DIR = Path("/home/baojie/work/knowledge/shiji-kb/wiki/public/history")
REPO_ROOT = Path("/home/baojie/work/knowledge/shiji-kb")

total_groups = 0
total_deleted = 0
total_kept = 0

def file_quality_score(path: Path) -> tuple:
    """返回 (字节数, 行数, 章节数, 有引用, 有表格)，用于比较质量"""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    sections = sum(1 for l in lines if l.startswith("##"))
    has_quotes = any(l.startswith(">") for l in lines)
    has_table = any("|" in l for l in lines)
    return (len(content), len(lines), sections, has_quotes, has_table)

def pick_best(files: list[Path]) -> Path:
    """选出质量最好的文件"""
    scored = [(f, file_quality_score(f)) for f in files]
    # 按 (字节数, 行数, 章节数, 引用, 表格) 降序
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]

def pick_canonical_name(files: list[Path]) -> str:
    """选规范文件名：优先最短的中文名（不含冒号/句号等描述性后缀）"""
    # 排除带冒号、长描述的，短名优先
    names = [f.stem for f in files]
    # 按名称长度升序
    names_sorted = sorted(names, key=len)
    return names_sorted[0]

def record_revision(page_name: str, summary: str):
    script = REPO_ROOT / "wiki/scripts/butler/record_revision.py"
    if not script.exists():
        print(f"  [警告] record_revision.py 不存在，跳过记录")
        return
    result = subprocess.run(
        ["python3", str(script), page_name, "--summary", summary, "--author", "butler"],
        capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    if result.returncode != 0:
        print(f"  [警告] record_revision 失败: {result.stderr.strip()}")
    else:
        print(f"  [记录] revision 已写入 {page_name}")

def process_group(group_name: str, files: list[Path]):
    """处理一个重复组"""
    global total_groups, total_deleted, total_kept

    if len(files) < 2:
        return

    total_groups += 1
    print(f"\n=== 处理组: {group_name} ({len(files)} 个版本) ===")
    for f in files:
        score = file_quality_score(f)
        print(f"  {f.name}: {score[0]}字节, {score[1]}行, {score[2]}节, 引用={score[3]}, 表格={score[4]}")

    # 找最优版本
    best = pick_best(files)
    # 找规范名
    canonical_stem = pick_canonical_name(files)
    canonical_file = PAGES_DIR / f"{canonical_stem}.md"

    print(f"  最优版本: {best.name}")
    print(f"  规范文件名: {canonical_stem}.md")

    # 如果最优版本与规范名不同，把最优内容写入规范文件
    if best != canonical_file:
        content = best.read_text(encoding="utf-8")
        canonical_file.write_text(content, encoding="utf-8")
        print(f"  [写入] {best.name} -> {canonical_stem}.md")
        # 删除原最优版本（已复制到规范名）
        best.unlink()
        print(f"  [删除] {best.name}")
        total_deleted += 1
        # 也删除对应的 history
        best_history = HISTORY_DIR / f"{best.stem}.json"
        if best_history.exists():
            best_history.unlink()
            print(f"  [删除] history/{best.stem}.json")

    # 删除其他冗余版本
    for f in files:
        if f == canonical_file:
            continue
        if not f.exists():  # 已被上面删除（即 best == f）
            continue
        f.unlink()
        print(f"  [删除] {f.name}")
        total_deleted += 1
        # 删除 history
        hist = HISTORY_DIR / f"{f.stem}.json"
        if hist.exists():
            hist.unlink()
            print(f"  [删除] history/{f.stem}.json")

    total_kept += 1

    # 记录 revision
    n_merged = len(files)
    record_revision(canonical_stem, f"butler/dedup: 合并{n_merged}个版本，保留最完整内容")


def glob_group(prefix: str) -> list[Path]:
    """按前缀找所有页面文件"""
    return sorted(PAGES_DIR.glob(f"{prefix}*.md"))


# ============================================================
# 定义所有需要处理的重复组
# 每项: (规范组名, [文件列表 or 前缀])
# ============================================================

def get_groups():
    groups = []

    # === 高优先级 ===

    # 商鞅变法 (8个) - 两个子主题分开处理
    # 子主题1: 八步推行法
    g1 = [
        PAGES_DIR / "商鞅变法八步推行法：大规模改革落地方法论.md",
        PAGES_DIR / "商鞅变法八步推行全流程：权力获取到扩大成果的改革落地完整方法论.md",
        PAGES_DIR / "商鞅变法八步推行完整方法论：四轮说服权力获取理论辩论公信力建立执法到扩大成果.md",
    ]
    groups.append(("商鞅变法八步推行", [f for f in g1 if f.exists()]))

    # 子主题2: 阻力应对
    g2 = [
        PAGES_DIR / "商鞅变法改革阻力五类应对策略.md",
        PAGES_DIR / "商鞅变法阻力完整方法论：五类阻力应对矩阵恩威并重退出机制与成败根本原因.md",
        PAGES_DIR / "商鞅变法阻力五类应对策略：理论辩论铁腕执法与功成身退方法论.md",
    ]
    groups.append(("商鞅变法阻力", [f for f in g2 if f.exists()]))

    # 商鞅变法.md 和 商鞅变法三辩.md 保持独立（主题不同，不合并）
    # 商鞅立木为信 保持独立

    # 功高震主 (6个)
    g3 = [
        PAGES_DIR / "功高震主的生存之道.md",
        PAGES_DIR / "功高震主六重自保术.md",
        PAGES_DIR / "功高震主四策决策树：张良萧何韩信曹参比较.md",
        PAGES_DIR / "功高震主四策决策树：张良萧何韩信曹参的生存决策树.md",
        PAGES_DIR / "功高震主四策：张良萧何韩信曹参的生存决策树.md",
        PAGES_DIR / "功高震主.md",
    ]
    groups.append(("功高震主", [f for f in g3 if f.exists()]))

    # 围魏救赵 (6个)
    g4 = [
        PAGES_DIR / "围魏救赵：桂陵与马陵之战.md",
        PAGES_DIR / "围魏救赵六步操作法：批亢捣虚间接路线战略.md",
        PAGES_DIR / "围魏救赵完整方法论：批亢捣虚六步法三原则决策点与现代间接路线策略.md",
        PAGES_DIR / "围魏救赵完整战术框架：批亢捣虚六步法与间接路线三原则.md",
        PAGES_DIR / "围魏救赵战术.md",
        PAGES_DIR / "围魏救赵.md",
    ]
    groups.append(("围魏救赵", [f for f in g4 if f.exists()]))

    # 四战之地 (5个)
    g5 = [
        PAGES_DIR / "四战之地的缓冲国困境.md",
        PAGES_DIR / "四战之地生存策略工具包.md",
        PAGES_DIR / "四战之地生存策略.md",
        PAGES_DIR / "四战之地五策生存法.md",
        PAGES_DIR / "四战之地五策生存工具包：郑国宋国蔡国春秋夹缝中的系统性方法论.md",
    ]
    groups.append(("四战之地", [f for f in g5 if f.exists()]))

    # 宋襄公 (5个) - 宋襄公.md 是人物页面保持独立，其余合并
    g6 = [
        PAGES_DIR / "宋襄公泓之战：道义与成功冲突时五维决策框架与礼的时效性分析.md",
        PAGES_DIR / "宋襄公之仁：道义与成功冲突时的决策框架.md",
        PAGES_DIR / "宋襄公之仁完整方法论：道义与成功冲突五决策点礼的时效性与何时该坚持原则.md",
        PAGES_DIR / "宋襄公之仁.md",
    ]
    groups.append(("宋襄公之仁", [f for f in g6 if f.exists()]))

    # 向戌弭兵 (5个)
    g7 = [
        PAGES_DIR / "向戌弭兵——14国和会的操盘方法.md",
        PAGES_DIR / "向戌弭兵14国和会：小国主导多边和平谈判七原则与穿梭外交方法论.md",
        PAGES_DIR / "向戌弭兵完整方法论：14国和会五步操盘七原则小国主导大国谈判与穿梭外交.md",
        PAGES_DIR / "向戌弭兵：小国主导大国和平谈判七原则.md",
        PAGES_DIR / "向戌弭兵.md",
    ]
    groups.append(("向戌弭兵", [f for f in g7 if f.exists()]))

    # 司马谈 (5个) - 司马谈.md 是人物页保持，其余合并
    # 六家论 和 临终嘱托 是不同主题，保持各自独立，但合并近似版本
    g8a = [
        PAGES_DIR / "司马谈论六家要指.md",
        PAGES_DIR / "司马谈论六家要旨.md",
        PAGES_DIR / "司马谈六家论.md",
    ]
    groups.append(("司马谈六家论", [f for f in g8a if f.exists()]))
    # 司马谈临终嘱托与史记使命.md 保持独立（唯一版本）
    # 司马谈.md 保持独立（人物页）

    # === 中优先级 ===

    # 功臣世家/功臣家族 (6个合并)
    g9 = [
        PAGES_DIR / "功臣家族传承三代方法论：百年存五的规律分析与六策防衰完整操作.md",
        PAGES_DIR / "功臣家族传代魔咒完整方法论：周勃周亚夫父子七步预防高位低实力与皇帝信号识别.md",
        PAGES_DIR / "功臣家族传代七步防魔咒：周勃周亚夫父子下狱的结构性根源与预防方法论.md",
        PAGES_DIR / "功臣世家传代策略.md",
        PAGES_DIR / "功臣世家传代魔咒：周勃周亚夫父子七步预防法.md",
        PAGES_DIR / "功臣世家的传代困境.md",
    ]
    groups.append(("功臣世家传代", [f for f in g9 if f.exists()]))

    # 存二王之后 (4个)
    g10 = [
        PAGES_DIR / "存二王之后的制度.md",
        PAGES_DIR / "存二王之后的周初制度.md",
        PAGES_DIR / "存二王之后：封前朝后裔六原则与怀柔政治合法性建构.md",
        PAGES_DIR / "存二王之后六原则：封前朝后裔的礼制怀柔与两千年制度传承方法论.md",
    ]
    groups.append(("存二王之后", [f for f in g10 if f.exists()]))

    # 存亡国 (4个)
    g11 = [
        PAGES_DIR / "存亡国延续与并购整合方法.md",
        PAGES_DIR / "存亡国整合完整方法论：微子封宋754年七原则六步实施并购整合与文化清洗对比.md",
        PAGES_DIR / "存亡国之后裔——商人在宋的延续.md",
        PAGES_DIR / "存亡国之后裔.md",
    ]
    groups.append(("存亡国", [f for f in g11 if f.exists()]))

    # 周公三诰 (3个)
    g12 = [
        PAGES_DIR / "周公三诰模式：新任领导者入职三文件治理方法论与五步实施清单.md",
        PAGES_DIR / "周公三诰完整方法论：建国入职三文件总纲禁令榜样五步实施与新任领导者治理清单.md",
        PAGES_DIR / "周公三诰：新任领导者入职文件治理方法.md",
    ]
    groups.append(("周公三诰", [f for f in g12 if f.exists()]))

    # 鲍叔 (5个) - 鲍叔牙.md 是人物页保持，其余合并
    g13 = [
        PAGES_DIR / "鲍叔识人完整方法论：透过失败看本质五步法系统性约束分析与三大决策点.md",
        PAGES_DIR / "鲍叔式人才识别方法.md",
        PAGES_DIR / "鲍叔式人才识别：透过失败看本质的五步法.md",
        PAGES_DIR / "鲍叔知管仲：透过失败理解动机的识人五步法与系统性约束分析框架.md",
    ]
    groups.append(("鲍叔识人", [f for f in g13 if f.exists()]))

    return groups


def main():
    groups = get_groups()
    for group_name, files in groups:
        valid = [f for f in files if f.exists()]
        if len(valid) >= 2:
            process_group(group_name, valid)
        elif len(valid) == 1:
            print(f"\n[跳过] {group_name}：只剩1个文件 {valid[0].name}")
        else:
            print(f"\n[跳过] {group_name}：文件不存在")

    print(f"\n{'='*50}")
    print(f"完成！共处理 {total_groups} 组")
    print(f"删除冗余页面: {total_deleted} 个")
    print(f"保留页面: {total_kept} 个")


if __name__ == "__main__":
    main()
