#!/usr/bin/env python3
"""最终版知识图谱：主题预定位，节点围绕主题中心分布，跨主题虚线连接簇中心"""
import json, os, math
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD_JSON = os.path.join(BASE, "output", "cards", "card_index.json")
OUTPUT_HTML = os.path.join(BASE, "output", "cards", "knowledge_graph.html")

with open(CARD_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

cards = data["cards"]

# ── 1. 去重 ID ──
seen_ids = {}
for c in cards:
    raw = c["id"]
    if raw in seen_ids:
        seen_ids[raw] += 1
        c["_uid"] = f"{raw}-{seen_ids[raw]}"
    else:
        seen_ids[raw] = 0
        c["_uid"] = raw

# ── 2. 预计算 ──
def get_tags(c):
    return set(c.get("tags", []))

for c in cards:
    c["_tags"] = get_tags(c)
    c["_primary"] = c.get("topic", ["migration"])[0] if c.get("topic") else "migration"

# ── 3. 基于 tag 共现建立连接（权重 >= 2）──
pair_weights = {}
for i in range(len(cards)):
    for j in range(i + 1, len(cards)):
        a, b = cards[i], cards[j]
        if a["_uid"] == b["_uid"]:
            continue
        shared = a["_tags"] & b["_tags"]
        if len(shared) >= 2:
            key = tuple(sorted([a["_uid"], b["_uid"]]))
            pair_weights[key] = len(shared)

# ── 4. 每个节点保留 top 5 连接 ──
adj = defaultdict(list)
for (u, v), w in pair_weights.items():
    adj[u].append((v, w))
    adj[v].append((u, w))

link_set = set()
links = []
for uid in [c["_uid"] for c in cards]:
    if uid not in adj:
        continue
    connections = sorted(adj[uid], key=lambda x: x[1], reverse=True)
    for target, w in connections[:5]:
        key = tuple(sorted([uid, target]))
        if key in link_set:
            continue
        link_set.add(key)
        links.append({"source": uid, "target": target, "weight": w})

# ── 5. 找出每个主题的中心节点（度数最高）──
topic_cards = defaultdict(list)
for c in cards:
    topic_cards[c["_primary"]].append(c)

topic_centers = {}
for topic, tcards in topic_cards.items():
    # 选度数最高的节点作为中心
    best = max(tcards, key=lambda c: len(adj.get(c["_uid"], [])))
    topic_centers[topic] = best["_uid"]

# ── 6. 建立跨主题连接：主题中心之间 ──
# 相邻主题中心连接，权重=1
center_topics = sorted(topic_centers.keys())
for i in range(len(center_topics)):
    for j in range(i + 1, len(center_topics)):
        if abs(j - i) <= 2 or abs(j - i) >= len(center_topics) - 2:  # 相邻或首尾
            t1, t2 = center_topics[i], center_topics[j]
            u1, u2 = topic_centers[t1], topic_centers[t2]
            key = tuple(sorted([u1, u2]))
            if key not in link_set:
                link_set.add(key)
                links.append({"source": u1, "target": u2, "weight": 1})

# ── 7. 统计度 ──
node_degree = defaultdict(int)
for l in links:
    node_degree[l["source"]] += 1
    node_degree[l["target"]] += 1

# ── 8. 构建节点 ──
topic_counts = defaultdict(int)
topic_colors = {
    "visa": "#2471a3", "migration": "#2980b9", "job": "#c0392b",
    "living": "#1e8449", "major": "#e67e22", "assessment": "#d35400",
    "study": "#7f8c8d", "policy": "#8e44ad", "finance": "#9b59b6",
    "university": "#16a085", "regional": "#27ae60", "language": "#f39c12"
}
topic_zh = {
    "visa": "签证", "migration": "移民", "job": "就业", "living": "生活",
    "major": "专业", "assessment": "职业评估", "study": "留学",
    "policy": "政策", "finance": "资金", "university": "大学",
    "regional": "偏远地区", "language": "语言"
}

nodes = []
for c in cards:
    uid = c["_uid"]
    primary = c["_primary"]
    topic_counts[primary] += 1

    title = c.get("title", "").strip()
    short = title
    if len(short) > 9:
        short = short[:9] + "…"

    deg = node_degree.get(uid, 0)
    is_center = (uid == topic_centers.get(primary))
    nodes.append({
        "id": uid,
        "title": title,
        "shortTitle": short,
        "subtitle": c.get("subtitle", "").strip(),
        "topic": primary,
        "topic_zh": topic_zh.get(primary, primary),
        "group": primary,
        "degree": deg,
        "isCenter": is_center
    })

# 孤立节点 fallback
for n in nodes:
    if n["degree"] == 0:
        same = [m for m in nodes if m["topic"] == n["topic"] and m["id"] != n["id"]]
        if same:
            best = max(same, key=lambda x: x["degree"])
            links.append({"source": n["id"], "target": best["id"], "weight": 1})
            n["degree"] = 1
            best["degree"] += 1

node_degree = defaultdict(int)
for l in links:
    node_degree[l["source"]] += 1
    node_degree[l["target"]] += 1
for n in nodes:
    n["degree"] = node_degree.get(n["id"], 0)

# 统计跨主题连接
cross_topic_count = 0
for l in links:
    s = next((n for n in nodes if n["id"] == l["source"]), None)
    t = next((n for n in nodes if n["id"] == l["target"]), None)
    if s and t and s["topic"] != t["topic"]:
        cross_topic_count += 1

# ── 9. 图例 ──
legend_items = []
for t in ["visa", "migration", "job", "living", "major", "assessment",
           "study", "policy", "finance", "university", "regional", "language"]:
    count = topic_counts.get(t, 0)
    if count > 0:
        legend_items.append(
            f'<div><span class="legend-dot" style="background:{topic_colors[t]}"></span>{topic_zh.get(t,t)} ({count})</div>'
        )
legend_html = "\n".join(legend_items)

# ── 10. 计算主题聚类位置（均匀分布在椭圆上）──
active_topics = sorted([t for t in topic_counts if topic_counts[t] > 0])
n_topics = len(active_topics)
cluster_centers = {}
for idx, t in enumerate(active_topics):
    angle = 2 * math.pi * idx / n_topics - math.pi / 2
    cluster_centers[t] = {"x": math.cos(angle), "y": math.sin(angle)}

# ── 11. 生成 HTML ──
nodes_json = json.dumps(nodes, ensure_ascii=False)
links_json = json.dumps(links, ensure_ascii=False)

domain = ["visa", "migration", "job", "living", "major", "assessment",
          "study", "policy", "finance", "university", "regional", "language"]
range_colors = [topic_colors[d] for d in domain]

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>澳洲策略知识图谱</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"
        onerror="this.onerror=null;this.src='./d3.min.js'"
        integrity="sha256-..." crossorigin="anonymous"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: system-ui, "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #f8f9fa;
    overflow: hidden;
    height: 100vh;
}}
.header {{
    position: absolute;
    top: 0; left: 0; right: 0;
    z-index: 10;
    padding: 16px 24px;
    background: linear-gradient(180deg, #f8f9fa 60%, transparent);
    pointer-events: none;
}}
.header h1 {{
    font-size: 20px;
    font-weight: 700;
    color: #1a1a2e;
}}
.header p {{
    font-size: 13px;
    color: #888;
    margin-top: 3px;
}}
.tooltip {{
    position: absolute;
    z-index: 20;
    background: rgba(30,30,40,0.92);
    color: #fff;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    pointer-events: none;
    opacity: 0;
    transition: opacity .15s;
    max-width: 320px;
    line-height: 1.6;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}}
.tooltip.show {{ opacity: 1; }}
.legend {{
    position: absolute;
    bottom: 20px;
    left: 20px;
    z-index: 10;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(8px);
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 13px;
    line-height: 2;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06);
    max-width: 200px;
}}
.legend-dot {{
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 7px;
    vertical-align: middle;
}}
.legend-title {{
    font-weight: 600;
    margin-bottom: 4px;
    font-size: 14px;
    color: #333;
}}
.stats {{
    position: absolute;
    bottom: 20px;
    right: 20px;
    z-index: 10;
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(8px);
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 12px;
    color: #666;
    line-height: 1.6;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    text-align: right;
}}
.link {{
    stroke: #bbb;
    stroke-opacity: 0.5;
    transition: stroke-opacity 0.2s, stroke 0.2s;
}}
.link:hover {{
    stroke-opacity: 0.9;
    stroke: #666;
}}
.link-cross {{
    stroke-dasharray: 4, 4;
    stroke: #999;
    stroke-opacity: 0.4;
}}
.node-label {{
    font-size: 10px;
    fill: #444;
    pointer-events: none;
    text-anchor: middle;
    font-weight: 500;
    text-shadow: 0 1px 2px rgba(255,255,255,0.8), 0 1px 3px rgba(255,255,255,0.6);
}}
.node-circle {{
    cursor: grab;
    transition: r 0.2s;
}}
.node-circle:hover {{
    stroke: #ffd700 !important;
    stroke-width: 3 !important;
}}
</style>
</head>
<body>

<div class="header">
  <h1>🔗 澳洲策略知识图谱</h1>
  <p>节点 = 知识卡片 | 连线 = 标签共现关联 | 悬停看详情 | 拖拽移动 | 滚轮缩放</p>
</div>

<div class="tooltip" id="tooltip"></div>

<div class="legend">
  <div class="legend-title">📂 主题分类</div>
  {legend_html}
  <div style="margin-top:8px;padding-top:6px;border-top:1px solid #eee;color:#999;font-size:11px;">
    共 {len(nodes)} 张卡片 · {len(links)} 条关联
  </div>
</div>

<div class="stats" id="stats"></div>

<svg id="graph" width="100%" height="100%"></svg>

<script>
// 数据
var nodes = {nodes_json};
var links = {links_json};

var width = window.innerWidth;
var height = window.innerHeight;
var svg = d3.select("#graph");
var g = svg.append("g");

// Zoom
var zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", function(e) {{
        g.attr("transform", e.transform);
    }});
svg.call(zoom);

// Colors
var color = d3.scaleOrdinal()
    .domain({json.dumps(domain, ensure_ascii=False)})
    .range({json.dumps(range_colors, ensure_ascii=False)});

// Stats
var stats = d3.select("#stats");
stats.html(
    '<div style="font-weight:600;color:#333">图谱概览</div>' +
    '节点: <b>' + nodes.length + '</b> | ' +
    '关联: <b>' + links.length + '</b>'
);

// 节点半径
var maxDegree = d3.max(nodes, function(d) {{ return d.degree; }});
var rScale = d3.scaleSqrt()
    .domain([0, maxDegree || 1])
    .range([6, 14]);

// 聚类中心位置
var clusterRadius = Math.min(width, height) * 0.32;
var clusterCenters = {json.dumps(cluster_centers, ensure_ascii=False)};

// 为每个节点设置初始位置（围绕主题中心随机分布）
nodes.forEach(function(d) {{
    var c = clusterCenters[d.topic];
    if (c) {{
        var angle = Math.random() * 2 * Math.PI;
        var dist = Math.random() * 30 + 10;
        d.x = width / 2 + c.x * clusterRadius + Math.cos(angle) * dist;
        d.y = height / 2 + c.y * clusterRadius + Math.sin(angle) * dist;
        d.vx = 0;
        d.vy = 0;
    }}
}});

// 判断是否为跨主题连接
function isCrossTopic(l) {{
    var s = nodes.find(function(n) {{ return n.id === ((typeof l.source === 'object') ? l.source.id : l.source); }});
    var t = nodes.find(function(n) {{ return n.id === ((typeof l.target === 'object') ? l.target.id : l.target); }});
    if (!s || !t) return false;
    return s.topic !== t.topic;
}}

// Force simulation - 强聚类引力
var sim = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links)
        .id(function(d) {{ return d.id; }})
        .distance(function(l) {{
            return isCrossTopic(l) ? 200 : 70;
        }})
        .strength(function(l) {{
            return isCrossTopic(l) ? 0.01 : 0.12;
        }}))
    .force("charge", d3.forceManyBody()
        .strength(function(d) {{
            return -30 - d.degree * 2;
        }})
        .distanceMax(200))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide()
        .radius(function(d) {{ return rScale(d.degree) + 5; }})
        .strength(0.4))
    .force("clusterX", d3.forceX(function(d) {{
        var c = clusterCenters[d.topic];
        return c ? (width / 2 + c.x * clusterRadius) : width / 2;
    }}).strength(0.15))
    .force("clusterY", d3.forceY(function(d) {{
        var c = clusterCenters[d.topic];
        return c ? (height / 2 + c.y * clusterRadius) : height / 2;
    }}).strength(0.15));

// Links
var link = g.append("g")
    .attr("class", "links")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("class", function(l) {{
        return isCrossTopic(l) ? "link link-cross" : "link";
    }})
    .attr("stroke-width", function(l) {{
        return Math.max(0.6, l.weight * 0.5);
    }});

// Nodes
var node = g.append("g")
    .attr("class", "nodes")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .call(d3.drag()
        .on("start", function(e, d) {{
            if (!e.active) sim.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }})
        .on("drag", function(e, d) {{
            d.fx = e.x;
            d.fy = e.y;
        }})
        .on("end", function(e, d) {{
            if (!e.active) sim.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}));

node.append("circle")
    .attr("class", "node-circle")
    .attr("r", function(d) {{ return rScale(d.degree); }})
    .attr("fill", function(d) {{ return color(d.group); }})
    .attr("stroke", "#fff")
    .attr("stroke-width", 2);

node.append("text")
    .attr("class", "node-label")
    .text(function(d) {{ return d.shortTitle; }})
    .attr("dy", function(d) {{ return rScale(d.degree) + 13; }});

// Tooltip
var tooltip = d3.select("#tooltip");

node.on("mouseenter", function(e, d) {{
    d3.select(this).select("circle")
        .attr("stroke", "#ffd700")
        .attr("stroke-width", 3);

    var connected = links.filter(function(l) {{
        var s = (typeof l.source === 'object') ? l.source.id : l.source;
        var t = (typeof l.target === 'object') ? l.target.id : l.target;
        return s === d.id || t === d.id;
    }});

    tooltip.html(
        '<b>' + d.title + '</b><br>' +
        '<span style="opacity:0.7">' + d.topic_zh + (d.subtitle ? ' · ' + d.subtitle : '') + '</span><br>' +
        '<span style="opacity:0.5;font-size:11px">关联 ' + connected.length + ' 张卡片</span>'
    ).classed("show", true);
}})
.on("mousemove", function(e) {{
    tooltip.style("left", (e.pageX + 16) + "px")
           .style("top", (e.pageY - 12) + "px");
}})
.on("mouseleave", function() {{
    d3.select(this).select("circle")
        .attr("stroke", "#fff")
        .attr("stroke-width", 2);
    tooltip.classed("show", false);
}});

// Tick
sim.on("tick", function() {{
    link
        .attr("x1", function(d) {{ return d.source.x; }})
        .attr("y1", function(d) {{ return d.source.y; }})
        .attr("x2", function(d) {{ return d.target.x; }})
        .attr("y2", function(d) {{ return d.target.y; }});
    node.attr("transform", function(d) {{
        return "translate(" + d.x + "," + d.y + ")";
    }});
}});

// Resize
window.addEventListener("resize", function() {{
    width = window.innerWidth;
    height = window.innerHeight;
    clusterRadius = Math.min(width, height) * 0.32;
    sim.force("center", d3.forceCenter(width / 2, height / 2));
    sim.force("clusterX", d3.forceX(function(d) {{
        var c = clusterCenters[d.topic];
        return c ? (width / 2 + c.x * clusterRadius) : width / 2;
    }}).strength(0.15));
    sim.force("clusterY", d3.forceY(function(d) {{
        var c = clusterCenters[d.topic];
        return c ? (height / 2 + c.y * clusterRadius) : height / 2;
    }}).strength(0.15));
    sim.alpha(0.3).restart();
}});

// 3秒后稳定化
setTimeout(function() {{
    sim.alpha(0.05).restart();
}}, 3000);
</script>
</body>
</html>"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ 已生成：{OUTPUT_HTML}")
print(f"   节点：{len(nodes)}")
print(f"   边：{len(links)}")
print(f"   孤立节点：{sum(1 for n in nodes if n['degree'] == 0)}")
print(f"   跨主题边：{cross_topic_count}")
print(f"   主题数：{n_topics}")
print(f"   主题：{active_topics}")

# ══════════════════════════════════════════
# [FIX] 图谱验证指标 — 终结人工肉眼调试
# ══════════════════════════════════════════
import sys as _sys
do_validate = "--validate" in _sys.argv

# 指标 1: 跨主题连接占比
cross_ratio = cross_topic_count / len(links) * 100 if links else 0

# 指标 2: 孤立率
isolated = sum(1 for n in nodes if n["degree"] == 0)
isolated_ratio = isolated / len(nodes) * 100 if nodes else 0

# 指标 3: 主题内度分布
topic_degrees = defaultdict(list)
for n in nodes:
    topic_degrees[n["topic"]].append(n["degree"])
topic_stats = {}
for t, degs in topic_degrees.items():
    topic_stats[t] = {
        "count": len(degs),
        "avg_degree": sum(degs) / len(degs) if degs else 0,
        "max_degree": max(degs) if degs else 0,
    }

print(f"\n{'='*50}")
print(f"  图谱健康报告")
print(f"{'='*50}")
print(f"  跨主题占比:   {cross_ratio:.1f}% {'✅' if 3 <= cross_ratio <= 40 else '❌ 异常'}"
      f" (理想: 3%-40%)")
print(f"  孤立节点率:   {isolated_ratio:.1f}% {'✅' if isolated_ratio == 0 else '❌ 有孤立'}"
      f" (理想: 0%)")
print(f"  总节点/边:    {len(nodes)}/{len(links)}"
      f" {'✅' if len(links) >= len(nodes) * 1.5 else '⚠ 连接稀疏'}")
print(f"  主题内度分布:")
for t in sorted(topic_stats.keys()):
    s = topic_stats[t]
    flag = "✅" if s["avg_degree"] >= 2 else "⚠ 度偏低"
    print(f"    {t}: {s['count']}节点 / "
          f"平均{s['avg_degree']:.1f}度 / 最高{s['max_degree']}度 {flag}")

# 自动断言（--validate 模式）
if do_validate:
    errors = []
    if isolated_ratio > 0:
        errors.append(f"孤立节点率 {isolated_ratio:.1f}%（应为 0%）")
    if cross_ratio < 3 and n_topics > 1:
        errors.append(f"跨主题比 {cross_ratio:.1f}% 过低（应 ≥3%，多主题时需跨主题连接）")
    if cross_ratio > 50:
        errors.append(f"跨主题比 {cross_ratio:.1f}% 过高（应 ≤50%，过度跨主题会模糊簇结构）")
    if len(links) < len(nodes):
        errors.append(f"边数 {len(links)} < 节点数 {len(nodes)}（图多为树状/断裂）")
    
    if errors:
        print(f"\n  ❌ 验证失败 ({len(errors)} 项):")
        for e in errors:
            print(f"     - {e}")
        _sys.exit(1)
    else:
        print(f"\n  ✅ 验证通过 — 所有指标在健康范围内")
        _sys.exit(0)
