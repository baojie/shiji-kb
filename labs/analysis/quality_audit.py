#!/usr/bin/env python3
"""shiji-kb 全量页面质量审计脚本
生成 labs/analysis/quality_audit.csv（每页问题明细）
"""

import json, os, re, csv, sys
from collections import Counter, defaultdict

BASE = 'docs/wiki'
ROOT = '.'
REGISTRY = os.path.join(BASE, 'pages.json')

def load_registry():
    with open(REGISTRY) as f:
        return json.load(f)['pages']

def check_page(pid: str, info: dict, pages: dict) -> list[dict]:
    """Run all quality checks on a single page. Returns list of issues."""
    issues = []
    path = info.get('path', '')
    if not path:
        issues.append(dict(issue='NO_PATH', severity='critical', detail='registry entry has no path'))
        return issues

    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        issues.append(dict(issue='MISSING_FILE', severity='critical', detail=f'file not found on disk'))
        return issues

    try:
        with open(full) as f:
            content = f.read()
    except Exception as e:
        issues.append(dict(issue='READ_ERROR', severity='critical', detail=str(e)))
        return issues

    if not content.strip():
        issues.append(dict(issue='EMPTY_FILE', severity='critical', detail='file is empty'))
        return issues

    q = info.get('quality', '')
    t = info.get('type', '')
    score = info.get('quality_score', 0)
    k_score = info.get('k_score', 0)
    # Read description from file frontmatter (not registry)
    desc = ''
    fm_match = re.search(r'^description:\s*["\']?([^"\'\n]+)["\']?', content[:500], re.MULTILINE)
    if fm_match:
        desc = fm_match.group(1).strip()
    label = info.get('label', pid)

    # ── Category A: Content completeness ──
    lines = content.split('\n')

    # A1: Missing 史记引文 section (key feature)
    if '## 史记引文' not in content:
        issues.append(dict(issue='A1_NO_QUOTE_SECTION', severity='major',
                          detail='缺失「史记引文」章节'))

    # A2: Has 原文 section (should be in chapter pages only)
    if '## 原文' in content and t != 'chapter':
        issues.append(dict(issue='A2_RAW_TEXT_NONCHAPTER', severity='minor',
                          detail='非章节页面含有「原文」章节'))

    # A3: Content too short
    length = len(content)
    thresholds = {'stub': 0, 'basic': 200, 'standard': 1000, 'featured': 3000, 'premium': 5000}
    size_ok = length >= thresholds.get(q, 200)
    if not size_ok:
        issues.append(dict(issue='A3_CONTENT_TOO_SHORT', severity='major',
                          detail=f'质量{q}但仅{length}B，低于阈值{thresholds.get(q, 200)}B'))

    # A4: Missing TL;DR / summary for longer pages
    if length > 2000 and not content.startswith('>') and '## 摘要' not in content and '> ' not in content[:500]:
        issues.append(dict(issue='A4_MISSING_SUMMARY', severity='minor',
                          detail='长文（>2KB）缺摘要/引言区块'))

    # A5: No sections at all (just frontmatter + single paragraph)
    section_count = content.count('\n## ')
    if section_count == 0 and q not in ('stub', '') and t not in ('redirect', 'REDIRECT'):
        issues.append(dict(issue='A5_NO_SECTIONS', severity='major',
                          detail='仅有frontmatter和一段正文，无二级章节'))

    # ── Category B: Frontmatter metadata ──
    # B1: No description
    if not desc or len(desc) < 10:
        issues.append(dict(issue='B1_NO_DESCRIPTION', severity='major',
                          detail='缺失或过短（<10字）的描述'))
    elif '标注符号' in desc or '出现' in desc[:50]:
        issues.append(dict(issue='B2_AUTO_DESCRIPTION', severity='minor',
                          detail='自动生成的描述文本'))

    # B3: No tags
    if not info.get('tags'):
        issues.append(dict(issue='B3_NO_TAGS', severity='major',
                          detail='缺失tags标签'))

    # B4: No sources
    if not info.get('sources'):
        issues.append(dict(issue='B4_NO_SOURCES', severity='major',
                          detail='缺失sources来源引用'))

    # B5: No image (applicable to most page types)
    if not info.get('image') and t not in ('redirect', 'REDIRECT', 'special', 'skill', 'list'):
        issues.append(dict(issue='B5_NO_IMAGE', severity='minor',
                          detail='缺配图'))

    # B6: No references section
    if '## 参考文献' not in content and '## 来源' not in content and 'sources:' not in content[:500]:
        issues.append(dict(issue='B6_NO_REF_SECTION', severity='minor',
                          detail='缺「参考文献」或「来源」章节'))

    # B7: Empty/underpopulated aliases
    if not info.get('aliases') and q not in ('stub', '') and t not in ('redirect', 'REDIRECT', 'special'):
        issues.append(dict(issue='B7_NO_ALIASES', severity='minor',
                          detail='aliases为空，影响搜索匹配'))

    # ── Category C: Knowledge graph issues ──
    # C1: Low k_score for quality
    k_thresholds = {'premium': 30, 'featured': 25, 'standard': 15, 'basic': 8, 'stub': 0}
    k_min = k_thresholds.get(q, 0)
    if k_score < k_min and q not in ('',):
        issues.append(dict(issue='C1_LOW_K_SCORE', severity='minor',
                          detail=f'k_score={k_score}低于质量档{q}阈值{k_min}'))

    # C2: quality_score disparity
    qs_thresholds = {'premium': 35, 'featured': 30, 'standard': 20, 'basic': 10, 'stub': 0}
    qs_min = qs_thresholds.get(q, 0)
    if score < qs_min and q not in ('',):
        issues.append(dict(issue='C2_LOW_QUALITY_SCORE', severity='major',
                          detail=f'quality_score={score}低于质量档{q}阈值{qs_min}'))

    # ── Category D: Link & structure issues ──
    # D1: Broken wiki links
    wikilinks = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
    broken = set()
    for link in wikilinks:
        link_clean = link.strip()
        if link_clean == 'REDIRECT':
            continue
        if link_clean in pages:
            continue
        # Check alias match
        found = False
        for p2, i2 in pages.items():
            if link_clean in i2.get('aliases', []):
                found = True
                break
        if not found:
            broken.add(link_clean)
    if broken:
        issues.append(dict(issue='D1_BROKEN_LINKS', severity='major',
                          detail=f'{len(broken)}处指向不存在页面的链接：{", ".join(list(broken)[:5])}'))

    # D2: Malformed wikilinks
    bad_wl = re.findall(r'\[\[[^\]]*\\[^\]]*\]\]', content)
    if bad_wl:
        issues.append(dict(issue='D2_MALFORMED_LINKS', severity='major',
                          detail=f'{len(bad_wl)}处含反斜杠的畸形链接：{bad_wl[:3]}'))

    # D3: Orphan page (no incoming links from other wiki pages)
    # We'll detect this by checking backlinks.json later

    # ── Category E: Type-specific issues ──
    if t in ('place', 'state', '侯国'):
        # E1: No coordinates
        has_coord = bool(re.search(r'coords?\s*[:=]', content[:500]))
        if not has_coord:
            issues.append(dict(issue='E1_NO_COORDS', severity='major',
                              detail='place/state类型缺坐标，无法生成地图'))

    if t == 'person':
        # E2: Person page without canonical_name
        if not info.get('canonical_name'):
            issues.append(dict(issue='E2_NO_CANONICAL_NAME', severity='major',
                              detail='person类型缺canonical_name'))

    if t == 'chapter':
        # E3: Chapter not premium
        if q != 'premium':
            issues.append(dict(issue='E3_CHAPTER_NOT_PREMIUM', severity='major',
                              detail=f'章节页面质量{q}而非premium'))

    if t == 'chengyu':
        # E4: Chengyu pages all basic
        if q == 'basic':
            issues.append(dict(issue='E4_CHENGYU_BASIC', severity='minor',
                              detail='成语页面仅basic质量，缺少出处和典故'))

    if t in ('event',):
        # E5: Event pages mostly basic
        if q == 'basic':
            issues.append(dict(issue='E5_EVENT_BASIC', severity='minor',
                              detail='事件页面仅basic质量，缺少叙事、起因、结果'))

    if q == 'stub':
        issues.append(dict(issue='Z1_IS_STUB', severity='critical',
                          detail='存根页面，内容极度不足'))

    return issues


def main():
    os.makedirs('labs/analysis', exist_ok=True)

    pages = load_registry()
    print(f'Loaded {len(pages)} pages from registry')

    all_rows = []
    category_counts = Counter()
    severity_counts = Counter()
    page_count_by_type = Counter()
    page_count_by_quality = Counter()

    for i, (pid, info) in enumerate(pages.items()):
        if i % 2000 == 0 and i > 0:
            print(f'  Progress: {i}/{len(pages)}')
        issues = check_page(pid, info, pages)

        t = info.get('type', '')
        q = info.get('quality', '')

        issue_types = [iss['issue'].split('_', 1)[0][:1] for iss in issues]
        severity_list = [iss['severity'] for iss in issues]

        if not issues:
            # No issues found
            all_rows.append({
                'page_id': pid,
                'type': t,
                'quality': q,
                'quality_score': info.get('quality_score', 0),
                'k_score': info.get('k_score', 0),
                'file_size': 0,
                'issue_count': 0,
                'critical_count': 0,
                'major_count': 0,
                'minor_count': 0,
                'categories': '',
                'issues_summary': 'OK',
            })
            continue

        critical = sum(1 for s in severity_list if s == 'critical')
        major = sum(1 for s in severity_list if s == 'major')
        minor = sum(1 for s in severity_list if s == 'minor')

        cat_letters = sorted(set(issue_types))
        issue_summaries = [iss['detail'][:60] for iss in issues]

        all_rows.append({
            'page_id': pid,
            'type': t,
            'quality': q,
            'quality_score': info.get('quality_score', 0),
            'k_score': info.get('k_score', 0),
            'file_size': 0,  # filled below
            'issue_count': len(issues),
            'critical_count': critical,
            'major_count': major,
            'minor_count': minor,
            'categories': ','.join(cat_letters),
            'issues_summary': '; '.join([f'{iss["issue"]}: {iss["detail"]}' for iss in issues]),
        })

        for iss in issues:
            category_counts[iss['issue']] += 1
            severity_counts[iss['severity']] += 1

        page_count_by_type[t] += 1
        page_count_by_quality[q] += 1

    # Fill file_size
    for row in all_rows:
        pid = row['page_id']
        if pid in pages:
            path = pages[pid].get('path', '')
            if path:
                fp = os.path.join(BASE, path)
                if os.path.exists(fp):
                    row['file_size'] = os.path.getsize(fp)

    # Write CSV
    csv_path = 'labs/analysis/quality_audit.csv'
    fields = ['page_id', 'type', 'quality', 'quality_score', 'k_score', 'file_size',
              'issue_count', 'critical_count', 'major_count', 'minor_count',
              'categories', 'issues_summary']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f'\nCSV written: {csv_path}')
    print(f'Total rows: {len(all_rows)}')
    print(f'Pages with issues: {sum(1 for r in all_rows if r["issue_count"] > 0)}')
    print(f'Pages with no issues: {sum(1 for r in all_rows if r["issue_count"] == 0)}')

    # Write summary stats
    stats = {
        'total_pages': len(pages),
        'by_type': dict(page_count_by_type.most_common()),
        'by_quality': dict(page_count_by_quality.most_common()),
        'issue_summary': {
            'total_issues': sum(category_counts.values()),
            'by_severity': dict(severity_counts.most_common()),
            'by_category': dict(category_counts.most_common()),
        }
    }
    stats_path = 'labs/analysis/audit_stats.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f'Stats written: {stats_path}')

    # Print summary
    print('\n=== ISSUE SUMMARY ===')
    print(f'Total issues: {stats["issue_summary"]["total_issues"]}')
    for iss, count in category_counts.most_common(30):
        print(f'  {iss}: {count}')


if __name__ == '__main__':
    main()
