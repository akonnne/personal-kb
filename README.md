# personal-kb

AI 驱动的个人知识库系统。一句话：给 AI 一个 URL，它自动分类、索引、综合、蒸馏、图谱化。

---

## 为什么用 AI 知识库？

| 传统工具 | AI 知识库 |
|---------|----------|
| 手动分类 | 自动理解内容、匹配主题/标签 |
| 关键词搜索 | 全文语义搜索 + 主题聚合 |
| 孤立笔记 | 自动发现跨主题关联 |
| 手动写作 | 综合 N 篇素材生成策略文档 |
| 知识在脑子里 | 蒸馏成结构化卡片 + 交互式图谱 |

---

## 一句话调用

```
帮我建个知识库，主题：python/go/k8s，路径 ~/dev-kb，输出技术路线规划
```

Skill 自动完成：目录 → 系统宪法 → 注册主题 → 风格模板 → 复制脚本 → 初始化 SQLite → 生成状态概览。

---

## 项目结构

```
personal-kb/
├── SKILL.md                    # 主文档（AI 操作流程）
├── scripts/                    # 核心脚本（7 个）
│   ├── db.py                   # SQLite+FTS5 数据库
│   ├── fetch_material.py       # URL 自动抓取（4级降级）
│   ├── batch_fetch.py          # 批量抓取
│   ├── rebuild_index.py        # 索引同步
│   ├── generate_status.py      # 状态生成
│   ├── distill_cards.py        # 知识蒸馏
│   └── rebuild_graph.py        # 知识图谱渲染
├── references/                 # 系统文档 + 风格模板
│   ├── instruction.md          # 系统宪法
│   ├── analytic.md             # 分析型风格
│   ├── practical.md            # 实操型风格
│   └── inspiring.md            # 激励型风格
├── assets/
│   └── topics.json             # 主题注册模板
├── docs/
│   ├── iteration-log.md        # 迭代升级说明（5 步迭代法）
│   └── test-record.md          # 测试记录
└── test-workspace/             # 测试数据（真实澳洲策略数据）
    ├── input/materials/        # 5 篇素材
    ├── output/strategies/      # 3 篇策略
    └── output/cards/           # 23 张卡片 + 知识图谱
```

---

## 快速开始

### 1. 初始化

```bash
cd test-workspace
python scripts/rebuild_index.py
```

### 2. 导入素材

```bash
python scripts/fetch_material.py "https://example.com/article"
python scripts/rebuild_index.py
```

### 3. 知识蒸馏

```bash
python scripts/distill_cards.py
python scripts/rebuild_graph.py
```

---

## 技术栈

- **SQLite + FTS5** — 全文搜索，CJK 分词，WAL 模式
- **D3.js v7** — 交互式力导向知识图谱，聚类引力布局
- **4 级抓取降级** — markitdown → Jina AI → readability-lxml → HTML
- **7 个主题色** — 签证/留学/语言/职业评估/政策/生活/资金

---

## 测试验证

| 测试项 | 结果 |
|--------|------|
| rebuild_index.py（SQLite 同步） | ✅ 8 条记录 |
| distill_cards.py（知识蒸馏） | ✅ 3 策略 → 23 卡片 + 72 连接 |
| rebuild_graph.py（图谱渲染） | ✅ 23 节点 / 73 边 / 3 跨主题 / 0 孤立 |

详见 `docs/test-record.md`。

---

## 迭代记录

按照 5 步迭代法记录了 2 次完整迭代：
- **v3 → v4**：跨主题连接（从孤立簇到跨主题桥梁）
- **v5 → v7**：布局稳定性（从力导向漂移 → 聚类引力固定）

详见 `docs/iteration-log.md`。

---

## 触发词

搭建知识库、建 KM 系统、知识管理、知识蒸馏、知识图谱、知识卡片、个人知识系统、knowledge base setup。

