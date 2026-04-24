#!/usr/bin/env python3
"""
批量下载维基共享人物画像，裁切并更新页面 frontmatter。
用法: python3 scripts/batch_portraits.py [--dry-run]
"""
import argparse, json, pathlib, re, subprocess, sys, time, urllib.request

ROOT  = pathlib.Path(__file__).parent.parent
IMGS  = ROOT / "wiki/public/images"
PAGES = ROOT / "wiki/public/pages"

# person_label → (commons_filename, crop_spec, description, license)
# crop_spec: None = 自动（取下半段），或 "WxH+X+Y"
PORTRAITS = [
    # "Portraits of Famous Men" 系列（费城艺术博物馆，PD）
    ("黄帝",  "Portraits_of_Famous_Men_-_Yellow_Emperor_(Huangdi).jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    ("周文王", "Portraits_of_Famous_Men_-_King_Wen_of_Zhou.jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    ("周武王", "Portraits_of_Famous_Men_-_King_Wu_of_Zhou.jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    ("姬旦",  "Portraits_of_Famous_Men_-_Zhou_Gong.jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    ("汉景帝", "Portraits_of_Famous_Men_-_Liu_Qi.jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    ("屈原",  "Portraits_of_Famous_Men_-_Qu_Yuan.jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    ("帝喾",  "Portraits_of_Famous_Men_-_Emperor_Ku.jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    ("舜",   "Portraits_of_Famous_Men_-_Emperor_Shun.jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    ("大禹",  "Portraits_of_Famous_Men_-_Da_Yu.jpg", None,
     "费城艺术博物馆 Portraits of Famous Men，Simkhovitch Collection，19世纪–20世纪初", "PD"),
    # 独立来源
    ("尧",   "Ma_Lin_-_Emperor_Yao.jpg", "7890x5600+0+3000",
     "宋 马麟绘《帝尧像》，约1230年，绢本设色", "PD"),
    ("管仲",  "Guan_Zhong.png", "476x340+0+0",
     "管仲画像，来源不明，PD", "PD"),
]

BASE_URL = "https://upload.wikimedia.org/wikipedia/commons"

UA = "Mozilla/5.0 (compatible; ShijiKB/1.0; +https://github.com/baojie/shiji-kb)"

def get_orig_url(filename):
    api = (f"https://commons.wikimedia.org/w/api.php?action=query"
           f"&titles=File:{urllib.request.quote(filename)}"
           f"&prop=imageinfo&iiprop=url|size&format=json")
    req = urllib.request.Request(api, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    pages = data["query"]["pages"]
    p = list(pages.values())[0]
    ii = p["imageinfo"][0]
    return ii["url"], ii["width"], ii["height"]

def download(url, dest):
    subprocess.run(["wget", "-q", f"--user-agent={UA}", "-O", str(dest), url], check=True)

def auto_crop_series(orig_path, out_path, orig_w, orig_h):
    """Portraits of Famous Men 系列：面部约在图像 35–75% 高度处。
    取 y=orig_h*0.33 开始，高度 orig_h*0.42 的区域，全宽。"""
    y_start = int(orig_h * 0.33)
    height  = int(orig_h * 0.42)
    crop = f"{orig_w}x{height}+0+{y_start}"
    subprocess.run(["convert", str(orig_path),
                    "-crop", crop, "+repage",
                    "-resize", "400x>", "-quality", "85", str(out_path)], check=True)

def manual_crop(orig_path, out_path, crop_spec):
    subprocess.run(["convert", str(orig_path),
                    "-crop", crop_spec, "+repage",
                    "-resize", "400x>", "-quality", "85", str(out_path)], check=True)

def update_frontmatter(page_file, img_rel):
    text = page_file.read_text(encoding="utf-8")
    if "^image:" in text or re.search(r"^image:", text, re.MULTILINE):
        print(f"  [skip] {page_file.name} already has image:")
        return
    # insert after first '---' block opener
    new_text = re.sub(
        r"(^---\s*\n(?:.*\n)*?)(^---)",
        lambda m: m.group(1) + f"image: {img_rel}\n" + m.group(2),
        text, count=1, flags=re.MULTILINE
    )
    if new_text != text:
        page_file.write_text(new_text, encoding="utf-8")
        print(f"  [ok] added image: {img_rel} → {page_file.name}")
    else:
        print(f"  [warn] could not patch frontmatter: {page_file.name}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="only process this person")
    args = ap.parse_args()

    sources = json.loads((IMGS / "sources.json").read_text(encoding="utf-8"))
    existing_files = {s["file"] for s in sources}

    for label, fname, crop_spec, desc, lic in PORTRAITS:
        if args.only and label != args.only:
            continue
        out_file = IMGS / f"{label}.jpg"
        img_rel  = f"images/{label}.jpg"

        print(f"\n{'='*50}\n処理: {label} ← {fname}")

        # Find page
        page_files = list(PAGES.glob(f"**/{label}.md"))
        if not page_files:
            print(f"  [skip] no page for {label}")
            continue
        page_file = page_files[0]

        if out_file.exists():
            print(f"  [skip] image already exists: {out_file.name}")
        else:
            if args.dry_run:
                print(f"  [dry] would download + crop → {out_file.name}")
            else:
                print(f"  downloading original...")
                orig_url, orig_w, orig_h = get_orig_url(fname)
                print(f"  {orig_url} ({orig_w}x{orig_h})")
                orig_path = IMGS / f"_orig_{label}.tmp"
                download(orig_url, orig_path)
                print(f"  cropping...")
                if crop_spec:
                    manual_crop(orig_path, out_file, crop_spec)
                else:
                    auto_crop_series(orig_path, out_file, orig_w, orig_h)
                orig_path.unlink()
                result = subprocess.run(["identify", str(out_file)],
                                        capture_output=True, text=True)
                print(f"  result: {result.stdout.split()[2]}")

                # Update sources.json
                if f"{label}.jpg" not in existing_files:
                    sources.append({
                        "file": f"{label}.jpg",
                        "source": f"https://commons.wikimedia.org/wiki/File:{fname}",
                        "license": lic,
                        "description": desc,
                    })
                    (IMGS / "sources.json").write_text(
                        json.dumps(sources, ensure_ascii=False, indent=2),
                        encoding="utf-8")

                time.sleep(1)

        if not args.dry_run:
            update_frontmatter(page_file, img_rel)

    print("\n[done]")

if __name__ == "__main__":
    main()
