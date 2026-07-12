# personal-kb — 个人知识库系统

> Hermes Agent Skill | AI 驱动的知识闭环：输入 → 索引 → 输出 → 蒸馏 → 图谱

**GitHub**: https://github.com/akonnne/personal-kb

---

## 1. Skill 功能与简介

**personal-kb** 是一个 AI 原生的个人知识库系统。它不是传统工具套一个 AI 壳——每一个环节都由 AI 做决策。

**一句话**：给 AI 一个 URL，它自动抓取、分类、索引、综合、蒸馏、图谱化。

### AI 做了传统工具做不到的事

| 传统工具 | personal-kb（AI驱动） |
|---------|---------------------|
| 手动分类每篇文章 | AI 自动理解内容，匹配主题/标签 |
| 搜索靠关键词 | 全文语义搜索 + 主题聚合 + 跨文档关联 |
| 孤立笔记 | AI 自动发现「A文章的第2点 × B文章的第5点」的隐藏关联 |
| 手动写作 | AI 综合 N 篇素材生成结构化策略文档 |
| 知识在脑子里 | AI 蒸馏成知识卡片 + D3 交互式知识图谱 |
| 定期整理 | AI 定期 Spark 发现「你遗忘的关联」 |

### 一句话召唤

```
帮我建个知识库，主题：python/go/k8s，路径 ~/dev-kb，输出技术路线规划
```

Skill 自动完成：**建目录 → 写系统宪法 → 注册主题 → 建风格模板 → 复制脚本 → 初始化数据库 → 生成状态报告**。

### 六条核心工作流

```
① 输入  用户给 URL → AI 抓取+自动分类 → input/materials/
                   ↓
② 索引  rebuild_index.py → SQLite+FTS5 全文搜索
                   ↓
③ 输出  用户提需求 → AI 检索+综合 → output/strategies/
                   ↓
④ 蒸馏  distill_cards.py → 知识卡片 + 交互式图谱
                   ↓
⑤ Spark 定期发现 → 找到「遗忘的跨主题关联」
                   ↓
⑥ 问答  用户直接问 → AI 检索数据库+策略文档 → 带引用回答
```

---

## 2. Skill 文件

完整的 Hermes Agent Skill，标准结构：

```
personal-kb/
├── SKILL.md                    # 主文档：触发方式、AI编排流程、脚本使用说明
├── README.md                   # 本文件
├── scripts/                    # 7 个核心 AI 编排脚本
│   ├── db.py                   # SQLite+FTS5 数据库（CJK分词、全文搜索）
│   ├── fetch_material.py       # URL 自动抓取（4级降级+URL去重）
│   ├── batch_fetch.py          # 批量种子抓取
│   ├── rebuild_index.py        # 素材库同步：扫描 → SQLite → status.md
│   ├── generate_status.py      # 状态概览：30秒看懂素材库
│   ├── distill_cards.py        # 知识蒸馏：策略文档 → 卡片 + 概念提取
│   ├── rebuild_graph.py        # 知识图谱渲染（D3.js 聚类引力 + 健康验证）
│   └── test_suite.py           # 自动化测试：22项断言
├── references/                 # 系统文档 + 写作风格模板
│   ├── instruction.md          # 系统宪法（目录、主题、流程）
│   ├── analytic.md             # 分析型风格（结论先行、数据驱动）
│   ├── practical.md            # 实操型风格（Step-by-step、参数标签化）
│   └── inspiring.md            # 激励型风格（从「你」出发、画面感结尾）
├── assets/
│   └── topics.json             # 主题注册模板（12个预设主题+关键词）
├── docs/
│   ├── iteration-log.md        # 迭代升级说明（5步迭代法 × 2轮）
│   └── test-record.md          # 测试记录（环境、步骤、结果）
└── test-workspace/             # 完整测试数据集
    ├── input/materials/         # 14篇真实来源文章
    ├── output/strategies/       # 6篇 AI 策略文档
    ├── output/cards/            # 77张卡片 + 知识图谱
    └── system/                  # SQLite + status + topics
```

**核心特点**：
- 脚本基于 `__file__` 自动解析 workspace 路径，可在任意目录部署
- DB 名自动取 workspace 目录名（`my-kb.db`），多 workspace 不冲突
- 主题色 HSL 色环自动扩展，不限 12 个主题上限
- 卡片 ID 含源文件 MD5 hash，杜绝跨文档碰撞

---

## 3. 测试数据

使用**真实网络文章**作为测试数据集，非模拟数据：

### 输入素材（14 篇真实来源）

| 主题 | 数量 | 示例标题 | 来源 |
|------|------|---------|------|
| assessment | 3 | ACS 职业评估申请步骤 2026 | m.aoji.cn |
| assessment | 3 | EA 工程师认证路径与移民指南 | m.aoji.cn |
| assessment | 3 | VETASSESS 全流程避坑指南 | aunavigator.cn |
| language | 3 | 雅思4个8备考攻略 | aoji.cn |
| language | 3 | 2026英语要求：5大等级+8类考试 | sohu.com |
| language | 3 | IELTS vs OET vs PTE 比较 | firstmigrationservice.com |
| policy | 3 | 2026-27移民配额公布 | daoao.com.au |
| policy | 3 | 雇主担保薪资+签证费变化 | hallandwilcox.com.au |
| policy | 3 | 7月1日综合移民变化 | unitemigration.com.au |
| visa | 5 | 489/WHV/留学申请/城市气候等 | 多家来源 |

### 策略文档（6 篇 AI 生成）

| 策略 | 主题 | 来源素材 | 核心内容 |
|------|------|---------|---------|
| 职业评估实战策略 | assessment | 3篇真文 | ACS/EA/VETASSESS 对比 + 5大失败原因 |
| 英语考试策略 | language | 3篇真文 | 5大等级 + 4门考试 + PTE杠铃风险 |
| 2026政策变化解读 | policy | 3篇真文 | 配额洗牌 + 薪资 + 签证费暴涨 |
| IT 189 vs 190 | visa | 数据库 | 获邀分数对比 |
| 紧缺职业清单 | major | 数据库 | MLTSSL/STSOL/ROL |
| 城市与地区选择 | regional | 数据库 | 6城市对比 |

### 蒸馏产出

```
distill_cards.py 执行结果：
  发现 10 篇策略文档
  总计: 77 张卡片, 2049 条连接
  含: 表格提取 + 核心要点 + 概念定义 + 跨主题连接
```

---

## 4. 测试记录

### 测试环境

| 项目 | 值 |
|------|-----|
| OS | Windows 11 (build 22631) |
| Python | 3.13.12 |
| SQLite | 3.45+ (FTS5 enabled) |
| 浏览器 | WorkBuddy 内置 D3 预览 |
| 测试时间 | 2026-07-12 |
| 测试脚本 | test_suite.py |

### 自动化测试结果（22/22 通过）

```
📋 Test 1: rebuild_index.py — SQLite 索引同步
  ✅ 同步完成 | DB自动命名 | status.md 生成

📋 Test 2: distill_cards.py — 知识蒸馏
  ✅ 77卡片 | 2049连接 | 77/77 multi-topic | 概念提取 ✅

📋 Test 3: rebuild_graph.py — 知识图谱
  ✅ --validate 健康报告 | 0孤立节点 | D3渲染 OK

📋 Test 4: 增量蒸馏（幂等性）
  ✅ 次轮全部跳过 | 卡片数一致
```

### 全程测试步骤

| 步骤 | 命令 | 结果 |
|------|------|------|
| 1 | `python scripts/rebuild_index.py` | **63条记录 ✅** |
| 2 | `python scripts/distill_cards.py` | **77卡 / 2049连接 ✅** |
| 3 | `python scripts/rebuild_graph.py --validate` | **验证通过 ✅** |
| 4 | 再次运行 `distill_cards.py` | **10篇全部跳过 ✅** |
| 5 | `python scripts/test_suite.py` | **22/22通过 ✅** |

详细测试记录见 [docs/test-record.md](https://github.com/akonnne/personal-kb/blob/master/docs/test-record.md)。

---

## 5. Skill 迭代升级说明（5 步迭代法）

完整记录见 [docs/iteration-log.md](https://github.com/akonnne/personal-kb/blob/master/docs/iteration-log.md)。

### 第一轮迭代：跨主题连接 + 布局稳定性

| 步骤 | 内容 |
|------|------|
| **痛点** | 知识图谱中不同颜色主题簇之间完全无连接，图形成「多个孤岛」 |
| **量化影响** | 跨主题边数 = 0 / 占比 = 0% / 用户反馈「没有连接」 |
| **根因分析** | 纯 tag 共现策略：不同策略文档的标签天然无交集（「职业评估」vs「雅思」vs「政策」） |
| **实现方案** | topic 追加到 tag → tag ×3 + topic 权重 → 每个节点 top 3 同主题 + top 2 跨主题 |
| **评估效果** | 跨主题边 0 → 94，但弱连接把布局拉伸分散，引出第二轮迭代 |

| 步骤 | 内容 |
|------|------|
| **痛点** | 图谱布局被 94 条跨主题弱连接拉伸分散，簇漂移 |
| **量化影响** | 边数 927→205→159，跨主题 94→0→14，历经 v3-v7 五个版本 |
| **根因分析** | 纯力导向无法同时满足「簇内紧凑 + 跨主题桥梁 + 整体紧凑」三角 |
| **实现方案** | 聚类引力（forceX/Y strength=0.15）+ 预定位初始化 + 中心节点只连簇中心 |
| **评估效果** | 7 主题簇均匀分布，14 条跨主题虚线，0 孤立节点，`--validate` 自动断言 |

### 第二轮迭代：增强信息提取 + 系统健壮性

| 步骤 | 内容 |
|------|------|
| **痛点** | 蒸馏只提取表格和结论，漏掉 `**概念**: 定义` 格式的关键知识 |
| **量化影响** | 7 篇策略 → 0 张概念卡片，大量定义性知识点丢失 |
| **根因分析** | 正则只匹配 `###` 和表格，未识别 Markdown 加粗定义模式 |
| **实现方案** | 新增 `**概念**: 定义` 正则提取器 + 6 种结论标题 fallback + 终极段落降级 |
| **评估效果** | 每篇策略自动提取 6-23 个关键概念，3 篇新策略 → 36 个概念 |

### 全量痛点修复一览（10/10）

| 优先级 | 痛点 | 修复 | 验证 |
|--------|------|------|------|
| P0 | tag 不跨主题 | topic 追加到 tag | 连接数 +110% |
| P0 | 图谱调试靠肉眼 | `--validate` 模式 | 健康报告 ✅ |
| P1 | DB 名硬编码 | 取 workspace 目录名 | 多 workspace 不冲突 ✅ |
| P1 | 蒸馏格式敏感 | 6 种 fallback + 降级 | 容错率提升 ✅ |
| P2 | 无增量蒸馏 | mtime + cards 双缓存 | 次轮全部跳过 ✅ |
| P2 | 测试靠手动 | test_suite.py | 22/22 通过 ✅ |
| P3 | D3 离线 | onerror 回退 | 本地 fallback ✅ |
| N1 | ID 跨文档碰撞 | 加源文件 hash | 全局唯一 ✅ |
| N2 | 主题色硬编码 | HSL 色环自动扩展 | 无限主题 ✅ |
| N3 | URL 去重 | SQLite source_url 查重 | 重复跳过 ✅ |
| N4 | 概念提取 | `**概念**: 定义` 正则 | 36 概念/3 篇 ✅ |

---

## 6. GitHub 仓库地址

**所有代码、数据、测试记录统一提交至**：

https://github.com/akonnne/personal-kb

```
提交历史:
6a45b0f v3: 基于真实网络文章重新生成3篇策略文档
969f980 README: 重写为5项交付报告结构
6dffdb5 docs: 测试记录更新 + 22/22通过
a7fb303 第二轮迭代: N1-N4 痛点修复
fb90cbc 第一轮迭代: P1/P2/P3 剩余痛点修复
0f46cf0 P0 修复: tag跨主题 + 图谱验证 + 增量蒸馏
9be0604 README.md
d1a618d 真实测试数据
2a5e054 初始版本
```
