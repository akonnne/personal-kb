---
name: personal-kb
description: >
  个人知识库系统（Personal Knowledge Base）。
  当用户需要快速搭建一个带 AI 驱动的知识闭环系统时使用：自动抓取、智能分类、跨主题关联分析、知识蒸馏与图谱化。
  用户只需提供「路径 + 主题列表 + 输出类型」三要素，Skill 自动完成整个知识基础设施搭建。
  触发意图：搭建知识库、建 KM 系统、知识管理、个人知识系统、搞个知识库、知识蒸馏、知识图谱、knowledge base setup。
agent_created: true
---

# personal-kb — AI 驱动的个人知识闭环

## 为什么 AI 是核心

传统 PKM 工具（Notion / Obsidian / Roam）本质上是**文件柜**——你塞什么它存什么，查什么得自己搜。AI 让知识库从"存储"变成了**自生长的认知系统**：

| 传统工具 | AI 知识库 |
|---------|-----------|
| 用户手动分类每篇文章 | AI 自动理解内容并匹配主题/标签 |
| 搜索靠关键词匹配 | 全文语义搜索 + 主题聚合 + 跨文档关联 |
| 笔记是孤立的 | AI 自动发现「A 文章的第 2 点 × B 文章的第 5 点」的隐藏关联 |
| 输出全靠手动写作 | AI 综合 N 篇素材生成结构化策略文档 |
| 知识沉淀在脑子里 | AI 蒸馏成知识卡片 + 交互式知识图谱 |

**AI 做得到、传统工具做不到的三件事：**
1. **抓即分类** — URL 抓来的文章，AI 自动识别它属于哪个主题、贴哪些标签，用户零操作
2. **跨文档关联** — AI 遍历所有文章，发现人类自己都没注意到的跨主题连接（~Spark 发现）
3. **知识蒸馏** — AI 从策略文档中提取结构化表格、关键数据、核心要点，自动构建知识卡片和图谱

## 一句话召唤

```
帮我建个知识库，主题：python/go/k8s/微服务，路径 ~/dev-kb，输出技术路线规划
```

Skill 自动完成：建目录 → 写宪法 → 注册主题 → 建风格模板 → 复制脚本 → 初始化索引 → 生成状态概览。

## 架构全景

```
用户提供URL ──→  AI 自动抓取+分类 ──→  input/materials/(带元数据的Markdown)
                    ↓
          rebuild_index.py ──→  SQLite+FTS5 全文搜索
                    ↓
用户提需求 ──→  AI 检索+综合 ──→  output/strategies/(策略分析文档)
                    ↓
          distill_cards.py ──→  output/cards/(知识卡片 + 交互式图谱)
                    ↓
          定期 Spark 发现 ──→  自动找"遗忘的连接"
```

**这不是脚本流水线，这是 AI 编排的知识生命周期。** 每一步的核心决策都由 AI 完成。

## 目录结构

Skill 创建的标准结构：

```
{workspace}/
├── input/
│   ├── ideas/              ← AI 自动记录的想法
│   ├── materials/          ← AI 抓取+分类后的素材（.md）
│   └── snippets/           ← AI 提取的短片段
├── output/
│   ├── strategies/         ← AI 综合生成的策略文档
│   ├── reports/            ← AI 生成的检查报告
│   └── cards/              ← AI 蒸馏的知识卡片 + 图谱
├── styles/
│   ├── analytic.md         ← 分析型风格（AI 输出模板）
│   ├── practical.md        ← 实操型风格（AI 输出模板）
│   └── inspiring.md        ← 激励型风格（AI 输出模板）
├── system/
│   ├── instruction.md      ← 系统宪法（AI 工作规范）
│   ├── topics.json         ← 主题注册表（AI 分类依据）
│   ├── status.md           ← AI 自动生成的状态快照
│   ├── changelog.md        ← AI 维护的变更日志
│   └── {name}.db           ← SQLite+FTS5 数据库
└── scripts/                ← AI 编排工具集
```

## 初始化流程

路径必填，主题列表和输出类型可选（不从参数读取时，从 instruction.md 读取默认配置）。

### Phase 1：搭骨架（机械操作，一次性的）

创建目录、复制脚本、写入配置文件 —— 这些不需要 AI，但 AI 做的好处是**零遗漏、零差错**：

```bash
mkdir -p {workspace}/input/{ideas,materials,snippets}
mkdir -p {workspace}/output/{strategies,reports,cards}
mkdir -p {workspace}/styles
mkdir -p {workspace}/system
mkdir -p {workspace}/scripts
```

复制脚本到 workspace/scripts/，复制风格模板到 workspace/styles/。

### Phase 2：写宪法（AI 定制）

读取 `assets/topics.json`，用用户主题替换。读取 `references/instruction.md`，用实际路径和主题替换占位符。

**这是 AI 做的关键一步**：instruction.md 定义了 AI 后续所有工作的规范 —— 它告诉 AI 自己"你应该怎么分类、怎么写、怎么索引"。这是系统自指的核心。

### Phase 3：初始化索引（AI 驱动）

运行 `rebuild_index.py`：

```bash
cd {workspace}
python scripts/rebuild_index.py
```

创建 SQLite+FTS5 数据库（WAL 模式，CJK 字符级分词），生成 `system/status.md`。

> **为什么是 SQLite+FTS5 而不是 Elasticsearch？** 因为这是**个人**知识库。不需要运维，不需要集群。FTS5 的中文分词器足够好，SQLite 文件级备份随手可移。

## 日常工作流

### 工作流 1：输入 → AI 自动分类入库

```
用户 → 给 URL → AI 抓取正文 → AI 理解内容 → AI 匹配主题/标签 → 写入 Markdown → 更新索引
```

用户做的事：**只给一个 URL**。
AI 做的事：抓取、解析、去重、分类、标签、归档、索引。

```bash
# 单条（AI 自动完成一切后续）
python scripts/fetch_material.py "https://example.com/article"

# 批量（内置覆盖全部主题的 48 个种子 URL）
python scripts/batch_fetch.py
```

### 工作流 2：输出 → AI 综合生成策略

```
用户 → 提需求 → AI 搜索数据库 → AI 按主题聚合素材 → AI 选风格 → AI 生成策略文档 → 更新索引
```

用户做的事：**说一句"帮我分析 XX 主题"**。
AI 做的事：检索所有相关素材 → 筛选最新/最相关条目 → 按风格模板组织 → 生成带数据支撑的策略文档 → 同步索引。

选择风格（从 `styles/` 加载）：
- **analytic** — 结论先行、数据驱动、对比代替描述。用于政策解读、对比分析
- **practical** — Step-by-step 路线、参数标签化、风险矩阵。用于路线规划、清单
- **inspiring** — 从"你"出发、故事引导、画面感结尾。用于个人陈述、动机信

### 工作流 3：蒸馏 → AI 从文档提取结构化知识

```
AI → 读策略文档 → 识别 ### 章节 → 提取表格 → 提取核心要点 → 计算卡片关联 → 输出 JSON + HTML
```

用户做的事：**啥也不做，自动运行**。
AI 做的事：遍历所有策略文档 → 解析 frontmatter → 提取结构化数据 → 生成知识卡片 → 计算卡片间语义关联 → 构建交互式知识图谱。

```bash
python scripts/distill_cards.py
```

输出：
- `output/cards/card_index.json` — 结构化卡片（含表格数据、关联权重）
- `output/cards/knowledge_graph.html` — D3.js 交互式知识图谱（7 种主题色、聚类引力布局、跨主题虚线）

### 工作流 4：Spark → AI 定期发现"遗忘的连接"

```
AI → 遍历所有素材 → 找出首次/末次差异 → 发现被忽略的关联 → 输出发现报告
```

用户做的事：**每周日 20:00 自动收到飞书消息**。
AI 做的事：对比早期和近期输入 → 识别认知变化 → 找到孤立的跨主题关联 → 生成 Spark 发现。

（需配合自动化定时任务：每周日 20:00 自动执行一次 Spark 分析）

### 工作流 5：健康检查 → AI 自检

```
AI → 检查输入/输出比例 → 检查主题覆盖度 → 检查 Spark 命中率 → 生成健康报告
```

定期自动运行，确保知识库不偏科、不积灰。

### 工作流 6：问答 → AI 即时检索并回答

```
用户提问 → AI 解析关键词 → db.py 全文搜索 → AI 读策略文档+知识卡片 → 综合回答
```

用户做的事：**直接问问题**。任何关于知识库覆盖领域的问题，AI 都从数据库和策略文档中检索答案。

**AI 处理流程**：
1. 解析用户问题中的关键词
2. 用 `db.py` 的 `search()` 函数全文搜索 SQLite
3. 找到关联的素材、策略文档、知识卡片
4. 综合多个来源，给出有引用依据的回答
5. 如果数据库中无匹配结果，诚实告知并建议抓取相关 URL

**回答方式**：
- 引用具体的策略文档或知识卡片作为依据
- 给出可操作的结论（不要泛泛而谈）
- 如果数据不足以回答，主动建议补充方向

**示例对话**：
```
用户: "189 和 190 该选哪个？"
AI: 检索 IT 189 vs 190 策略文档 → 提取获邀分差数据
   → 回答: 对大多数 IT 从业者（EOI 75-90），190 性价比更高。
     189 获邀线 95-100 分，190 在选对州的前提下 75-80 分就有机会，
     分差 15-20 分。（来源: 2026-07-11-strategy-it-189-vs-190.md）

用户: "PTE 冲八炸有什么坑？"
AI: 检索语言策略 + 知识卡片
   → 回答: PTE 2025 年分数对标调整后，听力从 79→88、口语从 79→88，
     意味着之前靠模板刷到 79 的考生现在需要真功夫。
     同时注意「杠铃风险」——PTE AI 评分可能在某单项卡住。
     （来源: 2026-07-12-strategy-language-guide.md）
```

## 核心脚本（scripts/）

这些不是"传统 CLI 工具"，它们是**AI 编排的触手**——每个脚本都依赖 AI 的理解和决策能力：

| 脚本 | AI 做的事 | 传统工具做不到 |
|------|----------|---------------|
| `fetch_material.py` | 理解文章内容 → 自动匹配主题/标签 | URL 下载器只能存 HTML |
| `distill_cards.py` | 识别 ### 章节 → 提取表格 → 结构化知识 | 正则只能匹配格式，不能理解内容 |
| `rebuild_index.py` | 扫描目录 → 读取 frontmatter → 构建全文索引 | 文件列表 ≠ 可搜索的知识库 |
| `generate_status.py` | 统计主题覆盖 → 识别盲区 → 生成状态快照 | 30 秒看清全库状态 |
| `rebuild_graph.py` | 读取卡片关联 → 计算布局 → 渲染 D3 图谱 | 静态 JSON 不等于交互式图谱 |

**用法速查**：

```bash
# 抓取
python scripts/fetch_material.py <url>
python scripts/batch_fetch.py

# 索引
python scripts/rebuild_index.py

# 蒸馏
python scripts/distill_cards.py
python scripts/rebuild_graph.py     # 图谱迭代（最终稳定版）

# 状态
cat system/status.md
```

## 核心参考（references/）

| 文件 | 用途 |
|------|------|
| `instruction.md` | 系统宪法。定义了 AI 自己的行为规范。AI 读取后知道：主题有哪些、目录怎么用、每步怎么做 |
| `analytic.md` | 分析型写作风格。AI 生成策略文档时的输出模板之一 |
| `practical.md` | 实操型写作风格。Step-by-step 模板 |
| `inspiring.md` | 激励型写作风格。叙事模板 |
| `assets/topics.json` | 主题注册表模板。12 个预设主题，每个含中英文名和关键词 |

## 技术要点

- **DB 引擎**：SQLite + FTS5 全文搜索，WAL 模式，CJK 字符级分词。个人使用足够强，零运维
- **抓取降级**：markitdown → Jina AI → readability-lxml → 基础 HTML。4 级降级确保不丢内容
- **主题匹配**：AI 读取 topics.json 的关键词列表 + 理解文章内容 → 自动分类。非关键词匹配，是语义分类
- **命名规范**：`{datetime}-{slug}.md`，6 位时间戳。AI 按规范生成，不乱
- **图谱渲染**：D3.js v7 力导向图，聚类引力布局，7 种主题色，跨主题虚线连接簇中心

## 迁移已有工作目录

如果用户已有知识库目录，Skill 会：
1. 读取现有目录结构和 topics.json
2. 对比标准结构，补全缺失文件（不做全量覆盖）
3. 更新 instruction.md 和 topics.json（保留用户已有配置）
4. 重新索引数据库（增量同步）

增量迁移，不破坏已有数据。
