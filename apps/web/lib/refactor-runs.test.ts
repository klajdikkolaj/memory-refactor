import { afterEach, describe, expect, it, vi } from "vitest";

import {
  applyMemoryOperation,
  fetchRefactorRuns,
  mapApiOperationToMemoryOperation,
  mapApiPlanToRefactorRun,
  mapApiStatus,
  reviewMemoryOperation,
} from "@/lib/refactor-runs";
import type { ApiRefactorPlan } from "@/lib/types";

const apiPlan: ApiRefactorPlan = {
  id: "plan_123",
  run_id: "run_123",
  status: "needs_review",
  summary: "API-backed memory cleanup",
  input_event_ids: ["evt_1", "evt_2"],
  operations: [
    {
      id: "op_1",
      operation: "create_memory",
      source_memory_ids: [],
      source_event_ids: ["evt_1"],
      proposed_memory: {
        id: "mem_1",
        kind: "summary",
        content: "The user works in Go.",
        confidence: 0.8,
        status: "active",
        sources: [
          {
            source_type: "manual",
            source_id: "paste_demo",
            raw_event_id: "evt_1",
            excerpt: "I use Go.",
            url: null,
            captured_at: "2026-05-03T12:00:00Z",
          },
        ],
        metadata: {},
        created_at: "2026-05-03T12:30:00Z",
        updated_at: "2026-05-03T12:30:00Z",
      },
      rationale: "Source says the user works in Go.",
      confidence: 0.8,
      requires_human_review: true,
      review_status: "needs_review",
    },
    {
      id: "op_2",
      operation: "create_memory",
      source_memory_ids: [],
      source_event_ids: ["evt_2"],
      proposed_memory: null,
      rationale: "Source says the user wants to learn RL.",
      confidence: 1,
      requires_human_review: true,
      review_status: "needs_review",
    },
  ],
  contradictions: [],
  created_at: "2026-05-03T12:30:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("refactor run API mapping", () => {
  it.each([
    ["pending", "running"],
    ["running", "running"],
    ["needs_review", "review"],
    ["applied", "ready"],
    ["failed", "conflict"],
  ] as const)("maps backend status %s to UI status %s", (backendStatus, uiStatus) => {
    expect(mapApiStatus(backendStatus)).toBe(uiStatus);
  });

  it("maps a backend refactor plan to a dashboard run", () => {
    expect(mapApiPlanToRefactorRun(apiPlan)).toEqual({
      id: "run_123",
      title: "API-backed memory cleanup",
      status: "review",
      sourceCount: 2,
      operationCount: 2,
      confidence: 0.9,
      startedAt: "2026-05-03 12:30 UTC",
    });
  });

  it("uses zero confidence when a run has no operations yet", () => {
    const run = mapApiPlanToRefactorRun({
      ...apiPlan,
      status: "running",
      operations: [],
    });

    expect(run.status).toBe("running");
    expect(run.operationCount).toBe(0);
    expect(run.confidence).toBe(0);
  });

  it("maps operation source excerpts from proposed memory", () => {
    const operation = mapApiOperationToMemoryOperation(apiPlan.operations[0], apiPlan.status);

    expect(operation).toMatchObject({
      id: "op_1",
      type: "create_memory",
      title: "Create summary memory",
      detail: "The user works in Go.",
      rationale: "Source says the user works in Go.",
      sources: ["evt_1"],
      confidence: 0.8,
      status: "review",
      reviewStatus: "needs_review",
    });
    expect(operation.sourceDetails).toEqual([
      {
        id: "evt_1",
        label: "evt_1",
        excerpt: "I use Go.",
      },
    ]);
  });

  it.each([
    ["create_memory", "Create summary memory", "review"],
    ["merge_memories", "Merge summary memory", "review"],
    ["split_memory", "Split summary memory", "review"],
    ["supersede_memory", "Supersede summary memory", "review"],
    ["archive_memory", "Archive summary memory", "review"],
    ["mark_contradiction", "Mark contradiction summary memory", "conflict"],
  ] as const)("maps operation kind %s", (operationKind, title, status) => {
    const operation = mapApiOperationToMemoryOperation(
      {
        ...apiPlan.operations[0],
        operation: operationKind,
      },
      apiPlan.status,
    );

    expect(operation.title).toBe(title);
    expect(operation.status).toBe(status);
  });

  it.each([
    ["approved", "ready"],
    ["rejected", "conflict"],
    ["applied", "ready"],
  ] as const)("maps operation review status %s to UI status %s", (reviewStatus, status) => {
    const operation = mapApiOperationToMemoryOperation(
      {
        ...apiPlan.operations[0],
        review_status: reviewStatus,
      },
      apiPlan.status,
    );

    expect(operation.reviewStatus).toBe(reviewStatus);
    expect(operation.status).toBe(status);
  });
});

describe("fetchRefactorRuns", () => {
  it("fetches and maps API refactor runs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify([apiPlan]), { status: 200 })),
    );

    const result = await fetchRefactorRuns();

    expect(fetch).toHaveBeenCalledWith("http://localhost:8000/refactor-runs", {
      cache: "no-store",
    });
    expect(result.source).toBe("api");
    expect(result.error).toBeNull();
    expect(result.runs[0].title).toBe("API-backed memory cleanup");
    expect(result.operationsByRunId.run_123[0].sourceDetails[0].excerpt).toBe("I use Go.");
  });

  it("falls back to sample runs when the API is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("Service unavailable", { status: 503 })),
    );

    const result = await fetchRefactorRuns();

    expect(result.source).toBe("sample");
    expect(result.error).toBe("API returned 503");
    expect(result.runs.length).toBeGreaterThan(0);
    expect(result.operationsByRunId[result.runs[0].id].length).toBeGreaterThan(0);
  });

  it("patches memory operation review decisions", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              ...apiPlan.operations[0],
              review_status: "approved",
            }),
            { status: 200 },
          ),
      ),
    );

    const operation = await reviewMemoryOperation({
      runId: "run_123",
      operationId: "op_1",
      decision: "approved",
    });

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/refactor-runs/run_123/operations/op_1/review",
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ decision: "approved" }),
      },
    );
    expect(operation.reviewStatus).toBe("approved");
    expect(operation.status).toBe("ready");
  });

  it("posts approved memory operation apply requests", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              operation: {
                ...apiPlan.operations[0],
                review_status: "applied",
              },
              memory: apiPlan.operations[0].proposed_memory,
            }),
            { status: 200 },
          ),
      ),
    );

    const operation = await applyMemoryOperation({
      runId: "run_123",
      operationId: "op_1",
    });

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/refactor-runs/run_123/operations/op_1/apply",
      {
        method: "POST",
      },
    );
    expect(operation.reviewStatus).toBe("applied");
    expect(operation.status).toBe("ready");
  });
});
