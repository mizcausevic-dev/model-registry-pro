# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-05-12

### Released
- Published **model-registry-pro** as a public, portfolio-grade system focused on identity governance.
- Packaged the current implementation, documentation, validation flow, and proof surfaces into a repo that can be reviewed by technical and operating stakeholders.
- Clarified the core problem the project is addressing: identity sprawl, tenant-boundary mistakes, and access-review workflows that are technically complete but poorly explained.

### Why this mattered
- Existing approaches in IGA suites, ticket approvals, and access review campaigns were useful for parts of the workflow.
- They still left out a fast, legible control layer for access reasoning at the moment decisions are made.
- This release made the repo read like an operational capability rather than a narrow technical demo.

## [0.1.0] - 2026-01-09

### Shipped
- Cut the first coherent internal version of **model-registry-pro** with stable domain objects, review surfaces, and decision outputs.
- Established the first reviewable version of the architecture described as: Model lifecycle catalog for AI agents: versions, lineage, stage promotion, and approval gates. Audit-friendly governance for which version is in prod, who approved it, and what came before.
- Focused the repo around actionability instead of passive reporting.

## [Prototype] - 2025-07-19

### Built
- Built the first runnable prototype for the repo's main workflow and decision model.
- Validated the concept against pressure points such as identity sprawl, least-privilege drift, tenant-boundary mistakes, and approval latency.
- Used the prototype phase to test whether the project could drive action, not just present information.

## [Design Phase] - 2023-10-11

### Designed
- Defined the system around operator-first and decision-legible outputs.
- Chose interfaces and examples that made sense for IAM, platform security, compliance, and internal platform teams.
- Avoided reducing the project to a generic dashboard, CRUD app, or fashionable wrapper around the stack.

## [Idea Origin] - 2023-01-11

### Observed
- The original idea surfaced while looking at how teams were handling identity sprawl, tenant-boundary mistakes, and access-review workflows that are technically complete but poorly explained.
- The recurring pattern was that teams had data and tools, but still lacked a usable operating layer for the hardest decisions.

## [Background Signals] - 2022-08-09

### Context
- Earlier platform, governance, and operator-tooling work made one pattern hard to ignore: the systems that create the most drag are often the ones with partial controls and weak operational coherence, not the ones with no controls at all.
- That pattern shaped the thinking behind this repo well before the public version existed.