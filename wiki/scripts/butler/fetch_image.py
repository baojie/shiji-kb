#!/usr/bin/env python3
"""
fetch_image.py — 为首页精品页搜索并下载 Wikimedia Commons 配图。

用法:
    python3 wiki/scripts/butler/fetch_image.py <slug> [--label 标签] [--type 类型]
    python3 wiki/scripts/butler/fetch_image.py <slug> --dry-run

输出 JSON 到 stdout:
    {"found": true, "file": "images/xxx.jpg", "source": "...", "license": "...",
     "caption": "...", "credit": "..."}
    {"found": false, "prompt": "AI绘图提示词"}
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent  # shiji-kb/
IMGS = ROOT / "wiki/public/images"
PAGES_DIR = ROOT / "wiki/public/pages"
SOURCES_JSON = IMGS / "sources.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
UA = "ShijiKB/1.0 (butler image fetch; baojie@gmail.com)"

# 类型 → Wikimedia 搜索策略
TYPE_QUERY_TEMPLATES = {
    "person": [
        "{label} portrait China ancient",
        "{label_en} portrait ancient Chinese",
        "{label} 画像",
    ],
    "story": [
        "{label} ancient China historical painting",
        "{label_en} China history painting",
    ],
    "overview": [
        "{label} ancient China map painting",
        "{label_en} China history ancient",
    ],
    "sanwen": [
        "{label_en} China ancient calligraphy text",
        "{label} China ancient",
    ],
    "chapter": [
        "{label} ancient China painting",
        "{label_en} China ancient history",
    ],
    "concept": [
        "{label_en} ancient China illustration",
        "{label} China ancient",
    ],
}

# 人名常用英译（补充词表）
PERSON_EN = {
    "刘邦": "Liu Bang Emperor Gaozu Han",
    "项羽": "Xiang Yu Chu overlord",
    "韩信": "Han Xin general Han dynasty",
    "张良": "Zhang Liang strategist Han",
    "萧何": "Xiao He minister Han",
    "陈平": "Chen Ping advisor Han",
    "吕后": "Empress Lü Zhi Han",
    "秦始皇": "Qin Shi Huang First Emperor",
    "汉武帝": "Emperor Wu Han dynasty",
    "汉文帝": "Emperor Wen Han dynasty",
    "汉景帝": "Emperor Jing Han dynasty Liu Qi",
    "司马迁": "Sima Qian historian Han",
    "屈原": "Qu Yuan poet Chu",
    "管仲": "Guan Zhong Qi statesman",
    "伍子胥": "Wu Zixu Wu kingdom",
    "廉颇": "Lian Po Zhao general",
    "蔺相如": "Lin Xiangru Zhao diplomat",
    "白起": "Bai Qi Qin general",
    "范雎": "Fan Ju Qin minister",
    "吕不韦": "Lü Buwei Qin chancellor",
    "赵高": "Zhao Gao Qin eunuch",
    "李斯": "Li Si Qin minister",
    "蒙恬": "Meng Tian Qin general",
    "黄帝": "Yellow Emperor Huangdi",
    "尧": "Emperor Yao ancient China",
    "舜": "Emperor Shun ancient China",
    "大禹": "Yu the Great flood control",
    "周文王": "King Wen of Zhou",
    "周武王": "King Wu of Zhou",
    "伯夷": "Bo Yi recluse Zhou",
    "晋文公": "Duke Wen Jin Chong Er",
    "勾践": "Goujian King Yue",
    "夫差": "Fuchai King Wu",
    "范蠡": "Fan Li Yue statesman",
    "西施": "Xi Shi beauty Yue",
    "卫青": "Wei Qing Han general",
    "霍去病": "Huo Qubing Han general",
    "项梁": "Xiang Liang Chu general",
    "彭越": "Peng Yue Han general",
    "英布": "Ying Bu king Han",
    "周勃": "Zhou Bo Han general",
    "灌婴": "Guan Ying Han general",
    "樊哙": "Fan Kuai Han general",
    "袁盎": "Yuan Ang Han official",
    "晁错": "Chao Cuo Han legalist",
    "二世皇帝": "Huhai Second Emperor Qin dynasty",
    "秦昭襄王": "King Zhaoxiang Qin",
    "楚怀王": "King Huai Chu kingdom",
    "彭越": "Peng Yue Han general king Liang",
    "项梁": "Xiang Liang Chu general",
    "公孙弘": "Gongsun Hong Han chancellor",
    "赵高": "Zhao Gao Qin eunuch",
    "李斯": "Li Si Qin chancellor",
    "商鞅": "Shang Yang Qin reformer",
    "卢绾": "Lu Wan Han king Yan",
    "后稷": "Houji Lord Millet Zhou ancestor",
    "刘濞": "Liu Pi king Wu",
    "宣太后": "Queen Dowager Xuan Mi Bazi Qin regent",
    "窦太后": "Empress Dowager Dou Han Wendi mother",
    "薄太后": "Empress Dowager Bo Han Wendi mother",
    "戚夫人": "Lady Qi Liu Bang concubine",
    "郑袖": "Zheng Xiu King Huai Chu consort",
    "鲁元公主": "Princess Luyuan Liu Bang daughter",
    "卓文君": "Zhuo Wenjun talented woman Han",
    "慎夫人": "Lady Shen Han Wendi concubine",
    "武姜": "Wu Jiang Zheng state mother",
    "刘嫖": "Princess Guantao Liu Piao Han",
}

# 地图/战役相关词
TOPIC_EN = {
    "楚汉战争": "Chu Han contention war map",
    "鸿门宴": "Hongmen banquet Xiang Yu Liu Bang",
    "垓下之战": "Battle of Gaixia Xiang Yu",
    "长平之战": "Battle of Changping Qin Zhao",
    "战国七雄": "Warring States seven kingdoms map",
    "秦朝": "Qin dynasty empire map",
    "汉朝": "Han dynasty empire map",
    "春秋": "Spring Autumn period map China",
    "七国之乱": "Rebellion of Seven States Han",
    "三家分晋": "Partition of Jin three kingdoms",
    "商鞅变法": "Shang Yang reform Qin",
}

# "Portraits of Famous Men" 费城博物馆系列 — 仅收录已确认存在的 Commons 文件名
# 来源: scripts/batch_portraits.py（已实际下载成功的条目）
PFAM_FILES = {
    "黄帝":  "Portraits_of_Famous_Men_-_Yellow_Emperor_(Huangdi).jpg",
    "周文王": "Portraits_of_Famous_Men_-_King_Wen_of_Zhou.jpg",
    "周武王": "Portraits_of_Famous_Men_-_King_Wu_of_Zhou.jpg",
    "姬旦":  "Portraits_of_Famous_Men_-_Zhou_Gong.jpg",
    "汉景帝": "Portraits_of_Famous_Men_-_Liu_Qi.jpg",
    "屈原":  "Portraits_of_Famous_Men_-_Qu_Yuan.jpg",
    "帝喾":  "Portraits_of_Famous_Men_-_Emperor_Ku.jpg",
    "舜":   "Portraits_of_Famous_Men_-_Emperor_Shun.jpg",
    "大禹":  "Portraits_of_Famous_Men_-_Da_Yu.jpg",
}

# 直接已知 Commons 文件名（PFAM以外）— 已确认存在
KNOWN_FILES = {
    "尧":   "Ma_Lin_-_Emperor_Yao.jpg",
    "管仲":  "Guan_Zhong.png",
}

# 不合适的图片关键词（拒绝）
BAD_TITLE_KW = [
    "coin", "seal", "ruins", "temple", "tomb", "inscription",
    "calligraphy", "bronze", "jade", "flag", "character", "map_",
    "monument", "landscape", "terracotta",
]


def api_get(params):
    params["format"] = "json"
    url = COMMONS_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[fetch_image] API error: {e}", file=sys.stderr)
        return None


def search_commons(query, limit=8):
    data = api_get({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": "6",
        "srlimit": str(limit),
    })
    if not data:
        return []
    return data.get("query", {}).get("search", [])


def get_image_info(title, width=600):
    data = api_get({
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|mime",
        "iiurlwidth": str(width),
    })
    if not data:
        return None
    for page in data.get("query", {}).get("pages", {}).values():
        infos = page.get("imageinfo", [])
        if infos:
            return infos[0]
    return None


def is_acceptable(title, query=""):
    t = title.lower()
    if not any(t.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif"]):
        return False
    for kw in BAD_TITLE_KW:
        if kw in t:
            return False
    # 要求标题与查询词有实质重叠（至少一个单词匹配），防止误匹配
    if query:
        query_words = set(w.lower() for w in query.split() if len(w) > 2)
        title_words = set(re.split(r'[\W_]+', t))
        if not query_words & title_words:
            return False
    return True


def get_license(info):
    meta = info.get("extmetadata", {})
    lic = meta.get("LicenseShortName", {}).get("value", "")
    if not lic:
        lic = meta.get("License", {}).get("value", "unknown")
    lic_url = meta.get("LicenseUrl", {}).get("value", "")
    return lic, lic_url


def get_description(info):
    meta = info.get("extmetadata", {})
    desc = meta.get("ImageDescription", {}).get("value", "")
    # strip HTML tags
    desc = re.sub(r"<[^>]+>", "", desc).strip()
    return desc[:200] if desc else ""


def download_image(url, dest_path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        dest_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"[fetch_image] download error: {e}", file=sys.stderr)
        return False


def build_queries(slug, label, page_type):
    label_en = PERSON_EN.get(label, "") or TOPIC_EN.get(label, "")
    templates = TYPE_QUERY_TEMPLATES.get(page_type, TYPE_QUERY_TEMPLATES["overview"])
    queries = []
    for tmpl in templates:
        q = tmpl.format(label=label, label_en=label_en or label)
        queries.append(q)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            result.append(q)
    return result


def try_known_file(label):
    """直接查询已知 Commons 文件名（PFAM 系列优先），跳过全文搜索。"""
    fname = PFAM_FILES.get(label) or KNOWN_FILES.get(label)
    if not fname:
        return None
    title = f"File:{fname}"
    print(f"[fetch_image] trying known file: {title}", file=sys.stderr)
    info = get_image_info(title, width=600)
    if not info:
        return None
    w = info.get("width", 0)
    h = info.get("height", 0)
    if w < 100 or h < 100:
        return None
    lic, lic_url = get_license(info)
    is_free = any(kw in lic.lower() for kw in
                  ["pd", "public domain", "cc0", "cc-by", "cc by"])
    return {
        "title": title,
        "thumb_url": info.get("thumburl", info.get("url", "")),
        "full_url": info.get("url", ""),
        "width": w,
        "height": h,
        "license": lic,
        "license_url": lic_url,
        "is_free": is_free,
        "description": get_description(info),
        "commons_page": "https://commons.wikimedia.org/wiki/"
                        + urllib.parse.quote(title.replace(" ", "_")),
    }


def find_best_image(queries):
    candidates = []
    for query in queries:
        print(f"[fetch_image] searching: {query!r}", file=sys.stderr)
        results = search_commons(query, limit=8)
        for r in results:
            title = r["title"]
            if not is_acceptable(title, query):
                continue
            info = get_image_info(title, width=600)
            if not info:
                continue
            w = info.get("width", 0)
            h = info.get("height", 0)
            if w < 150 or h < 150:
                continue
            lic, lic_url = get_license(info)
            is_free = any(kw in lic.lower() for kw in
                          ["pd", "public domain", "cc0", "cc-by", "cc by"])
            candidates.append({
                "title": title,
                "thumb_url": info.get("thumburl", info.get("url", "")),
                "full_url": info.get("url", ""),
                "width": w,
                "height": h,
                "license": lic,
                "license_url": lic_url,
                "is_free": is_free,
                "description": get_description(info),
                "commons_page": "https://commons.wikimedia.org/wiki/"
                                + urllib.parse.quote(title.replace(" ", "_")),
            })
            time.sleep(0.3)
        if candidates:
            break
        time.sleep(0.5)

    if not candidates:
        return None
    candidates.sort(key=lambda x: (not x["is_free"], -(x["width"] * x["height"])))
    return candidates[0]


def update_sources(file_name, source_url, license_str, description):
    if SOURCES_JSON.exists():
        sources = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    else:
        sources = []
    existing = {s["file"] for s in sources}
    if file_name not in existing:
        sources.append({
            "file": file_name,
            "source": source_url,
            "license": license_str,
            "description": description,
        })
        SOURCES_JSON.write_text(
            json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# ── 朝代 → 绘画风格对照表 ─────────────────────────────────────────────────────
# 史记时间跨度：上古传说（黄帝）→ 西汉武帝，跨越约2000年
DYNASTY_STYLES = {
    "legendary": (
        "archaic Chinese mythological illustration, Chu Ci (楚辞) manuscript style, "
        "Warring States lacquerware aesthetic, swirling cloud motifs, vermillion and black pigments, "
        "pre-Qin ancient imagery"
    ),
    "shang": (
        "Shang dynasty oracle bone and bronze vessel aesthetic, taotie (饕餮) mask motifs, "
        "ritual bronze ding composition, ancient Chinese pictograph influence, "
        "earth tones and patinated bronze green"
    ),
    "zhou_spring_autumn": (
        "Spring and Autumn period lacquerware painting style, flowing curvilinear patterns, "
        "Zhou bronze vessel decorative aesthetic, Chu silk manuscript style, "
        "black lacquer and vermillion, elegant line work"
    ),
    "warring_states": (
        "Warring States period Chinese painting style, Mawangdui proto-silk painting aesthetic, "
        "dynamic warrior compositions, Chu kingdom lacquer painting, "
        "bold brushwork, black and red palette with accents of gold"
    ),
    "qin": (
        "Qin dynasty monumental mural style, austere and powerful composition, "
        "terracotta army aesthetic, unified empire imagery, "
        "mineral pigments on stone, imposing architectural backdrop"
    ),
    "han": (
        "Han dynasty tomb mural painting style, Mawangdui silk painting aesthetic, "
        "bold confident brushwork, mineral pigments (cinnabar red, azurite blue, malachite green), "
        "dynamic figure compositions, cloud scroll borders"
    ),
}

# 章节 → 朝代键值映射（史记130篇分期）
CHAPTER_DYNASTY = {
    # 上古传说
    "001_五帝本纪": "legendary",
    "002_夏本纪": "legendary",
    "003_殷本纪": "shang",
    "004_周本纪": "zhou_spring_autumn",
    "013_三代世表": "shang",
    "014_十二诸侯年表": "zhou_spring_autumn",
    # 春秋
    "032_齐太公世家": "zhou_spring_autumn",
    "033_鲁周公世家": "zhou_spring_autumn",
    "034_燕召公世家": "zhou_spring_autumn",
    "035_管蔡世家": "zhou_spring_autumn",
    "036_陈杞世家": "zhou_spring_autumn",
    "037_卫康叔世家": "zhou_spring_autumn",
    "038_宋微子世家": "zhou_spring_autumn",
    "039_晋世家": "zhou_spring_autumn",
    "040_楚世家": "zhou_spring_autumn",
    "041_越王勾践世家": "zhou_spring_autumn",
    "042_郑世家": "zhou_spring_autumn",
    "043_赵世家": "warring_states",
    "044_魏世家": "warring_states",
    "045_韩世家": "warring_states",
    "015_六国年表": "warring_states",
    "069_苏秦列传": "warring_states",
    "070_张仪列传": "warring_states",
    "071_樗里子甘茂列传": "warring_states",
    "072_穰侯列传": "warring_states",
    "073_白起王翦列传": "warring_states",
    "074_孟子荀卿列传": "warring_states",
    "075_孟尝君列传": "warring_states",
    "076_平原君虞卿列传": "warring_states",
    "077_魏公子列传": "warring_states",
    "078_春申君列传": "warring_states",
    "079_范雎蔡泽列传": "warring_states",
    "080_乐毅列传": "warring_states",
    "081_廉颇蔺相如列传": "warring_states",
    "082_田单列传": "warring_states",
    "083_鲁仲连邹阳列传": "warring_states",
    "084_屈原贾生列传": "warring_states",
    "085_吕不韦列传": "warring_states",
    "086_刺客列传": "warring_states",
    "087_李斯列传": "qin",
    # 秦
    "005_秦本纪": "warring_states",
    "006_秦始皇本纪": "qin",
    "016_秦楚之际月表": "qin",
    # 楚汉/西汉
    "007_项羽本纪": "han",
    "008_高祖本纪": "han",
    "009_吕太后本纪": "han",
    "010_孝文本纪": "han",
    "011_孝景本纪": "han",
    "012_孝武本纪": "han",
}

# slug/label关键词 → 朝代
LABEL_DYNASTY_HINTS = {
    "legendary": ["黄帝", "炎帝", "尧", "舜", "禹", "大禹", "后稷", "契", "皋陶",
                  "帝喾", "帝挚", "颛顼", "少昊", "蚩尤", "后羿", "嫦娥",
                  "伏羲", "神农", "女娲"],
    "shang":     ["商", "殷", "汤", "纣", "武丁", "盘庚", "太甲", "伊尹",
                  "妲己", "比干", "微子", "箕子"],
    "zhou_spring_autumn": ["周", "文王", "武王", "周公", "管仲", "齐桓公",
                            "晋文公", "宋襄公", "秦穆公", "楚庄王", "吴王", "越王",
                            "勾践", "夫差", "伍子胥", "范蠡", "西施", "孔子",
                            "老子", "孟子"],
    "warring_states": ["战国", "商鞅", "苏秦", "张仪", "廉颇", "蔺相如",
                       "白起", "范雎", "吕不韦", "荆轲", "屈原", "信陵君",
                       "平原君", "孟尝君", "春申君", "赵武灵王", "秦昭王"],
    "qin":       ["秦始皇", "二世", "李斯", "赵高", "蒙恬", "章邯", "秦朝", "秦帝"],
    "han":       ["刘邦", "项羽", "吕后", "汉武帝", "汉文帝", "汉景帝",
                  "韩信", "张良", "萧何", "陈平", "樊哙", "卫青", "霍去病",
                  "司马迁", "汉", "高祖", "太后"],
}


def detect_dynasty(label, sources=None, summary="", tags=None):
    """根据label、sources章节、summary推断朝代键。"""
    sources = sources or []
    tags = tags or []

    # 1. 先从章节号推断（最可靠）
    chapter_votes = {}
    for src in sources:
        for chap_key, dynasty in CHAPTER_DYNASTY.items():
            if chap_key in src or src in chap_key:
                chapter_votes[dynasty] = chapter_votes.get(dynasty, 0) + 1
    if chapter_votes:
        return max(chapter_votes, key=chapter_votes.get)

    # 2. 从label/slug关键词匹配
    for dynasty, keywords in LABEL_DYNASTY_HINTS.items():
        for kw in keywords:
            if kw in label:
                return dynasty

    # 3. 从summary关键词匹配
    summary_lower = summary.lower()
    dynasty_summary_kw = {
        "legendary": ["五帝", "上古", "远古", "传说", "神话", "三皇"],
        "shang":     ["商朝", "殷商", "商代"],
        "zhou_spring_autumn": ["春秋", "西周", "东周", "诸侯"],
        "warring_states": ["战国", "七雄", "合纵", "连横"],
        "qin":       ["秦朝", "秦代", "始皇", "统一六国"],
        "han":       ["汉朝", "汉代", "西汉", "刘氏"],
    }
    for dynasty, kws in dynasty_summary_kw.items():
        if any(kw in summary for kw in kws):
            return dynasty

    # 默认：汉代（史记主体时代）
    return "han"


def build_ai_prompt(slug, label, page_type, page_summary="", sources=None, tags=None):
    """生成 AI 绘图提示词，按所属朝代使用对应绘画风格。"""
    dynasty = detect_dynasty(label, sources=sources, summary=page_summary, tags=tags)
    style = DYNASTY_STYLES.get(dynasty, DYNASTY_STYLES["han"])
    label_en = PERSON_EN.get(label, label)

    # 判断是否为女性人物
    FEMALE_MARKERS = ["太后", "夫人", "公主", "姬", "妃", "皇后", "王后", "女"]
    is_female = any(m in label for m in FEMALE_MARKERS)

    if page_type == "person":
        if is_female:
            attire = "elegant court robes, noblewoman attire appropriate to period, dignified bearing"
        else:
            attire = "official robes or armor appropriate to period, dignified pose"
        prompt = (
            f"Portrait of {label_en} ({label}), ancient Chinese historical figure. "
            f"{style}, {attire}, "
            f"neutral background, high quality, museum artwork"
        )
    elif page_type == "story":
        prompt = (
            f"Historical scene: {label_en} ({label}), ancient China. "
            f"{style}, dramatic composition, multiple figures, narrative scene, "
            f"high quality illustration"
        )
    elif page_type in ("overview", "concept"):
        prompt = (
            f"Ancient China: {label_en} ({label}). "
            f"{style}, landscape or symbolic composition, high quality"
        )
    elif page_type == "sanwen":
        prompt = (
            f"Ancient Chinese historical scene related to {label_en} ({label}). "
            f"{style}, elegant composition, scholarly atmosphere"
        )
    else:
        prompt = (
            f"Ancient China historical illustration: {label_en} ({label}). "
            f"{style}, high quality"
        )
    if page_summary:
        prompt += f". Context: {page_summary[:100]}"
    return prompt


def read_page_meta(slug):
    """读取页面 frontmatter，返回 {label, type, image, summary, sources, tags}。"""
    page_path = PAGES_DIR / f"{slug}.md"
    if not page_path.exists():
        return {}
    text = page_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm_text = m.group(1)
    result = {}
    for key in ("label", "type", "image"):
        km = re.search(rf"^{key}:\s*(.+)$", fm_text, re.MULTILINE)
        if km:
            result[key] = km.group(1).strip().strip('"\'')
    # sources: [秦始皇本纪, 高祖本纪, ...]
    sm = re.search(r"^sources:\s*\[(.+?)\]", fm_text, re.MULTILINE)
    if sm:
        result["sources"] = [s.strip().strip('"\'') for s in sm.group(1).split(",")]
    else:
        result["sources"] = []
    # tags: [史记人物, 帝王, ...]
    tm = re.search(r"^tags:\s*\[(.+?)\]", fm_text, re.MULTILINE)
    if tm:
        result["tags"] = [t.strip().strip('"\'') for t in tm.group(1).split(",")]
    else:
        result["tags"] = []
    # 取首段作摘要
    body = text[m.end():].strip()
    for line in body.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---"):
            result["summary"] = line[:150]
            break
    return result


def main():
    ap = argparse.ArgumentParser(description="Fetch Wikimedia image for a wiki page.")
    ap.add_argument("slug", help="Page slug (e.g. 韩信)")
    ap.add_argument("--label", help="Display label (defaults to slug)")
    ap.add_argument("--type", dest="page_type", help="Page type (person/story/...)")
    ap.add_argument("--dry-run", action="store_true", help="Search only, no download")
    args = ap.parse_args()

    slug = args.slug
    meta = read_page_meta(slug)

    label = args.label or meta.get("label") or slug
    page_type = args.page_type or meta.get("type") or "person"

    # 已有图片则跳过
    if meta.get("image"):
        print(json.dumps({
            "found": True,
            "skipped": True,
            "reason": f"page already has image: {meta['image']}",
        }, ensure_ascii=False))
        return

    # 本地文件已存在（但页面尚未设置 image 字段）
    local_candidates = [
        (IMGS / f"{label}.jpg", f"images/{label}.jpg"),
        (IMGS / f"{slug}.jpg", f"images/{slug}.jpg"),
    ]
    for local_path, img_rel in local_candidates:
        if local_path.exists():
            print(f"[fetch_image] local file exists: {local_path}", file=sys.stderr)
            print(json.dumps({
                "found": True,
                "slug": slug,
                "file": img_rel,
                "source": "local",
                "license": "unknown",
                "caption": f"{label}画像",
                "credit": "本地已有文件",
                "local_existing": True,
            }, ensure_ascii=False))
            return

    # 优先尝试已知文件名（PFAM 系列 + 已知来源）
    best = try_known_file(label)

    if not best:
        queries = build_queries(slug, label, page_type)
        best = find_best_image(queries)

    if not best:
        prompt = build_ai_prompt(
            slug, label, page_type,
            page_summary=meta.get("summary", ""),
            sources=meta.get("sources", []),
            tags=meta.get("tags", []),
        )
        print(json.dumps({
            "found": False,
            "slug": slug,
            "label": label,
            "type": page_type,
            "prompt": prompt,
        }, ensure_ascii=False))
        return

    # 确定文件名
    file_name = f"{label}.jpg"
    dest_path = IMGS / file_name
    img_rel = f"images/{file_name}"

    if dest_path.exists():
        print(f"[fetch_image] image file already exists: {dest_path}", file=sys.stderr)
    elif not args.dry_run:
        url = best["thumb_url"] or best["full_url"]
        ok = download_image(url, dest_path)
        if not ok:
            prompt = build_ai_prompt(slug, label, page_type, meta.get("summary", ""))
            print(json.dumps({"found": False, "slug": slug, "prompt": prompt},
                             ensure_ascii=False))
            return
        update_sources(file_name, best["commons_page"], best["license"],
                       best["description"] or f"Wikimedia Commons: {best['title']}")
        print(f"[fetch_image] downloaded → {dest_path}", file=sys.stderr)

    caption = best["description"] or f"{label}，来源：Wikimedia Commons"
    if len(caption) > 80:
        caption = caption[:77] + "..."
    credit = f"Wikimedia Commons / {best['license']}"

    result = {
        "found": True,
        "slug": slug,
        "file": img_rel,
        "source": best["commons_page"],
        "license": best["license"],
        "caption": caption,
        "credit": credit,
        "dry_run": args.dry_run,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
