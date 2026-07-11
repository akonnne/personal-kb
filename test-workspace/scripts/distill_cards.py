#!/usr/bin/env python3
"""
知识蒸馏系统：从策略文档提取知识卡片，构建知识图谱数据。
"""

import json, re, os, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
STRATEGIES_DIR = ROOT / "output" / "strategies"
CARDS_DIR = ROOT / "output" / "cards"
CARDS_DIR.mkdir(parents=True, exist_ok=True)


def parse_frontmatter(text):
    """解析 YAML frontmatter"""
    m = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith('['):
                val = [v.strip().strip('"').strip("'") for v in val.strip('[]').split(',') if v.strip()]
            fm[key] = val
    return fm, m.group(2).strip()


def make_card_id(title, idx):
    slug = re.sub(r'[^\w\u4e00-\u9fff]', '', title)[:12]
    return f"card-{slug}-{idx:02d}"


def extract_cards(strategy_path):
    """从策略文档提取知识卡片"""
    text = strategy_path.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(text)
    
    title = fm.get('title', strategy_path.stem)
    topic = fm.get('topic', [])
    if isinstance(topic, list):
        topic = topic
    tags = fm.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    # [FIX] tag 跨主题：把文档的 topic 追加到 tag，消除跨主题盲区
    tags = list(set(tags + topic))
    
    source = strategy_path.name
    cards = []
    
    # 提取 ### 级别的标题及其下方内容作为卡片候选
    sections = re.split(r'\n(?=###\s)', body)
    
    for i, sec in enumerate(sections):
        lines = sec.strip().split('\n')
        sec_title = ""
        for line in lines:
            if line.startswith('### '):
                sec_title = line[4:].strip()
                break
        
        # 跳过太短的、无意义的内容
        if not sec_title or len(sec_title) < 2:
            continue
        if sec_title in ['核心结论', '行动建议', '常见误区', '分析', '通用建议']:
            continue  # 这些会专门处理
            
        # 提取表格
        tables = re.findall(r'\|[^\n]+\|[^\n]*\|(?:\n\|[^\n]+\|)*', sec)
        
        # 提取关键数字行
        key_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('- **') or line.startswith('1. **') or line.startswith('2. **'):
                key_lines.append(line)
        
        # 表格是最有价值的结构化知识
        for ti, table in enumerate(tables):
            rows = table.strip().split('\n')
            if len(rows) < 3:  # 至少需要表头+分隔+数据
                continue
            headers = [h.strip() for h in rows[0].strip('|').split('|')]
            data_rows = []
            for row in rows[2:]:  # 跳过表头和分隔行
                cells = [c.strip() for c in row.strip('|').split('|')]
                if cells:
                    data_rows.append(cells)
            
            card_id = make_card_id(sec_title, ti)
            card = {
                "id": card_id,
                "type": "card",
                "title": sec_title,
                "subtitle": f"表格: {' vs '.join(headers[:2])}" if len(headers) >= 2 else headers[0],
                "topic": topic,
                "tags": tags,
                "source": source,
                "table_headers": headers,
                "table_data": data_rows,
                "summary": "",
            }
            cards.append(card)
    
    # 提取核心结论段落
    conclusion_match = re.search(r'## 核心结论\n\n(.*?)(?:\n\n##|\Z)', body, re.DOTALL)
    if conclusion_match:
        concl_text = conclusion_match.group(1).strip()
        # 拆成多个要点
        points = []
        for line in concl_text.split('\n'):
            line = line.strip()
            if line.startswith('**') or line.startswith('- **') or re.match(r'^\d+\.', line):
                points.append(line.lstrip('- ').strip())
        
        if points:
            card = {
                "id": make_card_id("核心结论", 0),
                "type": "card",
                "title": f"{title} — 核心结论",
                "subtitle": "",
                "topic": topic,
                "tags": tags,
                "source": source,
                "key_points": points,
                "summary": "",
            }
            cards.append(card)
    
    return cards


def main():
    # [FIX] 增量蒸馏：记录 mtime，只重新提取变化的文件
    cache_path = CARDS_DIR / ".distill_cache.json"
    cards_cache_path = CARDS_DIR / ".distill_cards_cache.json"
    
    mtime_cache = {}
    cards_cache = {}
    if cache_path.exists():
        mtime_cache = json.loads(cache_path.read_text(encoding='utf-8'))
    if cards_cache_path.exists():
        cards_cache = json.loads(cards_cache_path.read_text(encoding='utf-8'))
    
    strategy_files = sorted(STRATEGIES_DIR.glob("*.md"))
    print(f"发现 {len(strategy_files)} 篇策略文档")
    
    all_cards = []
    changed = 0
    skipped = 0
    for sf in strategy_files:
        mtime = sf.stat().st_mtime
        key = sf.name
        if key in mtime_cache and mtime_cache[key] >= mtime and key in cards_cache:
            skipped += 1
            all_cards.extend(cards_cache[key])
            print(f"  ⏭ {sf.name}: 跳过（未变化，{len(cards_cache[key])} 张卡片）")
            continue
        
        changed += 1
        cards = extract_cards(sf)
        mtime_cache[key] = mtime
        cards_cache[key] = cards
        all_cards.extend(cards)
        print(f"  📝 {sf.name}: 提取 {len(cards)} 张卡片")
    
    # 保存缓存
    cache_path.write_text(json.dumps(mtime_cache, ensure_ascii=False), encoding='utf-8')
    cards_cache_path.write_text(json.dumps(cards_cache, ensure_ascii=False), encoding='utf-8')
    
    # 全量重建卡片间连接（索引不变，但连接需要全量重算）
    card_links = []
    for i, c in enumerate(all_cards):
        for j in range(i + 1, len(all_cards)):
            oc = all_cards[j]
            shared_topics = set(c.get('topic', []) or []) & set(oc.get('topic', []) or [])
            shared_tags = set(c.get('tags', []) or []) & set(oc.get('tags', []) or [])
            if len(shared_topics) >= 2 or len(shared_tags) >= 3:
                card_links.append({
                    "source": c["id"],
                    "target": oc["id"],
                    "weight": len(shared_topics) * 2 + len(shared_tags)
                })
    index = {
        "total_cards": len(all_cards),
        "total_links": len(card_links),
        "cards": all_cards,
        "links": card_links
    }
    
    index_path = CARDS_DIR / "card_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"\n总计: {len(all_cards)} 张卡片, {len(card_links)} 条连接")
    print(f"已写入: {index_path}")
    
    # 也生成知识图谱 HTML
    generate_graph_html(all_cards, card_links)


def generate_graph_html(cards, links):
    """生成知识图谱 HTML"""
    # 按主题分组统计
    topic_counts = {}
    for c in cards:
        for t in (c.get('topic', []) or []):
            topic_counts[t] = topic_counts.get(t, 0) + 1
    
    # 简化为 graph 可用的数据
    graph_nodes = []
    seen_titles = {}
    for c in cards:
        t = c.get('title', '')
        if t not in seen_titles:
            seen_titles[t] = 0
            topics = c.get('topic', []) or []
            graph_nodes.append({
                "id": c["id"],
                "title": t,
                "subtitle": c.get("subtitle", ""),
                "topic": topics[0] if topics else "general",
                "group": topics[0] if topics else "general"
            })
    
    # 写 HTML
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>澳洲知识图谱 — 知识卡片关联</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:system-ui,sans-serif; background:#f8f9fa; overflow:hidden; height:100vh; }
.header { position:absolute; top:0; left:0; right:0; z-index:10; padding:16px 24px; background:linear-gradient(180deg,#f8f9fa 60%,transparent); }
.header h1 { font-size:18px; font-weight:600; color:#1a1a2e; }
.header p { font-size:13px; color:#666; margin-top:2px; }
.tooltip { position:absolute; z-index:20; background:rgba(0,0,0,0.85); color:#fff; padding:8px 12px; border-radius:8px; font-size:12px; pointer-events:none; opacity:0; transition:opacity .15s; max-width:300px; line-height:1.5; }
.tooltip.show { opacity:1; }
.legend { position:absolute; bottom:24px; left:24px; z-index:10; background:rgba(255,255,255,0.92); backdrop-filter:blur(8px); border:1px solid #e0e0e0; border-radius:10px; padding:12px 16px; font-size:12px; line-height:2; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.legend-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle; }
</style>
</head>
<body>
<div class="header"><h1>澳洲策略知识图谱</h1><p>节点=知识卡片 | 连线=主题关联 | 悬停看详情 | 拖拽移动</p></div>
<div class="tooltip" id="tooltip"></div>
<div class="legend">
"""
    colors = {"visa":"#2471a3","migration":"#2471a3","job":"#c0392b","living":"#1e8449","major":"#c0392b","assessment":"#d35400","study":"#7f8c8d","policy":"#8e44ad","finance":"#9b59b6","university":"#2980b9","regional":"#1e8449","language":"#f39c12"}
    for t, c in sorted(topic_counts.items(), key=lambda x:-x[1]):
        col = colors.get(t, "#95a5a6")
        html += f'<div><span class="legend-dot" style="background:{col}"></span>{t} ({c})</div>\n'
    
    html += f'<div style="margin-top:6px;padding-top:6px;border-top:1px solid #eee">共 {len(graph_nodes)} 张知识卡片</div>'
    html += '</div><svg id="graph" width="100%" height="100%"></svg><script>\n'
    
    # 嵌入数据
    html += f'const data = {json.dumps({"nodes": graph_nodes, "links": links}, ensure_ascii=False)};\n'
    
    html += """
const width = window.innerWidth, height = window.innerHeight;
const svg = d3.select("#graph");
const g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.3,3]).on("zoom",e=>g.attr("transform",e.transform)));

const color = d3.scaleOrdinal()
  .domain(["visa","migration","job","living","major","assessment","study","policy","finance","university","regional","language"])
  .range(["#2471a3","#2471a3","#c0392b","#1e8449","#c0392b","#d35400","#7f8c8d","#8e44ad","#9b59b6","#2980b9","#1e8449","#f39c12"]);

const sim = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.links).id(d=>d.id).distance(120).strength(l=>l.weight/20))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(width/2, height/2))
  .force("collision", d3.forceCollide(25));

const link = g.append("g").selectAll("line").data(data.links).join("line")
  .attr("stroke","#999").attr("stroke-width",l=>Math.max(0.5,l.weight*0.3)).attr("stroke-opacity",0.3);

const node = g.append("g").selectAll("g").data(data.nodes).join("g")
  .call(d3.drag().on("start",(e,d)=>{if(!e.active)sim.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y;})
    .on("drag",(e,d)=>{d.fx=e.x;d.fy=e.y;})
    .on("end",(e,d)=>{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}));

node.append("circle").attr("r",12).attr("fill",d=>color(d.group)).attr("stroke","#fff").attr("stroke-width",2).style("cursor","grab");
node.append("text").text(d=>d.title.substring(0,12)).attr("text-anchor","middle").attr("dy",24)
  .attr("font-size","11px").attr("fill","#333").style("pointer-events","none");

const tooltip = d3.select("#tooltip");
node.on("mouseenter",function(e,d){
  d3.select(this).select("circle").attr("stroke","#ffd700").attr("stroke-width",3);
  tooltip.html(`<b>${d.title}</b><br><span style="opacity:0.7">${d.subtitle || d.group}</span>`).classed("show",true);
}).on("mousemove",e=>tooltip.style("left",(e.pageX+14)+"px").style("top",(e.pageY-10)+"px"))
  .on("mouseleave",function(){d3.select(this).select("circle").attr("stroke","#fff").attr("stroke-width",2);tooltip.classed("show",false);});

sim.on("tick",()=>{
  link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
  node.attr("transform",d=>`translate(${d.x},${d.y})`);
});
</script></body></html>"""
    
    graph_path = CARDS_DIR / "knowledge_graph.html"
    with open(graph_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"知识图谱: {graph_path}")
    
    # 也打印卡片清单
    print(f"\n=== 知识卡片清单 ===")
    for c in cards:
        topics = ', '.join(c.get('topic', []) or [])
        has_table = 'table_data' in c and c['table_data']
        has_points = 'key_points' in c and c['key_points']
        note = ""
        if has_table: note += f"[表格 {len(c['table_data'])}行] "
        if has_points: note += f"[{len(c['key_points'])}要点]"
        print(f"  [{topics}] {c['title']} {note}")


if __name__ == "__main__":
    main()
