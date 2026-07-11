# 澳洲出国策略系统 - 操作规范

> 这是系统的「宪法」。所有输入、输出、索引操作必须遵守本文规定。

---

## 一、核心原则

**文件系统是唯一事实来源。** 所有内容以 Markdown 文件形式存储。SQLite 数据库 (`system/australia.db`) 是全文搜索加速层，由脚本自动同步，不可手动编辑。

---

## 二、目录结构

```
australia_strategy/
├── input/                # 输入素材
│   ├── ideas/            #   想法/灵感片段
│   ├── materials/        #   外部素材（文章摘要、政策原文、数据等）
│   └── snippets/         #   短片段/待整理
├── output/               # 生成输出
│   ├── strategies/       #   策略分析文档
│   ├── pathways/         #   路线规划（时间线、步骤）
│   ├── reports/          #   对比报告、研究分析
│   └── checklists/       #   清单（申请清单、材料清单等）
├── system/               # 系统文件
│   ├── instruction.md    #   本文件
│   ├── status.md         #   自动生成的状态概览（30 秒看懂当前素材库）
│   ├── topics.json       #   主题注册表
│   ├── australia.db      #   SQLite + FTS5 全文搜索数据库
│   └── changelog.md     #   系统变更日志
├── styles/               # 风格文件
│   ├── analytic.md       #   分析型
│   ├── practical.md      #   实操型
│   └── inspiring.md      #   激励型
├── scripts/              # 工具脚本
│   └── rebuild_index.py  #   索引重建脚本
└── .workbuddy/           # WorkBuddy 会话记忆（自动管理）
```

---

## 三、主题分类规则

所有内容必须归属到 `topics.json` 中已注册的主题。当前注册的主题：

| ID | 名称 | 适用范围 |
|----|------|----------|
| visa | 签证政策 | 签证类型、条件、流程 |
| study | 留学申请 | 申请流程、材料、时间 |
| migration | 移民路径 | 移民策略、路径对比 |
| job | 工作机会 | 就业、行业、薪资 |
| living | 生活成本 | 住房、消费、医保 |
| language | 语言考试 | IELTS/PTE 备考 |
| university | 院校选择 | 大学排名、专业对比 |
| major | 专业方向 | 紧缺职业、专业分析 |
| policy | 政策动态 | 政策变化、趋势 |
| finance | 资金准备 | 预算、资金规划 |
| assessment | 评估体系 | 职业评估 |
| regional | 地区选择 | 城市/州对比 |

一篇内容可以标记多个主题（用数组），但必须至少有一个主主题。

---

## 四、输入流程

### 触发词
- "输入 xxx"、"记录 xxx"、"记一下 xxx"、"add xxx"

### 操作步骤

1. **提取内容**：识别用户原始输入的核心信息
2. **判断类型**：
   - `idea`：自己的思考、灵感、判断
   - `material`：外部信息（网页、文章、数据）
   - `snippet`：短片段，未成型的碎片信息
3. **判断主题**：根据内容自动匹配 topics.json 中的主题
4. **确认主题是否在注册表中**：如不在，先加入 topics.json
5. **生成文件名**：`YYYY-MM-DD-HHMMSS-{slug}.md`
6. **写入 frontmatter**：
   ```yaml
   ---
   date: 2026-07-11T09:30:00
   type: idea|material|snippet
   topic: [visa, study]
   tags: [标签1, 标签2]
   source: （仅 material 类型，填写来源 URL 或出处）
   ---
   ```
7. **写入正文**：原始内容 + AI 提炼的摘要
8. **重建索引**：运行 `scripts/rebuild_index.py`
9. **返回确认**：告知存到哪里、主题是什么、标签

---

## 五、输出流程

### 触发词
- "输出 xxx"、"生成 xxx"、"分析 xxx"、"规划 xxx"、"对比 xxx"

### 输出类型
- `strategy`：策略分析 → 存入 `output/strategies/`
- `pathway`：路线规划 → 存入 `output/pathways/`
- `report`：研究报告/对比分析 → 存入 `output/reports/`
- `checklist`：清单/检查表 → 存入 `output/checklists/`

### 操作步骤

1. **读取状态**：加载 `system/status.md` 了解素材库当前状态
2. **检索素材**：通过 SQLite 数据库组合检索相关素材
3. **选择风格**：列出 `styles/` 下的风格文件，询问用户选择
4. **读取风格**：加载选中风格文件的完整内容
5. **读取素材正文**：回读相关素材的完整内容
6. **生成输出**：按风格规则组织内容
7. **写入文件**：生成输出文件到对应目录
8. **重建索引**：运行 `scripts/rebuild_index.py`
9. **展示结果**：摘要 + 存储路径

### 输出文件 frontmatter
```yaml
---
date: 2026-07-11T10:00:00
type: strategy|pathway|report|checklist
topic: [visa, migration]
tags: [标签]
sources: [引用的素材文件名列表]
style: analytic|practical|inspiring
---
```

---

## 六、Spark 发现流程

### 触发词
- "灵感"、"启发"、"spark"、"有什么想法"

### 六大发现策略

1. **随机考古**：挖出创建久、未被引用的老素材（时间 > 7天 + 引用计数 = 0）
2. **空白发现**：有输入无输出的主题（说明只记了但没分析）
3. **跨主题关联**：找不同主题间有标签交集的素材对
4. **标签延伸**：从高频标签找延伸创作方向
5. **时间脉冲**：找即将到关键时间节点的事项（签证到期、申请截止等）
6. **矛盾发现**：找观点冲突或存在张力的素材对

### 操作步骤

1. 读取当前索引和素材库
2. 按六大策略分别扫描
3. 随机扰动各策略权重（注入熵增）
4. 展示 Top 3 发现点，附简要说明
5. 用户选择后，读取素材正文，进入输出流程

---

## 七、索引与搜索

### SQLite 数据库
`system/australia.db` 是全文搜索加速层：
- **materials 表**：存储所有素材的元数据和正文
- **materials_fts 表**：FTS5 虚拟表，支持中文逐字索引和全文检索
- 数据库由 `scripts/rebuild_index.py` 自动同步，**禁止手动编辑**

### 状态概览
`system/status.md` 由 `scripts/generate_status.py` 从数据库生成：
- 核心指标（总数、类型分布、时间跨度）
- 主题分布和目标签排行
- 空白发现（有输入无输出的主题）
- 最新素材列表
- 目标：30 秒内看懂当前素材库状态

### 检索能力
支持任意组合检索：
- **关键词**：FTS5 全文搜索（中英文均支持）
- **主题过滤**：按 topics.json 中的主题 ID 筛选
- **标签过滤**：按标签精确匹配
- **类型过滤**：idea / material / snippet / strategy / pathway / report / checklist
- **时间范围**：date_from / date_to
- **响应时间**：< 5ms（远低于 5 秒目标）

### 同步时机
每次输入/输出操作完成后，自动运行 `scripts/rebuild_index.py`，同时更新数据库和 status.md。新素材写入后立即可检索。

---

## 八、命名规则

### 文件命名
- 输入：`{YYYY-MM-DD}-{HHMMSS}-{slug}.md`
- 输出：`{YYYY-MM-DD}-{type}-{slug}.md`
- slug 规则：中文转拼音首字母缩写 + 英文关键词，不超过 40 字符

### 标签命名
- 使用中文标签，每个标签 2-6 个字
- 避免过于笼统的标签（如「澳洲」），使用更具体的（如「189签证」）

---

## 九、特殊规则

1. **创作链条**：输出文件可以引用之前的输出文件作为素材
2. **版本管理**：修改已存在的文件时，在末尾追加 `## 更新记录` 段落
3. **素材去重**：输入前检查是否已有高度相似内容，如存在则合并而非新建
4. **政策时效**：涉及签证政策的内容，必须标注数据截止日期
5. **个人隐私**：涉及个人具体信息（护照号、成绩等）的内容，标注 `[PII]` 并提醒用户

---

*版本：1.0.0 | 创建：2026-07-11*
