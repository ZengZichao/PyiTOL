# PyiTOL 项目治理

本文档描述 PyiTOL 项目的治理结构与决策流程。

## 角色与职责

### 项目负责人（Project Lead）

项目负责人对 PyiTOL 的方向、健康度与可持续性负总责。职责包括：

- 制定项目路线图与发布计划
- 在无法达成共识时作出最终决定
- 任命与移除 maintainer
- 确保行为准则得到遵守
- 管理发布物的发布

### Maintainer

Maintainer 是拥有仓库写入权限的可信贡献者。职责包括：

- 审查并合并 pull request
- 对 issue 进行分诊并回应社区问题
- 确保代码质量与测试覆盖率达标
- 指导新贡献者
- 参与重大变更的设计讨论

Maintainer 应保持活跃。连续六个月不活跃的 maintainer 可能被要求卸任或转为名誉状态。

### 贡献者（Contributor）

任何提交 pull request、报告 issue、改进文档或参与讨论的人都是贡献者。所有贡献都受到重视与欢迎。

## 贡献层级

贡献者按以下层级晋升：

1. **Contributor** —— 至少有一个 pull request 被合并的任何人。
2. **Committer** —— 在项目多个领域展现出持续、高质量贡献并被授予分诊权限的贡献者。
3. **Maintainer** —— 由现有 maintainer 提名并经项目负责人批准、被授予仓库写入权限的 committer。

## 决策流程

本项目遵循**惰性共识**（lazy consensus）模型：

- 对于例行变更（bug 修复、文档、小幅增强），一名 maintainer 批准即可。
- 对于重大变更（新功能、API 变更、架构决策），需至少两名 maintainer 批准，且提案应至少开放 72 小时供评论。
- 若无法达成共识，由项目负责人作出最终决定。

### 提议变更

重大变更在开始实施前应通过 GitHub Issue 提出。提案应包含：

- 问题或动机的描述
- 拟定的解决方案
- 考虑过的替代方案
- 对现有用户的影响

## 行为准则

所有参与者应遵守 [Contributor Covenant 行为准则](CODE_OF_CONDUCT.md)。关于不可接受行为的报告应提交给项目负责人。

## 修订

本治理文档可通过 pull request 修订，修订需经项目负责人批准并至少有一名 maintainer 同意。
