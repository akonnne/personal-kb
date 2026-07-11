#!/usr/bin/env python3
"""
知识库自动化测试套件
运行方式：python scripts/test_suite.py
"""
import json, os, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT
PASS, FAIL = 0, 0


def run_py(script, *args, expect_code=0):
    """运行脚本并返回 (exit_code, stdout)"""
    cmd = [sys.executable, str(ROOT / "scripts" / script)] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), timeout=30)
    return r.returncode, r.stdout


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ✅ {name} {detail}")
        PASS += 1
    else:
        print(f"  ❌ {name} {detail}")
        FAIL += 1


print("=" * 50)
print("  personal-kb Test Suite")
print("=" * 50)


# ── Test 1: rebuild_index.py ──
print("\n📋 Test 1: rebuild_index.py")
rc, out = run_py("rebuild_index.py")
check("Exit code == 0", rc == 0, f"(got {rc})")
check("Output contains '同步完成'", "同步完成" in out)

# Check files exist
db_name = ROOT.name + ".db"
check("SQLite DB created", (ROOT / "system" / db_name).exists(), f"({db_name})")
check("status.md generated", (ROOT / "system" / "status.md").exists())


# ── Test 2: distill_cards.py ──
print("\n📋 Test 2: distill_cards.py")
rc, out = run_py("distill_cards.py")
check("Exit code == 0", rc == 0, f"(got {rc})")
check("Output contains '总计'", "总计" in out)

# Check card_index.json
card_json = ROOT / "output" / "cards" / "card_index.json"
if card_json.exists():
    data = json.loads(card_json.read_text(encoding='utf-8'))
    cards = data.get("cards", [])
    links = data.get("links", [])
    check("card_index.json valid", len(cards) > 0, f"({len(cards)} cards)")
    check("Cards have ids", all("id" in c for c in cards))
    check("Cards have topic", all("topic" in c for c in cards))
    check("Cards have tags", all("tags" in c for c in cards))
    # [FIX] 验证 tag 跨主题：检查是否有卡片包含多个 topic
    multi_topic = sum(1 for c in cards if len(c.get("topic", [])) > 1)
    check("Cards have cross-topic tags", multi_topic > 0, f"({multi_topic}/{len(cards)} multi-topic)")
    check("Links exist", len(links) > 0, f"({len(links)} links)")
else:
    check("card_index.json exists", False)


# ── Test 3: rebuild_graph.py ──
print("\n📋 Test 3: rebuild_graph.py")
rc, out = run_py("rebuild_graph.py", "--validate")
check("Exit code == 0", rc == 0, f"(got {rc})")
check("Output contains '健康报告'", "健康报告" in out)
check("Output contains '验证通过'", "验证通过" in out)

graph_html = ROOT / "output" / "cards" / "knowledge_graph.html"
if graph_html.exists():
    html = graph_html.read_text(encoding='utf-8')
    check("HTML contains D3.js", "d3.min.js" in html or "d3@7" in html)
    check("HTML contains data", "var nodes =" in html)
    check("HTML contains links", "var links =" in html)
    check("HTML has simulation", "d3.forceSimulation" in html)


# ── Test 4: 增量蒸馏（幂等性）──
print("\n📋 Test 4: 增量蒸馏（幂等性）")
rc1, out1 = run_py("distill_cards.py")
rc2, out2 = run_py("distill_cards.py")
check("Second run exit code == 0", rc2 == 0)
check("Second run skips all", "跳过" in out2)
# Verify same output
data1 = json.loads((ROOT / "output" / "cards" / "card_index.json").read_text(encoding='utf-8'))
check("Same card count", data1["total_cards"] == data["total_cards"],
      f"({data1['total_cards']} vs {data['total_cards']})")


# ── Summary ──
print(f"\n{'='*50}")
total = PASS + FAIL
print(f"  Results: {PASS}/{total} passed" + (f", {FAIL} failed" if FAIL else ""))
print(f"{'='*50}")

sys.exit(0 if FAIL == 0 else 1)
