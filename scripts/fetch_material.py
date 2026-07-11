#!/usr/bin/env python3
"""
fetch_material.py — URL 素材自动抓取工具

用法:
    python fetch_material.py <URL>                     # 交互模式：抓取后提示输入 note
    python fetch_material.py <URL> --note "备注"       # 直接提供存储理由
    python fetch_material.py <URL> --method jina       # 指定抓取方式

抓取方式 (优先级):
    markitdown → jina (r.jina.ai) → requests+trafilatura → requests+html

输出:
    保存到 input/materials/YYYY-MM-DD-HHMMSS-slug.md
    frontmatter 包含: date, type, topic, tags, source
"""

import sys
import re
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse


# ── 路径配置 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_MATERIALS = PROJECT_ROOT / "input" / "materials"
TOPICS_FILE = PROJECT_ROOT / "system" / "topics.json"
BEIJING_TZ = timezone(timedelta(hours=8))


# ── 辅助函数 ──

def slugify(text, max_len=40):
    """生成文件名 slug：保留中英文、数字，空格/斜杠转连字符"""
    slug = re.sub(r'[^\w\u4e00-\u9fff-]', '', text.replace(' ', '-').replace('/', '-'))
    slug = re.sub(r'-+', '-', slug).strip('-').lower()
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip('-')
    return slug or 'untitled'


def now_iso():
    return datetime.now(BEIJING_TZ).isoformat()


def now_ts():
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d-%H%M%S')


# ── 元数据提取 ──

def extract_title(html):
    """从 HTML 提取标题（优先级: og:title > title > h1）"""
    # og:title
    m = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html, re.I)
    if m:
        return m.group(1).strip()
    # <title>
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    # <h1>
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.I | re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return ""


def extract_date(html):
    """从 HTML 提取发布日期"""
    patterns = [
        (r'<meta[^>]*property="article:published_time"[^>]*content="([^"]*)"', 1),
        (r'<meta[^>]*name="date"[^>]*content="([^"]*)"', 1),
        (r'<meta[^>]*name="pubdate"[^>]*content="([^"]*)"', 1),
        (r'<meta[^>]*property="article:modified_time"[^>]*content="([^"]*)"', 1),
        (r'<time[^>]*datetime="([^"]*)"', 1),
    ]
    for pattern, _ in patterns:
        m = re.search(pattern, html, re.I)
        if m:
            dt_str = m.group(1).strip()
            # 尝试多种格式
            for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S',
                         '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(dt_str[:len(fmt.replace('%z', ''))], fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt.astimezone(BEIJING_TZ).isoformat()
                except ValueError:
                    continue
    return None


def extract_title_from_md(md_text):
    """从 Markdown 文本提取标题"""
    lines = md_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# ') and not line.startswith('## '):
            return line[2:].strip()
    if lines:
        first = lines[0].strip()
        return first[:100] if first else ""
    return ""


# ── 内容抓取 ──

def fetch_via_markitdown(url):
    """markitdown Python API：自动识别正文并转 Markdown（质量最高）"""
    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(url)
        return result.text_content, ""
    except ImportError:
        raise RuntimeError("markitdown 未安装")


def fetch_via_jina(url):
    """Jina AI：将网页转为 Markdown（无需安装，token 友好）"""
    jina_url = f"https://r.jina.ai/{url}"
    req = urllib.request.Request(jina_url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/markdown',
    })
    ssl_ctx = _get_ssl_context()
    with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
        return resp.read().decode('utf-8'), ""


def fetch_via_trafilatura(url):
    """trafilatura：专业网页正文提取"""
    html = _fetch_html(url)
    try:
        from trafilatura import extract, bare_extraction
        result = extract(html, output_format='markdown', url=url,
                         include_links=True, include_images=False,
                         include_tables=True, with_metadata=True)
        if result and len(result.strip()) > 100:
            return result.strip(), html
        # 正文太短，退回 bare 模式
        result = extract(html, output_format='markdown', url=url,
                         favor_precision=True)
        if result:
            return result.strip(), html
    except ImportError:
        pass
    raise RuntimeError("trafilatura 提取失败")


def _get_ssl_context():
    """获取 SSL 上下文（尝试 certifi，失败则跳过验证）"""
    try:
        import certifi
        import ssl
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, Exception):
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


def _fetch_html(url):
    """HTTP GET，返回 HTML 文本（优先用 requests 库处理编码）"""
    try:
        import requests as req
        resp = req.get(url, headers={
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/125.0.0.0 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }, timeout=30)
        resp.raise_for_status()
        # requests 自动处理编码
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except ImportError:
        pass

    # fallback: urllib
    ssl_ctx = _get_ssl_context()
    req = urllib.request.Request(url, headers={
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/125.0.0.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    })
    with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
        raw = resp.read()
        for enc in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return raw.decode('utf-8', errors='replace')


def html_to_markdown_basic(html):
    """基础 HTML → Markdown（无外部依赖的最后兜底）"""
    # 移除 script / style / 注释
    html = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.I)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    # 优先取 <article> / <main>，否则整个 body
    for tag in ['article', 'main']:
        m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', html, re.DOTALL | re.I)
        if m and len(m.group(1).strip()) > 200:
            html = m.group(1)
            break
    else:
        m = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.I)
        if m:
            html = m.group(1)

    md = html

    # 标题 h1-h6
    for i in range(6, 0, -1):
        md = re.sub(rf'<h{i}[^>]*>\s*(.*?)\s*</h{i}>',
                     rf'\n\n{"#" * i} \1\n\n', md, flags=re.DOTALL | re.I)

    # 段落
    md = re.sub(r'<p[^>]*>\s*(.*?)\s*</p>', r'\n\n\1\n\n', md, flags=re.DOTALL | re.I)

    # 粗体 / 斜体
    md = re.sub(r'<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>', r'**\1**', md, flags=re.DOTALL | re.I)
    md = re.sub(r'<(?:em|i)[^>]*>(.*?)</(?:em|i)>', r'*\1*', md, flags=re.DOTALL | re.I)

    # 链接
    md = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', md, flags=re.DOTALL | re.I)

    # 列表
    md = re.sub(r'<li[^>]*>\s*(.*?)\s*</li>', r'- \1\n', md, flags=re.DOTALL | re.I)

    # 换行
    md = re.sub(r'<br\s*/?>', '\n', md, flags=re.I)

    # 表格（简单处理）
    md = re.sub(r'</?table[^>]*>', '\n', md, flags=re.I)
    md = re.sub(r'</?tr[^>]*>', '\n', md, flags=re.I)
    md = re.sub(r'<t[dh][^>]*>\s*(.*?)\s*</t[dh]>', r'| \1 ', md, flags=re.DOTALL | re.I)

    # 移除其余标签
    md = re.sub(r'<[^>]+>', '', md)

    # 解码 HTML 实体
    import html as html_module
    md = html_module.unescape(md)

    # 清理空白
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = re.sub(r' +', ' ', md)
    md = re.sub(r'^\s+', '', md)

    return md.strip()


# ── 主题/标签自动匹配 ──

def detect_topics_and_tags(text):
    """根据正文关键词匹配 topics.json 中的主题和标签"""
    if not TOPICS_FILE.exists():
        return [], []

    with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
        topics_data = json.load(f)

    text_lower = text.lower()
    topics = []
    tags = []

    for topic in topics_data.get('topics', []):
        keywords = topic.get('keywords', [])
        for kw in keywords:
            # 英文关键词：大小写不敏感；中文关键词：直接匹配
            if kw.lower() in text_lower:
                if topic['id'] not in topics:
                    topics.append(topic['id'])
                if kw not in tags:
                    tags.append(kw)

    return topics, tags


# ── 核心流程 ──

def fetch_content(url, method="auto"):
    """多级抓取 URL 内容 → (markdown, html)"""
    methods = {
        "markitdown": fetch_via_markitdown,
        "jina": fetch_via_jina,
        "trafilatura": fetch_via_trafilatura,
        "basic": lambda u: (html_to_markdown_basic(_fetch_html(u)), _fetch_html(u)),
    }

    order = (["markitdown", "jina", "trafilatura", "basic"]
             if method == "auto" else [method])

    last_error = None
    for m in order:
        try:
            print(f"   尝试 {m} ...", end=" ", flush=True)
            md, html = methods[m](url)
            if md and len(md.strip()) > 50:
                print("✓")
                return md, html
            print("✗ (内容过短)")
        except Exception as e:
            print(f"✗ ({_short_error(e)})")
            last_error = e
            continue

    raise RuntimeError(f"所有抓取方式均失败: {last_error}")


def _short_error(e):
    msg = str(e).split('\n')[0]
    return msg[:80]


def save_material_from_content(url, markdown_content, title="", date_str="", note=None):
    """从已抓取的 Markdown 内容保存素材（适用 WebFetch 等外部抓取）"""
    # [FIX] URL 去重：检查 SQLite 是否已存在
    try:
        import sqlite3
        db_path = PROJECT_ROOT / "system" / f"{PROJECT_ROOT.name}.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cur = conn.execute("SELECT id FROM materials WHERE source_url=?", (url,))
            if cur.fetchone():
                conn.close()
                print(f"  ⏭ 跳过（已存在）: {url}")
                return None
            conn.close()
    except Exception:
        pass  # SQLite 不可用时忽略，不阻断流程
    
    domain = urlparse(url).netloc

    # 标题：传入 > HTML提取 > Markdown提取 > domain
    if not title:
        title = extract_title_from_md(markdown_content)
    if not title:
        title = domain
    title = title.replace('\n', ' ').strip()

    # 日期
    if not date_str:
        date_str = now_iso()

    # 清理 Markdown
    md_text = _clean_markdown(markdown_content, url)

    # 主题/标签
    topics, tags = detect_topics_and_tags(md_text)

    # 生成文件名
    slug = slugify(title)
    filename = f"{now_ts()}-{slug}.md"
    filepath = INPUT_MATERIALS / filename

    # 构建内容
    fm_parts = [
        "---",
        f"date: {date_str}",
        "type: material",
    ]
    if topics:
        fm_parts.append(f"topic: [{', '.join(topics)}]")
    if tags:
        fm_parts.append(f"tags: [{', '.join(tags)}]")
    fm_parts.append("source:")
    fm_parts.append(f"  - {url}")
    fm_parts.append("---")

    body_parts = [
        f"# {title}",
        "",
        f"> 来源: [{domain}]({url})",
        f"> 抓取时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 原文",
        "",
        md_text,
    ]

    content = '\n'.join(fm_parts) + '\n\n' + '\n'.join(body_parts)

    # 写入
    INPUT_MATERIALS.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding='utf-8')

    rel_path = str(filepath.relative_to(PROJECT_ROOT)).replace('\\', '/')

    print(f"\n{'='*60}")
    print(f"✅ 已保存: {rel_path}")
    print(f"   标题: {title}")
    print(f"   来源: {domain}")
    print(f"   日期: {date_str[:10]}")
    print(f"   主题: {', '.join(topics) if topics else '(未自动匹配)'}")
    print(f"   标签: {', '.join(tags) if tags else '(无)'}")
    print(f"{'='*60}")

    if note:
        _append_note(filepath, note)
        print(f"📝 备注已写入: {note}")

    return filepath
    """主流程：抓取 → 提取元数据 → 写入文件 → 提示 note"""
    print(f"🌐 抓取: {url}")

    # 1. 抓取内容
    md_text, html_text = fetch_content(url, method)

    # 2. 提取元数据
    domain = urlparse(url).netloc

    # 标题
    title = ""
    if html_text:
        title = extract_title(html_text)
    if not title:
        title = extract_title_from_md(md_text)
    if not title:
        title = domain
    title = title.replace('\n', ' ').strip()

    # 日期
    date_str = None
    if html_text:
        date_str = extract_date(html_text)
    if not date_str:
        date_str = now_iso()

    # 4. 主题/标签
    topics, tags = detect_topics_and_tags(md_text)

    # 5. 生成文件名
    slug = slugify(title)
    filename = f"{now_ts()}-{slug}.md"
    filepath = INPUT_MATERIALS / filename

    # 清理 Markdown：移除 Jina 等工具加在开头的 URL 行
    md_text = _clean_markdown(md_text, url)

    # 6. 构建内容
    fm_parts = [
        "---",
        f"date: {date_str}",
        "type: material",
    ]
    if topics:
        fm_parts.append(f"topic: [{', '.join(topics)}]")
    if tags:
        fm_parts.append(f"tags: [{', '.join(tags)}]")
    fm_parts.append("source:")
    fm_parts.append(f"  - {url}")
    fm_parts.append("---")

    body_parts = [
        f"# {title}",
        "",
        f"> 来源: [{domain}]({url})",
        f"> 抓取时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 原文",
        "",
        md_text,
    ]

    content = '\n'.join(fm_parts) + '\n\n' + '\n'.join(body_parts)

    # 7. 写入文件
    INPUT_MATERIALS.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding='utf-8')

    rel_path = str(filepath.relative_to(PROJECT_ROOT)).replace('\\', '/')

    print(f"\n{'='*60}")
    print(f"✅ 已保存: {rel_path}")
    print(f"   标题: {title}")
    print(f"   来源: {domain}")
    print(f"   日期: {date_str[:10]}")
    print(f"   主题: {', '.join(topics) if topics else '(未自动匹配)'}")
    print(f"   标签: {', '.join(tags) if tags else '(无)'}")
    print(f"{'='*60}")

    # 8. 如有 note，追加
    if note:
        _append_note(filepath, note)
        print(f"📝 备注已写入: {note}")

    return filepath


def _clean_markdown(md, url):
    """清理 Markdown 格式问题"""
    # 移除 Jina 加的 Title: 和 URL Source: 行
    lines = md.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # 跳过 Jina 格式的元数据行
        if re.match(r'^(Title|URL Source|Published Time|Markdown Content):', stripped, re.I):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned).strip()


def _append_note(filepath, note):
    """追加用户存储理由"""
    content = filepath.read_text(encoding='utf-8')
    if '## 存储理由' not in content:
        content = content.rstrip() + '\n\n## 存储理由\n\n'
    content += f"{note}\n"
    filepath.write_text(content, encoding='utf-8')


def append_note(filepath, note):
    """外部调用：给已有素材追加备注"""
    fp = Path(filepath)
    if not fp.exists():
        print(f"❌ 文件不存在: {filepath}")
        return False
    _append_note(fp, note)
    print(f"✅ 备注已追加到: {fp.name}")
    return True


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(
        description='URL 素材自动抓取工具 — 抓取网页正文转 Markdown，存入 input/materials/')
    parser.add_argument('url', nargs='?', help='要抓取的 URL')
    parser.add_argument('--note', '-n', help='存储理由')
    parser.add_argument('--method', '-m', default='auto',
                        choices=['auto', 'markitdown', 'jina', 'trafilatura', 'basic'],
                        help='抓取方式 (default: auto，自动降级)')
    parser.add_argument('--append', '-a', help='向已有文件追加备注（需提供文件路径）')
    parser.add_argument('--from-stdin', action='store_true',
                        help='从 stdin 读取 Markdown 内容（配合 WebFetch 等外部工具使用）')
    parser.add_argument('--content-file', help='从文件读取 Markdown 内容')
    parser.add_argument('--title', help='手动指定标题')
    parser.add_argument('--date', help='手动指定日期 (YYYY-MM-DD)')
    parser.add_argument('--output-json', action='store_true',
                        help='以 JSON 格式输出结果（供程序调用）')

    args = parser.parse_args()

    # 追加模式
    if args.append:
        if not args.note:
            print("❌ --append 需要同时提供 --note")
            sys.exit(1)
        append_note(args.append, args.note)
        return

    # stdin / 文件输入模式
    if args.from_stdin or args.content_file:
        if not args.url:
            print("❌ --from-stdin / --content-file 需要同时提供 URL")
            sys.exit(1)

        if args.from_stdin:
            markdown_content = sys.stdin.read()
        else:
            markdown_content = Path(args.content_file).read_text(encoding='utf-8')

        filepath = save_material_from_content(
            args.url, markdown_content,
            title=args.title or "",
            date_str=args.date or "",
            note=args.note,
        )

        if args.output_json:
            print(json.dumps({
                "path": str(filepath),
                "relative_path": str(filepath.relative_to(PROJECT_ROOT)).replace('\\', '/'),
            }, ensure_ascii=False))

        if not args.note:
            print("\n💡 运行以下命令补充存储理由：")
            print(f"   python scripts/fetch_material.py --append \"{filepath}\" --note \"你的理由\"")
            sys.exit(2)
        return

    # 抓取模式
    if not args.url:
        parser.print_help()
        sys.exit(1)

    filepath = save_material(args.url, args.note, args.method)

    if args.output_json:
        print(json.dumps({
            "path": str(filepath),
            "relative_path": str(filepath.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        }, ensure_ascii=False))

    if not args.note:
        print("\n💡 运行以下命令补充存储理由：")
        print(f"   python scripts/fetch_material.py --append \"{filepath}\" --note \"你的理由\"")
        sys.exit(2)  # 退出码 2 = 等待补充 note


if __name__ == '__main__':
    main()
