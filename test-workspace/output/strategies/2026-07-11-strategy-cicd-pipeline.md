---
title: "微服务部署流水线设计"
summary: "从代码提交到生产部署的完整 CI/CD 流程"
topics: [devops, backend, architecture]
tags: [CI/CD, Docker, K8s, GitHub Actions, Helm]
created: 2026-07-11
style: practical
---

# 微服务部署流水线设计

## 核心结论

**自动化是微服务运维的底线。** 当服务数量超过 5 个时，手动部署完全不可持续。一套标准的 CI/CD 流水线是微服务架构的必要基础设施。

## 流水线阶段

### Stage 1: 代码检查（~2min）

- Lint 检查（golangci-lint / checkstyle）
- 单元测试 + 覆盖率门禁（≥80%）
- 安全扫描（Trivy）

### Stage 2: 构建与镜像（~5min）

- 多阶段构建（Go：scratch 镜像，Java：分层构建）
- Docker 镜像标签：`{commit-sha}` + `{branch}`
- 推送到私有镜像仓库（Harbor / ECR）

### Stage 3: 部署（~3min）

- Helm Chart 模板渲染
- Blue-Green 或 Rolling Update
- 健康检查 + Readiness Probe

### Stage 4: 验证（~2min）

- Smoke Test（API 健康端点）
- 集成测试（测试环境）
- 监控告警确认（指标基线）

## 推荐工具链

| 环节 | 推荐工具 | 备选 |
|------|----------|------|
| CI 引擎 | GitHub Actions | GitLab CI / Jenkins |
| 镜像仓库 | Harbor | Docker Hub / ECR |
| 配置管理 | Helm | Kustomize |
| 部署策略 | ArgoCD | Flux |
| 监控告警 | Prometheus + Grafana | Datadog |

## 时间线

```
git push → Lint(2min) → Test(2min) → Build(5min) → Deploy(3min) → Verify(2min)
总耗时：约 15 分钟
```

## 最佳实践

1. **不可变基础设施** — 每次部署创建新 Pod，不原地升级
2. **灰度发布** — 先 10% 流量，观察 5 分钟，逐步放量
3. **一键回滚** — 保留最近 5 个版本的 Helm release
4. **部署通知** — 钉钉/Slack 通知结果 + 变更摘要
