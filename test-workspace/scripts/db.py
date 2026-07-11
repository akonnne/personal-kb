#!/usr/bin/env python3
"""
澳洲出国策略系统 — SQLite + FTS5 数据库模块

核心能力：
- 全文搜索 (FTS5)，关键词/主题/标签/类型/时间组合检索
- 素材 CRUD，自动同步文件系统
- WAL 模式，读不阻塞写
"""

import sqlite3
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# CJK Unicode 范围
CJK_RE = re.compile(r"([\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff])")


def tokenize_cjk(text: str) -> str:
    """中文分词：在 CJK 字符之间插入空格，使 FTS5 能逐字索引。
    
    FTS5 unicode61 tokenizer 不切中文词，需要预处理。
    '澳洲打工' -> '澳 洲 打 工 '
    """
    if not text:
        return ""
    return CJK_RE.sub(r" \1 ", text)


def cjk_query(keyword: str) -> str:
    """将中文搜索词转为 FTS5 短语查询。
    
    '打工' -> '" 打 工 "'
    """
    if not keyword:
        return ""
    spaced = tokenize_cjk(keyword)
    return f'"{spaced.strip()}"'

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# [FIX] 数据库名取 workspace 目录名，避免多 workspace 冲突
DB_NAME = os.environ.get("KB_DB_NAME", PROJECT_ROOT.name + ".db")
DB_PATH = PROJECT_ROOT / "system" / DB_NAME

INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"

INPUT_TYPE_MAP = {"ideas": "idea", "materials": "material", "snippets": "snippet"}
OUTPUT_TYPE_MAP = {"strategies": "strategy", "pathways": "pathway", "reports": "report", "checklists": "checklist"}

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-8000;
PRAGMA mmap_size=268435456;

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    topics TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    date TEXT,
    style TEXT,
    source TEXT,
    sources TEXT DEFAULT '[]',
    title TEXT,
    content TEXT,
    search_text TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_materials_type ON materials(type);
CREATE INDEX IF NOT EXISTS idx_materials_date ON materials(date);
CREATE INDEX IF NOT EXISTS idx_materials_style ON materials(style);

-- FTS5 虚拟表，索引 tokenize 后的中文文本
CREATE VIRTUAL TABLE IF NOT EXISTS materials_fts USING fts5(
    search_text,
    tokenize='unicode61 remove_diacritics 2'
);
"""


def get_db() -> sqlite3.Connection:
    """获取数据库连接，自动建表"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    return conn


def parse_frontmatter(content: str) -> dict:
    """解析 YAML frontmatter"""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    fm_text = match.group(1)
    fm = {}
    for line in fm_text.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
            fm[key] = val
    return fm


def extract_title_and_body(content: str) -> tuple:
    """提取标题（第一个 # 行）和正文（frontmatter 之后）"""
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
    title = ""
    lines = body.strip().split("\n")
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return title, body.strip()


def scan_file(md_file: Path, type_override: str = None) -> Optional[dict]:
    """扫描单个 Markdown 文件，返回数据字典"""
    try:
        content = md_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        title, body = extract_title_and_body(content)

        raw_topics = fm.get("topic", [])
        if isinstance(raw_topics, str):
            raw_topics = [raw_topics]
        raw_tags = fm.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]
        raw_sources = fm.get("sources", [])
        if isinstance(raw_sources, str):
            raw_sources = [raw_sources]

        # 构建 FTS5 搜索文本（标题+正文+标签+主题，中文做字符级分词）
        search_text = tokenize_cjk(f"{title} {' '.join(raw_tags)} {' '.join(raw_topics)}\n{body}")

        stat = md_file.stat()
        return {
            "filename": md_file.name,
            "filepath": str(md_file.relative_to(PROJECT_ROOT)),
            "type": fm.get("type", type_override or "unknown"),
            "topics": json.dumps(raw_topics, ensure_ascii=False),
            "tags": json.dumps(raw_tags, ensure_ascii=False),
            "date": fm.get("date", ""),
            "style": fm.get("style", ""),
            "source": fm.get("source", ""),
            "sources": json.dumps(raw_sources, ensure_ascii=False),
            "title": title,
            "content": body,
            "search_text": search_text,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    except Exception as e:
        print(f"  [WARN] 解析失败: {md_file} — {e}")
        return None


def full_sync() -> dict:
    """全量同步：扫描所有 Markdown 文件 → SQLite
    
    Returns: {"added": int, "updated": int, "deleted": int, "total": int}
    """
    conn = get_db()
    stats = {"added": 0, "updated": 0, "deleted": 0, "total": 0}
    seen_paths = set()

    # 扫描所有 Markdown 文件
    new_data = []
    for base_dir, type_map in [(INPUT_DIR, INPUT_TYPE_MAP), (OUTPUT_DIR, OUTPUT_TYPE_MAP)]:
        if not base_dir.exists():
            continue
        for subdir_name, entry_type in type_map.items():
            subdir = base_dir / subdir_name
            if not subdir.exists():
                continue
            for md_file in sorted(subdir.glob("*.md")):
                info = scan_file(md_file, type_override=entry_type)
                if info:
                    seen_paths.add(info["filepath"])
                    new_data.append(info)

    # 获取数据库中已有的记录
    cur = conn.execute("SELECT id, filepath FROM materials")
    existing = {row["filepath"]: row["id"] for row in cur.fetchall()}

    # FTS5 清空重建（保证一致性，数据量小时最快）
    conn.execute("DELETE FROM materials_fts")

    # 插入新记录 / 更新已有记录
    with conn:
        for info in new_data:
            if info["filepath"] in existing:
                row_id = existing[info["filepath"]]
                conn.execute("""
                    UPDATE materials SET
                        filename=:filename, type=:type, topics=:topics,
                        tags=:tags, date=:date, style=:style, source=:source,
                        sources=:sources, title=:title, content=:content,
                        search_text=:search_text, updated_at=:updated_at
                    WHERE id=:row_id
                """, {**info, "row_id": row_id})
                conn.execute("INSERT INTO materials_fts(rowid, search_text) VALUES (?, ?)",
                             (row_id, info["search_text"]))
                stats["updated"] += 1
                del existing[info["filepath"]]
            else:
                cur = conn.execute("""
                    INSERT INTO materials (filename, filepath, type, topics, tags, date, style, source, sources, title, content, search_text, created_at, updated_at)
                    VALUES (:filename, :filepath, :type, :topics, :tags, :date, :style, :source, :sources, :title, :content, :search_text, :created_at, :updated_at)
                """, info)
                row_id = cur.lastrowid
                conn.execute("INSERT INTO materials_fts(rowid, search_text) VALUES (?, ?)",
                             (row_id, info["search_text"]))
                stats["added"] += 1

    # 删除数据库中已不存在的文件记录
    for stale_path, stale_id in existing.items():
        conn.execute("DELETE FROM materials WHERE id = ?", (stale_id,))
        conn.execute("DELETE FROM materials_fts WHERE rowid = ?", (stale_id,))
        stats["deleted"] += 1

    stats["total"] = len(new_data)
    conn.close()
    return stats


def search(
    keyword: str = None,
    topic: str = None,
    tag: str = None,
    material_type: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    """组合检索
    
    参数：
        keyword: FTS5 全文搜索（匹配 title + content + tags + topics）
        topic: 按主题过滤
        tag: 按标签过滤
        material_type: 按类型过滤
        date_from / date_to: 时间范围 (YYYY-MM-DD)
        limit / offset: 分页
    
    返回：按 date DESC 排序的字典列表
    """
    conn = get_db()
    conditions = []
    params = {}

    if keyword:
        conditions.append("m.id IN (SELECT rowid FROM materials_fts WHERE materials_fts MATCH :keyword)")
        params["keyword"] = cjk_query(keyword)

    if topic:
        conditions.append("m.topics LIKE :topic")
        params["topic"] = f'%"{topic}"%'

    if tag:
        conditions.append("m.tags LIKE :tag")
        params["tag"] = f'%"{tag}"%'

    if material_type:
        conditions.append("m.type = :type")
        params["type"] = material_type

    if date_from:
        conditions.append("m.date >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("m.date <= :date_to")
        params["date_to"] = date_to + "T23:59:59"

    where = " AND ".join(conditions) if conditions else "1=1"

    sql = f"""
        SELECT m.*
        FROM materials m
        WHERE {where}
        ORDER BY m.date DESC
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = limit
    params["offset"] = offset

    cur = conn.execute(sql, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_stats() -> dict:
    """获取数据库统计信息，用于生成 status.md"""
    conn = get_db()

    # 总计数
    total = conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0]
    type_counts = {}
    for row in conn.execute("SELECT type, COUNT(*) as cnt FROM materials GROUP BY type"):
        type_counts[row["type"]] = row["cnt"]

    # 主题分布
    topic_counts = {}
    for row in conn.execute("SELECT topics FROM materials WHERE topics != '[]'"):
        for t in json.loads(row["topics"]):
            topic_counts[t] = topic_counts.get(t, 0) + 1

    # 时间分布
    first = conn.execute("SELECT MIN(date) FROM materials WHERE date != ''").fetchone()[0] or "—"
    last = conn.execute("SELECT MAX(date) FROM materials WHERE date != ''").fetchone()[0] or "—"

    # 最近 7 天新增
    recent = conn.execute(
        "SELECT COUNT(*) FROM materials WHERE date >= date('now', '-7 days')"
    ).fetchone()[0]

    # 高频标签 Top 10
    tag_counts = {}
    for row in conn.execute("SELECT tags FROM materials WHERE tags != '[]'"):
        for t in json.loads(row["tags"]):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:10]

    # 有输入无输出的主题（空白发现）
    input_topics = set()
    output_topics = set()
    for row in conn.execute("SELECT type, topics FROM materials WHERE topics != '[]'"):
        topics = json.loads(row["topics"])
        if row["type"] in ("idea", "material", "snippet"):
            input_topics.update(topics)
        else:
            output_topics.update(topics)
    gap_topics = list(input_topics - output_topics)

    # 最近修改
    latest = []
    for row in conn.execute("SELECT filename, type, date, filepath FROM materials ORDER BY date DESC LIMIT 5"):
        latest.append(dict(row))

    conn.close()

    return {
        "total": total,
        "type_counts": type_counts,
        "topic_counts": topic_counts,
        "first_date": first[:10] if first and first != "—" else "—",
        "last_date": last[:10] if last and last != "—" else "—",
        "recent_7d": recent,
        "top_tags": top_tags,
        "gap_topics": gap_topics,
        "latest": latest,
    }


if __name__ == "__main__":
    # 直接运行 → 全量同步
    print("=" * 60)
    print("  澳洲出国策略系统 — 数据库同步")
    print("=" * 60)
    result = full_sync()
    print(f"\n  新增: {result['added']} | 更新: {result['updated']} | 删除: {result['deleted']}")
    print(f"  总计: {result['total']} 条素材")
    print("\n" + "=" * 60)
    print("  同步完成")
    print("=" * 60)
