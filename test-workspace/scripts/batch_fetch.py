#!/usr/bin/env python3
"""
批量抓取脚本 — 从 URL 列表批量抓取澳洲信息文章并导入系统

使用 readability-lxml + html2text 抓取正文（已在系统 Python 中安装）
"""

import sys
import os
import json
import re
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from fetch_material import save_material_from_content, BEIJING_TZ, now_ts, slugify

INPUT_MATERIALS = PROJECT_ROOT / "input" / "materials"
TOPICS_FILE = PROJECT_ROOT / "system" / "topics.json"

# ===== URL 列表 =====
# 格式: (url, note)
URL_LIST = [
    # === 签证政策 (visa) ===
    ("https://atme.com.au/2026/06/04", "2026-27财年澳洲移民重大变化：189配额增加、雇主担保大涨、偏远地区削减"),
    ("https://firstmigrationservice.com/zh-tw/news/2026-27-migration-allocations-regional-cut", "2026-27各签证子类别配额公布：491区域签证大砍57%"),
    ("https://www.apearth.com/article/detail/35955", "2026澳洲移民新政策全景：投资技术通道门槛变动"),
    ("https://adlyym.immiknow.com/yimin/26060531966.html", "澳洲五大移民签证全解：打分制技术与雇主担保选签指南"),

    # === 留学申请 (study) ===
    ("https://liuxue.xdf.cn/news/bj_7991645.shtml", "2026澳洲学签大洗牌：GTE已成过去式，GS才是新主角"),
    ("https://studycentralau.com/yipo", "2026澳洲留学申请文件准备：SOP、CV、推荐信完整攻略与GS要求"),
    ("https://m.aoji.cn/news/2792357.html", "澳大利亚留学需要准备什么：2026年材料清单与时间规划"),

    # === 移民路径 (migration) ===
    ("https://jindingvisa.com/news_info/bmV3czEwMDE1MzE1.html", "2026年澳洲技术移民五大签证全解析：从189到186如何精准选路"),
    ("https://m.aoji.cn/news/2793293.html", "澳洲PR到底好不好拿：2026年留学生移民真实难度"),
    ("https://ozvisalink.com/2026%e6%be%b3%e6%b4%b2%e7%a7%bb%e6%b0%91%e6%8c%87%e5%8d%97/", "2026澳洲移民终极指南：路径、条件、流程与最新政策变化"),

    # === 工作机会 (job) ===
    ("https://m.aoji.cn/news/2781306.html", "澳洲最好就业的九大专业：2026年高就业率领域与薪资前景"),
    ("https://m.aoji.cn/news/2780910.html", "澳洲就业前景好的专业有哪些：2025-2026五大高就业领域全解析"),
    ("https://penguineducation.com/?p=5530", "澳洲留学2026热门科系最新排名：AI、工程、护理为什么最抢手"),

    # === 生活成本 (living) ===
    ("https://www.settleau.com.au/blog/cost-of-living-sydney-melbourne-brisbane-comparison", "Cost of Living in Sydney vs Melbourne vs Brisbane 2026对比"),
    ("https://comparemigrationagents.com.au/move-to-australia/cost-of-living-in-australia", "Cost of Living in Australia for Migrants 2026"),
    ("https://www.migrationdirectory.com.au/blog/cost-of-living-in-australia-2026", "澳洲生活成本2026：五大城市月度开销详细对比"),

    # === 语言考试 (language) ===
    ("https://m.aoji.cn/news/2793556.html", "澳洲雅思4个8是什么水平：技术移民加20分说清楚了"),
    ("https://m.aoji.cn/news/2789007.html", "澳洲雅思4个8分难吗：技术移民英语满分备考攻略"),

    # === 院校选择 (university) ===
    ("https://m.aoji.cn/news/2792716.html", "2026年澳洲大学排名一览表：36所大学完整榜单，9所进全球百强"),
    ("https://auspass.co?p=1091/", "澳洲八大留学指南：2026 QS世界排名一览"),
    ("https://sz.xhd.cn/lx/964335.html", "澳洲大学推荐及最新排名：八大名校核心择校亮点"),
    ("https://xiamen.aoji.cn/news/2780478.html", "2026年澳洲八大名校全解析：排名、专业与选校指南"),

    # === 专业方向 (major) ===
    ("https://www.haiyivisa.com/yiminzixun/6087.html", "你的职业能移民澳洲吗：2026紧缺职业清单直接对照"),
    ("https://m.aoji.cn/news/2788051.html", "2026年澳洲什么专业可以留下来：技术移民紧缺清单与五大留澳专业"),
    ("https://www.australianvisaonline.com/reference/skilled-occupation-list-database", "Skilled Occupation List Database 2026：Top 50紧缺职业"),

    # === 政策动态 (policy) ===
    ("https://www.racc.net.au/single-post/australia-migration-changes-from-1-july-2026-full-overview", "2026年7月1日澳洲移民新政全面生效：五大变化详解"),
    ("https://www.163.com/dy/article/L166CU6905383BZI.html", "澳洲狠下心狂砍移民配额：州担保还在线但偏远地区红利走没了"),
    ("https://www.australianmigrationlawyers.com.au/tw/news-and-updates/australia-migration-reforms-2026-skilled-student-visas", "澳洲2026年移民政策变动：技术移民与国际学生需知事项"),

    # === 资金准备 (finance) ===
    ("https://m.aoji.cn/news/2791345.html", "澳洲留学一年要花多少钱：2026年最新费用账单"),
    ("https://www.xhd.cn/liuxuezhuanqu/213555.html", "2026澳大利亚留学费用详解：一年到底要花多少钱"),
    ("https://taiyuan.aoji.cn/news/2791484.html", "澳洲留学费用2026：从学费到生活费每一笔都算给你听"),

    # === 职业评估 (assessment) ===
    ("https://www.joy1996.com/sys-nd/132.html", "澳洲186职业评估没过怎么办：5种常见失败原因与补救方案"),
    ("https://prmate.com.au/blog/skills-assessment-guide-australia", "Skills Assessment Australia 2026: Complete Guide by Occupation"),
    ("http://en.luminagloble.com/article/152", "澳洲移民职业评估全解析：为什么它是技术移民的核心环节"),

    # === 地区选择 (regional) ===
    ("https://www.aoji.cn/news/2797611.html", "移民加20分！澳洲留学学校选偏远地区还是大城市：2026全面对比"),
    ("https://www.aoji.cn/news/2795591.html", "八大区域位置决定留学体验：6座城市6种人生"),
    ("https://m.aoji.cn/news/2794083.html", "澳洲大学排名前十名所在城市：六城市生活成本与气候对比"),

    # === 气候地理 ===
    ("https://www.levelupstudies.com.au/cn/news-detail/australia-7-cities-weather-seasons-guide", "澳洲七大城市天气气候差异与穿衣指南"),
    ("https://guangzhou.aoji.cn/news/2754062.html", "澳大利亚哪个城市气候最好：各城市气候特点及宜居优势"),

    # === 文化社会 ===
    ("https://www.xiaoniucw.com/article/161034", "2026年澳洲华人实况：住哪最多、日子过得咋样"),
    ("https://m.apearth.com/article/detail/36238", "2026澳洲华人数量统计：聚居规模与生活现状"),
    ("http://www.171au.com/yiminsh/10977.html", "华人移民在澳洲的生活状况如何：真实体验"),

    # === 家庭团聚 ===
    ("https://www.evolvelawyers.com.au/chinese-blog/budget2026", "2026预算以及移民配额和政策变更：家庭签证与父母签证分析"),
    ("https://www.racc.net.au/parent-visa-australia", "Parent Visa Australia Complete 2026 Guide：父母签证完全指南"),

    # === 雇主担保 ===
    ("https://firstmigrationservice.com/zh-tw/news/employer-sponsored-visa-comparison-482-186-sid-2026", "482 vs 186 vs SID：雇主担保签证比较2026"),
    ("https://www.globesunshine.com/visasCaseDe_4297.html", "澳洲移民新政风向：这些职业的绿灯已亮起"),

    # === 房产市场 ===
    ("https://everstonefinance.com.au/median-house-prices-australia", "Median House Prices Australia 2026: 澳洲房产市场指南"),
    ("https://www.ausproperty.cn/market/trend/630723.html", "加息挡不住2026年房价再涨：墨尔本要领先悉尼"),
]


def get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


def fetch_html(url, timeout=30):
    """获取 HTML 文本"""
    try:
        import requests as req
        resp = req.get(url, headers={
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/125.0.0.0 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except ImportError:
        pass

    req = urllib.request.Request(url, headers={
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/125.0.0.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml',
    })
    with urllib.request.urlopen(req, timeout=timeout, context=get_ssl_context()) as resp:
        raw = resp.read()
        for enc in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
            try:
                return raw.decode(enc)
            except:
                continue
        return raw.decode('utf-8', errors='replace')


def fetch_via_readability(url):
    """readability-lxml + html2text 抓取正文"""
    from readability import Document
    import html2text

    html = fetch_html(url)
    doc = Document(html)

    title = doc.title()
    content_html = doc.summary()

    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_links = False
    converter.ignore_images = True
    md = converter.handle(content_html)

    # 清理多余空行
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    return md.strip(), title


def extract_title_from_md(md_text):
    lines = md_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# ') and not line.startswith('## '):
            return line[2:].strip()
    if lines and len(lines[0].strip()) > 5:
        return lines[0].strip()[:100]
    return ""


def process_batch(start_idx=0, count=None):
    urls = URL_LIST[start_idx:]
    if count:
        urls = urls[:count]

    success = 0
    fail = 0
    results = []

    for i, (url, note) in enumerate(urls):
        actual_idx = start_idx + i
        print(f"\n{'='*60}")
        print(f"[{actual_idx+1}/{len(URL_LIST)}] {url[:80]}")
        print(f"    备注: {note}")
        print(f"{'='*60}")

        try:
            md, title = fetch_via_readability(url)

            # 如果 readability 没提取到标题，从 md 中提取
            if not title:
                title = extract_title_from_md(md)
            if not title:
                title = urlparse(url).netloc

            body_len = len(md.strip())
            print(f"  标题: {title}")
            print(f"  正文长度: {body_len} 字符")

            if body_len < 100:
                print(f"  ⚠️ 正文过短，可能提取不完整")
                results.append({"url": url, "status": "too_short", "len": body_len, "note": note})
                fail += 1
                continue

            # 调用 fetch_material 的保存函数
            filepath = save_material_from_content(
                url, md,
                title=title,
                note=note,
            )
            results.append({"url": url, "status": "ok", "file": str(filepath)})
            success += 1

        except Exception as e:
            print(f"  ❌ 失败: {type(e).__name__}: {e}")
            results.append({"url": url, "status": "error", "error": str(e), "note": note})
            fail += 1

    print(f"\n{'='*60}")
    print(f"✅ 批量处理完成: 成功 {success}, 失败 {fail}, 总计 {success+fail}")
    print(f"{'='*60}")

    if fail > 0:
        print("\n需要后续处理的URL:")
        for r in results:
            if r["status"] != "ok":
                print(f"  [{r['status']}] {r['url']}")
                print(f"           {r.get('note', '')}")

    # 保存结果
    results_file = PROJECT_ROOT / "output" / "batch_fetch_results.json"
    results_file.parent.mkdir(exist_ok=True)
    results_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n结果已保存到: {results_file}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="批量抓取澳洲信息文章")
    parser.add_argument("--start", type=int, default=0, help="起始索引")
    parser.add_argument("--count", type=int, default=None, help="批量数量")
    parser.add_argument("--test", action="store_true", help="测试模式：只抓取1篇")
    args = parser.parse_args()

    if args.test:
        print("🧪 测试模式：只抓取1篇")
        process_batch(0, 1)
    else:
        process_batch(args.start, args.count)
