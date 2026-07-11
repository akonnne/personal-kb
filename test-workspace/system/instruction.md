---
title: "系统操作规范"
summary: "定义知识库的目录结构、主题分类、工作流程和命名规范"
---

# 知识库操作规范

## 目录结构
- `input/materials/` — 外部素材（自动抓取，带 frontmatter）
- `input/ideas/` — 个人想法/灵感
- `input/snippets/` — 短片段/代码片段
- `output/strategies/` — AI 生成的策略分析文档
- `output/reports/` — 系统检查报告
- `output/cards/` — 知识卡片 + 知识图谱
- `styles/` — 写作风格模板
- `system/` — 系统配置文件
- `scripts/` — 自动化脚本

## 主题分类
backend, frontend, devops, architecture, career, general

## 工作流程
1. 输入：提供 URL → AI 抓取+分类 → 写入 materials/
2. 索引：运行 rebuild_index.py → SQLite+FTS5 搜索
3. 输出：提需求 → AI 检索+综合 → 策略文档
4. 蒸馏：运行 distill_cards.py → 知识卡片 + 图谱

## 命名规范
素材：`{6位时间戳}-{slug}.md`
策略：`{日期}-strategy-{slug}.md`
报告：`{日期}-report-{slug}.md`
