#!/usr/bin/env python3
"""
batch_find_portraits.py - Search Wikimedia Commons for portrait images of historical Chinese figures.
Downloads 400px thumbnails to /tmp/portrait_candidates/ for review.
Outputs JSON report to /tmp/portrait_report.json.
"""

import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# Output directories
CANDIDATE_DIR = Path("/tmp/portrait_candidates")
CANDIDATE_DIR.mkdir(exist_ok=True)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"

PERSONS = [
    ("秦始皇", ["Qin Shi Huang portrait", "First Emperor Qin portrait"]),
    ("黄帝", ["Yellow Emperor portrait China", "Huangdi portrait"]),
    ("尧", ["Emperor Yao portrait China", "Yao emperor portrait"]),
    ("周文王", ["King Wen Zhou portrait", "King Wen of Zhou"]),
    ("周武王", ["King Wu Zhou portrait", "King Wu of Zhou"]),
    ("吕尚", ["Jiang Ziya portrait", "Taigong Wang portrait"]),
    ("管仲", ["Guan Zhong portrait", "Guanzi portrait"]),
    ("伍子胥", ["Wu Zixu portrait"]),
    ("蔺相如", ["Lin Xiangru portrait"]),
    ("廉颇", ["Lian Po portrait"]),
    ("萧何", ["Xiao He portrait Han dynasty"]),
    ("李斯", ["Li Si portrait Qin"]),
    ("彭越", ["Peng Yue portrait Han"]),
    ("卫青", ["Wei Qing portrait Han"]),
    ("汉景帝", ["Emperor Jing Han portrait", "Liu Qi Han emperor"]),
    ("赵高", ["Zhao Gao portrait Qin"]),
    ("晋文公", ["Duke Wen Jin portrait", "Chong Er Jin"]),
    ("秦昭襄王", ["King Zhaoxiang Qin portrait", "Qin Zhaoxiang"]),
    ("秦缪公", ["Duke Mu Qin portrait", "Qin Mu Gong"]),
    ("楚怀王", ["King Huai Chu portrait", "Chu Huaiwang"]),
    ("周勃", ["Zhou Bo portrait Han"]),
    ("樊哙", ["Fan Kuai portrait Han"]),
    ("灌婴", ["Guan Ying portrait Han"]),
    ("项梁", ["Xiang Liang portrait"]),
    ("袁盎", ["Yuan Ang portrait Han"]),
]

# Also search for the "Portraits of Famous Men" Philadelphia series
PFAM_SEARCHES = [
    ("汉景帝", "Portraits of Famous Men Liu Qi"),
    ("秦始皇", "Portraits of Famous Men Qin Shi Huang"),
    ("萧何", "Portraits of Famous Men Xiao He"),
    ("周勃", "Portraits of Famous Men Zhou Bo"),
    ("樊哙", "Portraits of Famous Men Fan Kuai"),
    ("灌婴", "Portraits of Famous Men Guan Ying"),
    ("彭越", "Portraits of Famous Men Peng Yue"),
    ("赵高", "Portraits of Famous Men Zhao Gao"),
]


def api_get(params):
    params["format"] = "json"
    url = COMMONS_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "ShijiKB/1.0 (portrait research; baojie@gmail.com)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  API error: {e}")
        return None


def search_commons(query, limit=5):
    """Search Wikimedia Commons for files matching query."""
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


def get_image_info(title, width=400):
    """Get image URL and metadata for a file title."""
    data = api_get({
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|mime",
        "iiurlwidth": str(width),
    })
    if not data:
        return None
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info_list = page.get("imageinfo", [])
        if info_list:
            return info_list[0]
    return None


def is_likely_portrait(title, info):
    """Heuristic check: is this likely a portrait image (not a map, statue, or text)?"""
    title_lower = title.lower()
    # Reject obvious non-portraits
    bad_keywords = ["map", "coin", "seal", "temple", "tomb", "inscription",
                    "monument", "ruins", "landscape", "flag", "character",
                    "calligraphy", "bronze", "jade", "terracotta"]
    for kw in bad_keywords:
        if kw in title_lower:
            return False
    # Check dimensions
    w = info.get("width", 0)
    h = info.get("height", 0)
    if w < 100 or h < 100:
        return False
    return True


def get_license(info):
    """Extract license from extmetadata."""
    meta = info.get("extmetadata", {})
    license_short = meta.get("LicenseShortName", {}).get("value", "")
    license_url = meta.get("LicenseUrl", {}).get("value", "")
    if not license_short:
        license_short = meta.get("License", {}).get("value", "unknown")
    return license_short, license_url


def download_thumb(url, dest_path):
    """Download image from URL to dest_path."""
    req = urllib.request.Request(url, headers={"User-Agent": "ShijiKB/1.0 (portrait research; baojie@gmail.com)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  Download error: {e}")
        return False


def find_best_portrait(chinese_name, search_queries):
    """Try multiple search queries, return best candidate."""
    candidates = []
    for query in search_queries:
        print(f"  Searching: {query!r}")
        results = search_commons(query, limit=8)
        for result in results:
            title = result["title"]
            # Skip non-image types
            mime_ok = any(title.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".tiff", ".tif"])
            if not mime_ok:
                continue
            info = get_image_info(title, width=400)
            if not info:
                continue
            if not is_likely_portrait(title, info):
                continue
            lic, lic_url = get_license(info)
            # Prefer PD or old licenses
            is_free = any(kw in lic.lower() for kw in ["pd", "public domain", "cc0", "cc-by", "cc by"])
            candidates.append({
                "title": title,
                "thumb_url": info.get("thumburl", info.get("url", "")),
                "full_url": info.get("url", ""),
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "license": lic,
                "license_url": lic_url,
                "is_free": is_free,
                "commons_page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
                "snippet": result.get("snippet", ""),
            })
            time.sleep(0.3)
        if candidates:
            break  # Stop at first query that yields results
        time.sleep(0.5)

    if not candidates:
        return None
    # Prefer free licenses, then larger images
    candidates.sort(key=lambda x: (not x["is_free"], -(x["width"] * x["height"])))
    return candidates[0]


def main():
    report = []
    all_queries = list(PERSONS)
    # Add PFAM searches for persons already in list
    pfam_map = {name: q for name, q in PFAM_SEARCHES}

    for chinese_name, queries in all_queries:
        print(f"\n=== {chinese_name} ===")
        # Add PFAM search as first option if available
        if chinese_name in pfam_map:
            queries = [pfam_map[chinese_name]] + queries

        best = find_best_portrait(chinese_name, queries)
        if not best:
            print(f"  No portrait found for {chinese_name}")
            report.append({
                "person": chinese_name,
                "found": False,
                "found_url": None,
                "commons_page": None,
                "license": None,
                "dimensions": None,
                "local_thumb": None,
            })
            continue

        print(f"  Found: {best['title']}")
        print(f"  License: {best['license']} | Size: {best['width']}x{best['height']}")
        print(f"  URL: {best['commons_page']}")

        # Download thumbnail
        thumb_path = CANDIDATE_DIR / f"{chinese_name}.jpg"
        if best["thumb_url"]:
            ok = download_thumb(best["thumb_url"], str(thumb_path))
            local_thumb = str(thumb_path) if ok else None
        else:
            local_thumb = None

        report.append({
            "person": chinese_name,
            "found": True,
            "file_title": best["title"],
            "found_url": best["full_url"],
            "thumb_url": best["thumb_url"],
            "commons_page": best["commons_page"],
            "license": best["license"],
            "is_free": best["is_free"],
            "dimensions": f"{best['width']}x{best['height']}",
            "local_thumb": local_thumb,
            "snippet": best["snippet"][:100] if best["snippet"] else "",
        })

    # Write report
    report_path = "/tmp/portrait_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n\nReport saved to {report_path}")
    found = [r for r in report if r["found"]]
    print(f"Found portraits: {len(found)}/{len(report)}")
    for r in found:
        print(f"  {r['person']}: {r['license']} | {r['dimensions']} | {r['commons_page']}")

    not_found = [r for r in report if not r["found"]]
    if not_found:
        print(f"\nNot found ({len(not_found)}):")
        for r in not_found:
            print(f"  {r['person']}")


if __name__ == "__main__":
    main()
