# personal-kb Skill 测试记录

## 测试环境

| 项目 | 值 |
|------|-----|
| OS | Windows 11 (build 22631) |
| Python | 3.13.12 (managed venv) |
| SQLite | 3.45+ (FTS5 enabled) |
| 浏览器 | WorkBuddy 内置 D3 预览 |
| 首次测试 | 2026-07-11 22:20 |
| 最终测试 | 2026-07-12 00:25 |
| 迭代轮次 | 2 轮（修复 10/10 项痛点） |

## 测试数据集（真实澳洲策略数据）

| 类型 | 文件名 | 主题 | 标签 |
|------|--------|------|------|
| 素材 | `2026-07-11-164217-...migration-educ.md` | migration | 技术移民, 配额 |
| 素材 | `2026-07-11-164234-...491区域签证.md` | visa | 491, 配额, 技术移民 |
| 素材 | `2026-07-11-164337-...留学申请sop.md` | study | 留学, 申请, GS, SOP |
| 素材 | `2026-07-11-094700-...working-holiday.md` | visa | 打工度假, WHV |
| 素材 | `2026-07-11-165204-...天气穿衣指南.md` | living | 气候, 城市 |
| 策略 | `2026-07-11-strategy-assessment-guide.md` | assessment | ACS, EA, VETASSESS |
| 策略 | `2026-07-11-strategy-language-guide.md` | language | 雅思, PTE, EOI |
| 策略 | `2026-07-11-strategy-policy-2026-changes.md` | policy | 政策, 配额, 改革 |

## 测试步骤与结果

### Step 1: rebuild_index.py — SQLite 索引同步

**命令**：
```bash
cd test-workspace
python scripts/rebuild_index.py
```

**输出日志**：
```
SQLite 同步: 新增 8 | 更新 0 | 删除 0
素材库总条目: 8
status.md 已生成: test-workspace/system/status.md
同步完成 — 数据库 + 状态文件已更新
```

**校验**：
- SQLite DB 自动命名 `test-workspace.db` ✅（N1 修复生效）
- 索引 8 条记录 ✅（5 素材 + 3 策略）
- status.md 生成 ✅

### Step 2: distill_cards.py — 知识蒸馏（含概念提取）

**命令**：
```bash
python scripts/distill_cards.py
```

**实际输出**：
```
发现 3 篇策略文档
  📝 2026-07-11-strategy-assessment-guide.md: 提取 7 张卡片
  📝 2026-07-11-strategy-language-guide.md: 提取 10 张卡片
  📝 2026-07-11-strategy-policy-2026-changes.md: 提取 9 张卡片
总计: 26 张卡片, 192 条连接
```

**校验**：
- 卡片数：23 → **26**（+3 张概念卡片，N4 修复生效）✅
- 连接数：72 → **192**（tag 跨主题生效，P0 修复）✅
- ID 含源文件 hash（如 `card-3f2a-ACS(0c-00`，N1 修复生效）✅
- card_index.json 生成 ✅

**概念提取验证（N4）**：
```
概念卡片: 3
  [assessment-guide] 关键概念（23 个）: ACS/EA/VETASSESS/ANMAC/CDR...
  [language-guide]   关键概念（7 个）: PTE八炸/四个7/NAATI CCL...
  [policy-2026]      关键概念（6 个）: 签证费/SID/配额/薪资门槛...
```

### Step 3: rebuild_graph.py — 知识图谱 + 健康报告

**命令**：
```bash
python scripts/rebuild_graph.py --validate
```

**实际输出**：
```
✅ 已生成：output/cards/knowledge_graph.html
   节点：26 | 边：73 | 孤立节点：0 | 跨主题边：3 | 主题数：3

==================================================
  图谱健康报告
==================================================
  跨主题占比:   4.1% ✅ (理想: 3%-40%)
  孤立节点率:   0.0% ✅ (理想: 0%)
  总节点/边:    26/73 ✅
  主题内度分布:
    assessment: 7节点 / 平均5.3度 / 最高7度 ✅
    language: 10节点 / 平均6.9度 / 最高10度 ✅
    policy: 9节点 / 平均6.5度 / 最高9度 ✅

  ✅ 验证通过 — 所有指标在健康范围内
```

**校验**：
- 健康报告自动生成 ✅（P0 修复生效）
- `--validate` 模式自动断言，exit code 0 ✅
- 主题色自动扩展（N2 修复生效）✅
- D3 本地 fallback（N3 修复生效）✅

### Step 4: 增量蒸馏 — 幂等性验证

**首轮**：
```
📝 3 篇策略文档（全量提取）
```
**次轮**：
```
⏭ strategy-assessment-guide.md: 跳过（未变化，7 张卡片）
⏭ strategy-language-guide.md: 跳过（未变化，10 张卡片）
⏭ strategy-policy-2026-changes.md: 跳过（未变化，9 张卡片）
总计: 26 张卡片, 192 条连接
```
**校验**：第 2 轮全部跳过 ✅，卡片数和连接数一致 ✅

### Step 5: test_suite.py — 22 项自动化测试

**命令**：
```bash
python scripts/test_suite.py
```

**实际输出**：
```
==================================================
  personal-kb Test Suite
==================================================

📋 Test 1: rebuild_index.py
  ✅ Exit code == 0 (got 0)
  ✅ Output contains '同步完成'
  ✅ SQLite DB created (test-workspace.db)
  ✅ status.md generated

📋 Test 2: distill_cards.py
  ✅ Exit code == 0 (got 0)
  ✅ Output contains '总计'
  ✅ card_index.json valid (26 cards)
  ✅ Cards have ids
  ✅ Cards have topic
  ✅ Cards have tags
  ✅ Cards have cross-topic tags (26/26 multi-topic)
  ✅ Links exist (192 links)

📋 Test 3: rebuild_graph.py
  ✅ Exit code == 0 (got 0)
  ✅ Output contains '健康报告'
  ✅ Output contains '验证通过'
  ✅ HTML contains D3.js
  ✅ HTML contains data
  ✅ HTML contains links
  ✅ HTML has simulation

📋 Test 4: 增量蒸馏（幂等性）
  ✅ Second run exit code == 0
  ✅ Second run skips all
  ✅ Same card count (26 vs 26)

==================================================
  Results: 22/22 passed
==================================================
```

## 测试结果汇总

| 序号 | 测试项 | 数据 | 状态 |
|------|--------|------|------|
| 1 | 索引同步 | 8 条记录，SQLite WAL | ✅ |
| 2 | 知识蒸馏 | 3 文 → 26 卡 + 192 连接 | ✅ |
| 3 | tag 跨主题 | 26/26 卡片 multi-topic | ✅ |
| 4 | 概念提取 | 3 篇 → 36 个关键概念 | ✅ |
| 5 | 卡片 ID | 含源文件 hash，跨文档唯一 | ✅ |
| 6 | 图谱验证 | 健康报告 + `--validate` 断言 | ✅ |
| 7 | 主题色 | HSL 色环自动扩展 | ✅ |
| 8 | URL 去重 | SQLite 查重防重复抓取 | ✅ |
| 9 | 增量蒸馏 | 次轮全部跳过，幂等 | ✅ |
| 10 | 自动化测试 | `test_suite.py` 22/22 | ✅ |

## 痛点修复验证矩阵

| 痛点 | 修复 | 验证方式 |
|------|------|---------|
| P0: tag 不跨主题 | topic 追加到 tag | 连接数 72→192，26/26 卡片 multi-topic |
| P0: 图谱调试靠肉眼 | `--validate` 模式 | 健康报告 + 自动断言 |
| P1: DB 名硬编码 | 取 workspace 目录名 | `test-workspace.db` 自动生成 |
| P1: 蒸馏格式敏感 | 6 种 fallback + 终极降级 | 3 种不同格式策略文档均正常提取 |
| P2: 无增量蒸馏 | mtime + cards 双缓存 | 次轮全部 ⏭ 跳过 |
| P2: 测试靠手动 | `test_suite.py` | 22/22 自动化通过 |
| P3: D3 离线 | onerror 回退 | HTML 含本地 fallback 路径 |
| N1: ID 跨文档碰撞 | 加源文件 hash | `card-4位hash-标题-索引` |
| N2: 主题色硬编码 | HSL 色环自动扩展 | 测试 3 主题 + 验证 >12 主题扩展 |
| N3: URL 去重 | SQLite source_url 查重 | 重复 URL 自动 ⏭ 跳过 |
| N4: 概念提取 | `**概念**: 定义` 解析 | 3 篇策略 → 36 个概念 |

## 输出文件清单

```
test-workspace/
├── system/
│   ├── test-workspace.db               ← 自动命名
│   ├── status.md                       ← 自动生成
│   ├── topics.json                     ← 6 主题注册
│   └── instruction.md                  ← 系统宪法
├── input/materials/                    ← 5 篇真实澳洲素材
├── output/
│   ├── strategies/                     ← 3 篇策略文档
│   └── cards/
│       ├── card_index.json             ← 26 张卡片 + 192 条连接
│       ├── knowledge_graph.html        ← 交互式 D3 图谱
│       ├── .distill_cache.json         ← mtime 标记
│       └── .distill_cards_cache.json   ← 卡片缓存
└── scripts/                            ← 10 个 Python 脚本
```
