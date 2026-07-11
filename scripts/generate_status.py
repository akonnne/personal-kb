#!/usr/bin/env python3
"""
澳洲出国策略系统 — 状态概览生成器

从 SQLite 数据库读取统计信息，生成 system/status.md
设计目标：30 秒内看懂当前素材库状态
"""

import sys
from datetime import datetime
from pathlib import Path
from db import get_stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = PROJECT_ROOT / "system" / "status.md"


def generate_status():
    stats = get_stats()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 数据库大小
    db_path = PROJECT_ROOT / "system" / "australia.db"
    db_size = db_path.stat().st_size / 1024 if db_path.exists() else 0

    lines = []
    lines.append("# 澳洲策略素材库 · 状态")
    lines.append("")
    lines.append(f"> 快照时间：{now}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ===== 核心指标（一眼看完） =====
    lines.append("## 核心指标")
    lines.append("")
    total = stats["total"]
    type_counts = stats["type_counts"]
    input_count = sum(v for k, v in type_counts.items() if k in ("idea", "material", "snippet"))
    output_count = sum(v for k, v in type_counts.items() if k in ("strategy", "pathway", "report", "checklist"))

    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 素材总数 | **{total}** |")
    lines.append(f"| 输入素材 | {input_count} 条 |")
    lines.append(f"| 输出内容 | {output_count} 条 |")
    lines.append(f"| 最近 7 天新增 | {stats['recent_7d']} 条 |")
    lines.append(f"| 时间跨度 | {stats['first_date']} ~ {stats['last_date']} |")
    lines.append(f"| 数据库大小 | {db_size:.0f} KB |")
    lines.append("")

    # ===== 类型分布 =====
    lines.append("## 类型分布")
    lines.append("")
    type_order = ["idea", "material", "snippet", "strategy", "pathway", "report", "checklist"]
    lines.append("| 类型 | 数量 | 占比 |")
    lines.append("|------|------|------|")
    for t in type_order:
        cnt = type_counts.get(t, 0)
        pct = f"{cnt/total*100:.0f}%" if total > 0 else "—"
        name_map = {
            "idea": "💡 想法", "material": "📄 素材", "snippet": "📎 片段",
            "strategy": "🎯 策略", "pathway": "🗺️ 路线", "report": "📊 报告", "checklist": "✅ 清单"
        }
        if cnt > 0:
            lines.append(f"| {name_map.get(t, t)} | {cnt} | {pct} |")
    lines.append("")

    # ===== 主题分布 =====
    if stats["topic_counts"]:
        lines.append("## 主题分布")
        lines.append("")
        lines.append("| 主题 | 数量 |")
        lines.append("|------|------|")
        for topic, cnt in sorted(stats["topic_counts"].items(), key=lambda x: -x[1]):
            lines.append(f"| {topic} | {cnt} |")
        lines.append("")

    # ===== 热门标签 =====
    if stats["top_tags"]:
        lines.append("## 热门标签 Top 10")
        lines.append("")
        for tag, cnt in stats["top_tags"]:
            lines.append(f"- `{tag}` ({cnt})")
        lines.append("")

    # ===== 空白发现 =====
    if stats["gap_topics"]:
        lines.append("## 空白发现")
        lines.append("")
        lines.append("以下主题有输入但尚未产出分析内容：")
        lines.append("")
        for t in stats["gap_topics"]:
            lines.append(f"- {t}")
        lines.append("")

    # ===== 最新素材 =====
    if stats["latest"]:
        lines.append("## 最新素材")
        lines.append("")
        for item in stats["latest"]:
            date_str = item["date"][:10] if item["date"] else "—"
            type_icon = {"idea": "💡", "material": "📄", "snippet": "📎",
                         "strategy": "🎯", "pathway": "🗺️", "report": "📊", "checklist": "✅"}
            icon = type_icon.get(item["type"], "📌")
            lines.append(f"- {icon} `{item['filename']}` — {date_str}")
        lines.append("")

    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"  status.md 已生成: {STATUS_FILE}")


if __name__ == "__main__":
    generate_status()
