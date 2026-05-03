import type { MemoryOperation, RefactorRun, TimelineEvent } from "@/lib/types";

export const refactorRuns: RefactorRun[] = [
  {
    id: "run_1029",
    title: "Developer direction cleanup",
    status: "review",
    sourceCount: 42,
    operationCount: 11,
    confidence: 0.91,
    startedAt: "Today 14:10",
  },
  {
    id: "run_1028",
    title: "Project preference refresh",
    status: "conflict",
    sourceCount: 18,
    operationCount: 4,
    confidence: 0.72,
    startedAt: "Today 11:45",
  },
  {
    id: "run_1027",
    title: "Old stack assumptions",
    status: "ready",
    sourceCount: 27,
    operationCount: 8,
    confidence: 0.88,
    startedAt: "Yesterday 18:20",
  },
];

export const memoryOperations: MemoryOperation[] = [
  {
    id: "op_2041",
    type: "merge",
    title: "Merge AI infrastructure product goals",
    detail:
      "Consolidates scattered notes about building a durable memory compiler with typed operations and reviewable changes.",
    rationale: "These sources describe the same durable memory compiler direction.",
    sources: ["mem_8a1", "mem_b42", "mem_e19"],
    sourceDetails: [
      { id: "mem_8a1", label: "mem_8a1", excerpt: "Build a durable memory compiler." },
      { id: "mem_b42", label: "mem_b42", excerpt: "Use typed operations and review." },
      { id: "mem_e19", label: "mem_e19", excerpt: "Memory should be maintained." },
    ],
    confidence: 0.94,
    status: "review",
    reviewStatus: "needs_review",
  },
  {
    id: "op_2042",
    type: "supersede",
    title: "Replace single-language stack preference",
    detail:
      "Supersedes older full TypeScript assumptions with Python for memory intelligence and TypeScript for product UI.",
    rationale: "The newer architecture separates product UI and AI memory intelligence.",
    sources: ["mem_c91", "mem_f03"],
    sourceDetails: [
      { id: "mem_c91", label: "mem_c91", excerpt: "Use TypeScript for the product UI." },
      { id: "mem_f03", label: "mem_f03", excerpt: "Use Python for AI and memory intelligence." },
    ],
    confidence: 0.89,
    status: "review",
    reviewStatus: "needs_review",
  },
  {
    id: "op_2043",
    type: "flag_contradiction",
    title: "Resolve graph layer timing",
    detail:
      "One source says Graphiti should be core. A newer note says fake graph semantics in Postgres for MVP.",
    rationale: "The timing of the graph layer is not yet settled.",
    sources: ["mem_120", "mem_778"],
    sourceDetails: [
      { id: "mem_120", label: "mem_120", excerpt: "Graphiti should be part of the core." },
      { id: "mem_778", label: "mem_778", excerpt: "Use Postgres relationship tables first." },
    ],
    confidence: 0.68,
    status: "conflict",
    reviewStatus: "needs_review",
  },
  {
    id: "op_2044",
    type: "archive",
    title: "Archive obsolete NestJS-only plan",
    detail:
      "Keeps the original note as history while removing it from active retrieval for architecture recommendations.",
    rationale: "The NestJS-only plan is obsolete but should remain auditable.",
    sources: ["mem_331"],
    sourceDetails: [
      { id: "mem_331", label: "mem_331", excerpt: "Consider building the whole backend in NestJS." },
    ],
    confidence: 0.86,
    status: "ready",
    reviewStatus: "approved",
  },
];

export const timeline: TimelineEvent[] = [
  {
    id: "step_1",
    label: "Ingest",
    detail: "42 raw events normalized",
    state: "complete",
  },
  {
    id: "step_2",
    label: "Retrieve",
    detail: "19 related memories loaded",
    state: "complete",
  },
  {
    id: "step_3",
    label: "Plan",
    detail: "11 typed operations proposed",
    state: "complete",
  },
  {
    id: "step_4",
    label: "Review",
    detail: "Awaiting approval",
    state: "current",
  },
  {
    id: "step_5",
    label: "Apply",
    detail: "Pending transaction",
    state: "pending",
  },
];
