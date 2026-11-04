# Agent workflow

```mermaid
flowchart LR
  CV[CV upload PDF/DOCX] --> A1[1 Profile Understanding]
  A1 --> A2[2 Job Search]
  A2 --> A3[3 Job Matching]
  A3 -->|fewer than 3 jobs or best score under 35| R[Reflection: relax filters, widen roles]
  R --> A2
  A3 --> A4[4 Skill Gap]
  A3 --> A5[5 CV Optimisation]
  A4 --> A6[6 Learning Pathway]
  A4 --> A7[7 Interview Coach]
  A3 & A4 & A5 & A6 & A7 --> REP[Readiness report]
  A1 & A2 & A3 & A4 & A5 & A6 & A7 -.-> LOG[(agent_runs: status, latency, engine)]
```

Match score = 0.35 semantic similarity + 0.50 weighted skill coverage + 0.15 experience fit.
Bands: 80+ Highly qualified, 60+ Qualified with gaps, otherwise Development required.

Text-producing steps call `try_llm()`. With the mock provider (default) they return rule-based templates and are
labelled `template`; a failing real model falls back to `template-fallback`. Contact details are redacted before any
text leaves the server.
