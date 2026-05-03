import {
  memoryOperations as sampleMemoryOperations,
  refactorRuns as sampleRefactorRuns,
} from "@/lib/sample-data";
import type {
  ApiRefactorPlan,
  ApiRefactorRunStatus,
  ApiMemoryOperation,
  ApiMemorySource,
  MemoryOperation,
  MemorySourceDetail,
  OperationReviewDecision,
  RefactorRun,
  RefactorRunDataSource,
  RefactorStatus,
} from "@/lib/types";
import { z } from "zod";

const sampleOperationsByRunId = Object.fromEntries(
  sampleRefactorRuns.map((run) => [run.id, sampleMemoryOperations]),
);

const apiSourceSchema = z.object({
  source_type: z.string(),
  source_id: z.string(),
  raw_event_id: z.string().nullable(),
  excerpt: z.string().nullable(),
  url: z.string().nullable(),
  captured_at: z.string(),
});

const apiMemoryUnitSchema = z.object({
  id: z.string(),
  kind: z.string(),
  content: z.string(),
  confidence: z.number(),
  status: z.string(),
  sources: z.array(apiSourceSchema),
  metadata: z.record(z.unknown()),
  created_at: z.string(),
  updated_at: z.string(),
});

const apiOperationSchema = z.object({
  id: z.string(),
  operation: z.enum([
    "create_memory",
    "merge_memories",
    "split_memory",
    "supersede_memory",
    "archive_memory",
    "mark_contradiction",
  ]),
  source_memory_ids: z.array(z.string()),
  source_event_ids: z.array(z.string()),
  proposed_memory: apiMemoryUnitSchema.nullable(),
  rationale: z.string(),
  confidence: z.number(),
  requires_human_review: z.boolean(),
  review_status: z.enum(["needs_review", "approved", "rejected", "applied"]),
});

const apiRefactorPlanSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  workflow_id: z.string().nullable(),
  trace_id: z.string().nullable(),
  status: z.enum(["pending", "running", "needs_review", "applied", "failed"]),
  summary: z.string(),
  input_event_ids: z.array(z.string()),
  operations: z.array(apiOperationSchema),
  contradictions: z.array(z.unknown()),
  created_at: z.string(),
});

const apiRefactorPlansSchema = z.array(apiRefactorPlanSchema);

const apiApplyMemoryOperationResponseSchema = z.object({
  operation: apiOperationSchema,
  memory: apiMemoryUnitSchema,
});

export type RefactorRunFetchResult = {
  runs: RefactorRun[];
  operationsByRunId: Record<string, MemoryOperation[]>;
  source: RefactorRunDataSource;
  error: string | null;
};

export function mapApiStatus(status: ApiRefactorRunStatus): RefactorStatus {
  switch (status) {
    case "pending":
    case "running":
      return "running";
    case "needs_review":
      return "review";
    case "applied":
      return "ready";
    case "failed":
      return "conflict";
  }
}

export function mapApiPlanToRefactorRun(plan: ApiRefactorPlan): RefactorRun {
  const operationCount = plan.operations.length;
  const averageConfidence =
    operationCount === 0
      ? 0
      : plan.operations.reduce((total, operation) => total + operation.confidence, 0) /
        operationCount;

  return {
    id: plan.run_id,
    title: plan.summary || `Refactor run ${plan.run_id}`,
    status: mapApiStatus(plan.status),
    sourceCount: plan.input_event_ids.length,
    operationCount,
    confidence: averageConfidence,
    startedAt: formatApiDate(plan.created_at),
  };
}

export function mapApiOperationToMemoryOperation(
  operation: ApiMemoryOperation,
  runStatus: ApiRefactorRunStatus,
): MemoryOperation {
  const sourceDetails = buildSourceDetails(operation);
  const proposedKind = operation.proposed_memory?.kind;
  const operationLabel = operationActionLabel(operation.operation);

  return {
    id: operation.id,
    type: operation.operation as MemoryOperation["type"],
    title: proposedKind ? `${operationLabel} ${proposedKind} memory` : operationLabel,
    detail: operation.proposed_memory?.content ?? operation.rationale,
    rationale: operation.rationale,
    sources: sourceDetails.map((source) => source.label),
    sourceDetails,
    confidence: operation.confidence,
    reviewStatus: operation.review_status,
    status: mapApiOperationStatus(operation.operation, runStatus, operation.review_status),
  };
}

export async function reviewMemoryOperation({
  runId,
  operationId,
  decision,
  reason,
}: {
  runId: string;
  operationId: string;
  decision: OperationReviewDecision;
  reason?: string;
}): Promise<MemoryOperation> {
  const response = await fetch(
    `${getClientApiBaseUrl()}/refactor-runs/${encodeURIComponent(
      runId,
    )}/operations/${encodeURIComponent(operationId)}/review`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ decision, ...(reason ? { reason } : {}) }),
    },
  );

  if (!response.ok) {
    throw new Error(`API returned ${response.status}`);
  }

  const operation = apiOperationSchema.parse(await response.json()) as ApiMemoryOperation;
  return mapApiOperationToMemoryOperation(operation, "needs_review");
}

export async function applyMemoryOperation({
  runId,
  operationId,
}: {
  runId: string;
  operationId: string;
}): Promise<MemoryOperation> {
  const response = await fetch(
    `${getClientApiBaseUrl()}/refactor-runs/${encodeURIComponent(
      runId,
    )}/operations/${encodeURIComponent(operationId)}/apply`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error(`API returned ${response.status}`);
  }

  const payload = apiApplyMemoryOperationResponseSchema.parse(await response.json());
  return mapApiOperationToMemoryOperation(payload.operation as ApiMemoryOperation, "needs_review");
}

export async function fetchRefactorRuns(): Promise<RefactorRunFetchResult> {
  const apiBaseUrl = getApiBaseUrl();

  try {
    const response = await fetch(`${apiBaseUrl}/refactor-runs`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const plans = apiRefactorPlansSchema.parse(await response.json()) as ApiRefactorPlan[];

    return {
      runs: plans.map(mapApiPlanToRefactorRun),
      operationsByRunId: Object.fromEntries(
        plans.map((plan) => [
          plan.run_id,
          plan.operations.map((operation) => mapApiOperationToMemoryOperation(operation, plan.status)),
        ]),
      ),
      source: "api",
      error: null,
    };
  } catch (error) {
    return {
      runs: sampleRefactorRuns,
      operationsByRunId: sampleOperationsByRunId,
      source: "sample",
      error: error instanceof Error ? error.message : "Unable to fetch refactor runs",
    };
  }
}

function getApiBaseUrl(): string {
  return (
    process.env.MEMORY_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000"
  ).replace(/\/$/, "");
}

function getClientApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

function formatApiDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  const iso = date.toISOString();
  return `${iso.slice(0, 10)} ${iso.slice(11, 16)} UTC`;
}

function mapApiOperationStatus(
  operation: string,
  runStatus: ApiRefactorRunStatus,
  reviewStatus: ApiMemoryOperation["review_status"],
): RefactorStatus {
  if (reviewStatus === "approved" || reviewStatus === "applied") {
    return "ready";
  }

  if (reviewStatus === "rejected") {
    return "conflict";
  }

  if (operation === "mark_contradiction") {
    return "conflict";
  }

  return mapApiStatus(runStatus);
}

function buildSourceDetails(operation: ApiMemoryOperation): MemorySourceDetail[] {
  if (operation.proposed_memory?.sources.length) {
    return operation.proposed_memory.sources.map(mapApiSourceToSourceDetail);
  }

  if (operation.source_event_ids.length) {
    return operation.source_event_ids.map((sourceId) => ({
      id: sourceId,
      label: sourceId,
      excerpt: null,
    }));
  }

  return operation.source_memory_ids.map((sourceId) => ({
    id: sourceId,
    label: sourceId,
    excerpt: null,
  }));
}

function mapApiSourceToSourceDetail(source: ApiMemorySource): MemorySourceDetail {
  const id = source.raw_event_id ?? source.source_id;

  return {
    id,
    label: id,
    excerpt: source.excerpt,
  };
}

function operationActionLabel(operation: ApiMemoryOperation["operation"]): string {
  switch (operation) {
    case "create_memory":
      return "Create";
    case "merge_memories":
      return "Merge";
    case "split_memory":
      return "Split";
    case "supersede_memory":
      return "Supersede";
    case "archive_memory":
      return "Archive";
    case "mark_contradiction":
      return "Mark contradiction";
  }
}
