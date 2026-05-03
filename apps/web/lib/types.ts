export type RefactorStatus = "review" | "running" | "ready" | "conflict";

export type RefactorRunDataSource = "api" | "sample";

export type OperationReviewStatus = "needs_review" | "approved" | "rejected" | "applied";

export type OperationReviewDecision = Extract<OperationReviewStatus, "approved" | "rejected">;

export type RefactorRun = {
  id: string;
  title: string;
  status: RefactorStatus;
  sourceCount: number;
  operationCount: number;
  confidence: number;
  startedAt: string;
};

export type MemoryOperation = {
  id: string;
  type:
    | "merge"
    | "supersede"
    | "archive"
    | "flag_contradiction"
    | "create_memory"
    | "merge_memories"
    | "split_memory"
    | "supersede_memory"
    | "archive_memory"
    | "mark_contradiction";
  title: string;
  detail: string;
  rationale: string;
  sources: string[];
  sourceDetails: MemorySourceDetail[];
  confidence: number;
  status: RefactorStatus;
  reviewStatus: OperationReviewStatus;
};

export type MemorySourceDetail = {
  id: string;
  label: string;
  excerpt: string | null;
};

export type TimelineEvent = {
  id: string;
  label: string;
  detail: string;
  state: "complete" | "current" | "pending";
};

export type ApiRefactorRunStatus = "pending" | "running" | "needs_review" | "applied" | "failed";

export type ApiOperationReviewStatus = OperationReviewStatus;

export type ApiMemoryOperationKind =
  | "create_memory"
  | "merge_memories"
  | "split_memory"
  | "supersede_memory"
  | "archive_memory"
  | "mark_contradiction";

export type ApiMemoryOperation = {
  id: string;
  operation: ApiMemoryOperationKind;
  source_memory_ids: string[];
  source_event_ids: string[];
  proposed_memory: ApiMemoryUnit | null;
  rationale: string;
  confidence: number;
  requires_human_review: boolean;
  review_status: ApiOperationReviewStatus;
};

export type ApiMemorySource = {
  source_type: string;
  source_id: string;
  raw_event_id: string | null;
  excerpt: string | null;
  url: string | null;
  captured_at: string;
};

export type ApiMemoryUnit = {
  id: string;
  kind: string;
  content: string;
  confidence: number;
  status: string;
  sources: ApiMemorySource[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ApiRefactorPlan = {
  id: string;
  run_id: string;
  status: ApiRefactorRunStatus;
  summary: string;
  input_event_ids: string[];
  operations: ApiMemoryOperation[];
  contradictions: unknown[];
  created_at: string;
};
