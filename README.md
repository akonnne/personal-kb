# personal-kb — Hermes Agent Skill 交付报告

**仓库地址**: https://github.com/akonnne/personal-kb

> 个人知识库系统（Personal Knowledge Base）。一句话：给 AI 一个 URL，它自动分类、索引、综合、蒸馏、图谱化。

---

## 1. Skill 文件

完整的 Hermes Agent Skill 结构，包含 `SKILL.md` + 配套脚本 + 参考文档 + 模板：

```
personal-kb/
├── SKILL.md                  # 主文档：触发方式、AI 编排流程、核心脚本使用说明
├── scripts/                  # 7 个核心自动化脚本（AI 编排的触手）
│   ├── db.py                 # SQLite+FTS5 数据库（CJK 分词、全文搜索）
│   ├── fetch_material.py     # URL 自动抓取（4级降级：markitdown→Jina AI→readability→HTML）
│   ├── batch_fetch.py        # 批量种子抓取，覆盖 12 主题
│   ├── rebuild_index.py      # 素材库同步：扫描文件 → 写入 SQLite → 生成 status.md
│   ├── generate_status.py    # 状态概览：30 秒看懂素材库全貌
│   ├── distill_cards.py      # 知识蒸馏：策略文档 → 结构化卡片 + 知识图谱
│   └── rebuild_graph.py      # 知识图谱渲染（D3.js 聚类引力布局）
│   └── test_suite.py         # 自动化测试：22 项断言，5 秒验证全链路
├── references/               # 系统文档 + 写作风格模板
│   ├── instruction.md        # 系统宪法：目录结构、主题分类、流程规范
│   ├── analytic.md           # 分析型风格模板（结论先行、数据驱动）
│   ├── practical.md          # 实操型风格模板（Step-by-step、参数标签化）
│   └── inspiring.md          # 激励型风格模板（从“你”出发、画面感结尾）
├── assets/
│   └── topics.json           # 主题注册模板（12 预设主题 + 关键词）
├── docs/
│   ├── iteration-log.md      # 迭代升级说明（5 步迭代法 × 2 轮）
│   └── test-record.md        # 测试记录（环境、步骤、执行结果）
└── test-workspace/           # 测试数据集（真实澳洲策略数据）
```

### 为什么 AI 是核心（不是脚本流水线）

| 传统工具 | AI 知识库 | 具体实现 |
|---------|----------|---------|
| 手动分类 | 自动理解内容匹配主题/标签 | `fetch_material.py` 的 NLP 分类 + topics.json 语义匹配 |
| 关键词搜索 | 全文语义搜索 + 主题聚合 | `db.py` 的 SQLite+FTS5 CJK 分词全文检索 |
| 孤立笔记 | 自动发现跨主题关联 | `distill_cards.py` 计算 tag 共现 + 权重阈值 |
| 手动写作 | 综合 N 篇素材生成策略文档 | AI 按风格模板检索 + 综合 + 输出 |
| 知识在脑子里 | 蒸馏成结构化卡片 + 交互式图谱 | `distill_cards.py` 表格提取 + `rebuild_graph.py` D3 聚类引力图 |

---

## 2. 测试数据

使用真实澳洲留学/移民策略数据，非模拟数据：

| 类型 | 文件名 | 主题 | 内容来源 |
|------|--------|------|---------|
| 素材 | `2026-07-11-164217-...migration-educ.md` | migration | 第三方网站抓取（2026-27 年度配额） |
| 素材 | `2026-07-11-164234-...491区域签证.md` | visa | 第三方网站抓取（491 区域签证大砍） |
| 素材 | `2026-07-11-164337-...留学申请sop.md` | study | 第三方网站抓取（SOP/CV/推荐信） |
| 素材 | `2026-07-11-094700-...working-holiday.md` | visa | 第三方网站抓取（WHV 攻略） |
| 素材 | `2026-07-11-165204-...天气穿衣指南.md` | living | 第三方网站抓取（七大城市气候） |
| 策略 | `2026-07-11-strategy-assessment-guide.md` | assessment | AI 生成（职业评估完整指南） |
| 策略 | `2026-07-11-strategy-language-guide.md` | language | AI 生成（雅思/PTE 选择策略） |
| 策略 | `2026-07-11-strategy-policy-2026-changes.md` | policy | AI 生成（2026 政策变化解读） |

**测试数据产出**：
- 素材 → 5 篇（含 frontmatter：title/source/date/tags/topics）
- 策略 → 3 篇（含结构化表格、核心结论、行动建议）
- 蒸馏卡片 → **26 张**（含 3 张概念卡片，36 个关键概念定义）
- 关联连接 → **192 条**（含跨主题虚线）

---

## 3. 测试记录

### 测试环境

| 项目 | 值 |
|------|-----|
| OS | Windows 11 (build 22631) |
| Python | 3.13.12 (managed venv) |
| SQLite | 3.45+ (FTS5 enabled) |
| 浏览器 | WorkBuddy 内置 D3 预览 |
| 测试时间 | 2026-07-12 00:25 |
| 测试脚本 | `test_suite.py`（22 项自动化断言） |

### 测试步骤与结果

| 步骤 | 命令 | 预期 | 结果 |
|------|------|------|------|
| 1. 索引同步 | `python scripts/rebuild_index.py` | 创建 SQLite + status.md | **8 条记录 ✅** |
| 2. 知识蒸馏 | `python scripts/distill_cards.py` | 3 策略 → 卡片 + 连接 | **26 卡 / 192 连接 ✅** |
| 3. 图谱渲染 | `python scripts/rebuild_graph.py --validate` | 健康报告 + 自动断言 | **验证通过 ✅** |
| 4. 增量幂等 | 再次运行 `distill_cards.py` | 全部跳过 | **3 篇 ⏭ 跳过 ✅** |
| 5. 全量测试 | `python scripts/test_suite.py` | 22 项断言 | **22/22 通过 ✅** |

### 验证指标

```
📋 Test 1: rebuild_index.py
  ✅ Exit code == 0 | 同步完成 | SQLite DB(test-workspace.db) | status.md

📋 Test 2: distill_cards.py
  ✅ 26 卡片 | 192 连接 | 26/26 multi-topic | 36 概念提取

📋 Test 3: rebuild_graph.py
  ✅ 健康报告 | 验证通过 | D3.js | data/links/simulation

📋 Test 4: 增量蒸馏
  ✅ 3 篇全部跳过 | 幂等性 | 26 vs 26 一致

Results: 22/22 passed
```

---

## 4. Skill 迭代升级说明（5 步迭代法）

完整记录见 `docs/iteration-log.md`，核心总结：

### 第一轮：P0/P1/P2 痛点修复（3 → 7 版本迭代）

| 阶段 | 内容 |
|------|------|
| **痛点** | 知识图谱中不同颜色主题簇之间完全没有连接 |
| **量化** | 跨主题边数 = 0 / 跨主题占比 = 0% |
| **假设** | 纯 tag 共现连接导致不同策略文档的标签无交集 |
| **方案** | tag 权重追加 topic 共享 → 每个节点保留 top 3 同主题 + top 2 跨主题 |
| **效果** | 跨主题边从 0 → 94，但弱连接把布局拉散 |

| 阶段 | 内容 |
|------|------|
| **痛点** | 图谱布局被跨主题弱连接拉伸分散 |
| **量化** | 94 条跨主题边中多数权重=1，导致簇漂移 |
| **假设** | 纯力导向无法同时满足“簇内紧凑 + 跨主题桥梁 + 整体紧凑” |
| **方案** | 引入聚类引力（forceX/Y 固定主题区域），中心节点只连簇中心 |
| **效果** | 7 个主题簇均匀分布，14 条跨主题虚线，0 孤立节点 |

### 第二轮：N1/N2/N3/N4 增量修复

| 阶段 | 内容 |
|------|------|
| **痛点** | 卡片 ID 跨文档碰撞（同名标题） |
| **量化** | 多策略文档的“核心结论”卡片共用同一 ID |
| **假设** | `make_card_id` 仅用标题前 12 字 + 索引 |
| **方案** | ID 加源文件 MD5 前 4 位：`card-{hash}-{slug}-{idx}` |
| **效果** | 跨文档唯一，D3 力导向解析不再失败 |

| 阶段 | 内容 |
|------|------|
| **痛点** | 主题色只支持 12 个硬编码，新增主题颜色循环 |
| **量化** | 第 13 个主题复用第 1 个颜色 |
| **假设** | 颜色列表写死，未动态扩展 |
| **方案** | HSL 色环自动生成：hue = 360×idx/N，sat 65%，light 45% |
| **效果** | 无限主题自动扩展，无循环冲突 |

| 阶段 | 内容 |
|------|------|
| **痛点** | 同一 URL 重复抓取生成多个素材文件 |
| **量化** | 未查重，每次抓取都写新文件 |
| **假设** | 没有 source_url 去重机制 |
| **方案** | `fetch_material.py` 保存前查 SQLite：`SELECT id FROM materials WHERE source_url=?` |
| **效果** | 重复 URL 自动跳过，输出 `⏭ 跳过（已存在）` |

| 阶段 | 内容 |
|------|------|
| **痛点** | 蒸馏只提取表格和结论，漏掉 `**概念名**: 定义` 格式 |
| **量化** | 策略文档中大量定义性知识点未被结构化 |
| **假设** | 正则只匹配 `###` 和表格，未识别加粗定义模式 |
| **方案** | 新增 `**概念**: 定义` 正则提取器，生成概念卡片 |
| **效果** | 3 篇策略 → 36 个关键概念，3 张独立概念卡片 |

---

## 5. GitHub 仓库地址

所有代码、数据、测试记录统一提交至：

**https://github.com/akonnne/personal-kb**

提交历史：

```
6dffdb5 docs: 测试记录更新 + 22/22通过
a7fb303 第二轮迭代: N1-N4 痛点修复
fb90cbc 第一轮迭代: P1/P2/P3 剩余痛点修复
0f46cf0 P0 修复: tag跨主题 + 图谱验证 + 增量蒸馏
9be0604 README.md
d1a618d 真实测试数据
2a5e054 初始版本: 7 脚本 + 3 风格 + 系统宪法
```
