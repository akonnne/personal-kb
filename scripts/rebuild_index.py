#!/usr/bin/env python3
"""
澳洲出国策略系统 — 素材库同步脚本

每次输入/输出操作后运行，自动同步 Markdown 文件到 SQLite 数据库。
同时生成 status.md 状态概览。
"""

import sys
sys.path.insert(0, str(__file__).rsplit("/", 1)[0] if "/" in __file__ else ".")

from db import full_sync
from generate_status import generate_status


def main():
    print("=" * 60)
    print("  澳洲出国策略系统 — 素材库同步")
    print("=" * 60)

    result = full_sync()
    print(f"\n  SQLite 同步: 新增 {result['added']} | 更新 {result['updated']} | 删除 {result['deleted']}")
    print(f"  素材库总条目: {result['total']}")

    generate_status()

    print("\n" + "=" * 60)
    print("  同步完成 — 数据库 + 状态文件已更新")
    print("=" * 60)


if __name__ == "__main__":
    main()
