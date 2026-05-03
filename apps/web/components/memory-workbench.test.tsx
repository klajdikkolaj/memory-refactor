import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MemoryWorkbench } from "@/components/memory-workbench";
import { applyMemoryOperation, reviewMemoryOperation } from "@/lib/refactor-runs";

vi.mock("@/lib/refactor-runs", () => ({
  applyMemoryOperation: vi.fn(),
  reviewMemoryOperation: vi.fn(),
}));

const mockApplyMemoryOperation = vi.mocked(applyMemoryOperation);
const mockReviewMemoryOperation = vi.mocked(reviewMemoryOperation);

beforeEach(() => {
  mockApplyMemoryOperation.mockReset();
  mockReviewMemoryOperation.mockReset();
});

describe("MemoryWorkbench", () => {
  it("renders the review workspace", () => {
    render(<MemoryWorkbench />);

    expect(screen.getByRole("heading", { name: "Memory PR review" })).toBeInTheDocument();
    expect(screen.getAllByText("Developer direction cleanup")).toHaveLength(2);
    expect(screen.getAllByText("Merge AI infrastructure product goals")).toHaveLength(2);
  });

  it("renders API-backed refactor runs", () => {
    render(
      <MemoryWorkbench
        refactorRuns={[
          {
            id: "run_api",
            title: "API-backed memory cleanup",
            status: "review",
            sourceCount: 2,
            operationCount: 3,
            confidence: 0.9,
            startedAt: "2026-05-03 12:30 UTC",
          },
        ]}
        operationsByRunId={{
          run_api: [
            {
              id: "op_api",
              type: "create_memory",
              title: "Create summary memory",
              detail: "The user works in Go and wants to learn RL.",
              rationale: "The raw events describe durable user goals.",
              sources: ["evt_api_1"],
              sourceDetails: [
                {
                  id: "evt_api_1",
                  label: "evt_api_1",
                  excerpt: "I use Go and want to learn RL.",
                },
              ],
              confidence: 0.9,
              status: "review",
              reviewStatus: "needs_review",
            },
          ],
        }}
        runDataSource="api"
      />,
    );

    expect(screen.getByText("Refactor runs loaded from FastAPI.")).toBeInTheDocument();
    expect(screen.getAllByText("API-backed memory cleanup")).toHaveLength(2);
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("90%")).toBeInTheDocument();
    expect(screen.getAllByText("Create summary memory")).toHaveLength(2);
    expect(screen.getByText("The raw events describe durable user goals.")).toBeInTheDocument();
    expect(screen.getByText("I use Go and want to learn RL.")).toBeInTheDocument();
    expect(screen.queryByText("Merge AI infrastructure product goals")).not.toBeInTheDocument();
  });

  it("renders an empty refactor run state", () => {
    render(<MemoryWorkbench refactorRuns={[]} runDataSource="api" />);

    expect(
      screen.getByText("No refactor runs yet. Paste raw memory and start a refactor to create one."),
    ).toBeInTheDocument();
    expect(screen.getByText("Select a refactor run")).toBeInTheDocument();
    expect(screen.getByText("Select a run operation to inspect its Memory PR detail.")).toBeInTheDocument();
  });

  it("shows sample fallback context when the API is unavailable", () => {
    render(<MemoryWorkbench runDataSource="sample" runDataError="API returned 503" />);

    expect(
      screen.getByText("Showing sample refactor runs: API returned 503"),
    ).toBeInTheDocument();
  });

  it("filters operations by conflict status", async () => {
    const user = userEvent.setup();
    render(<MemoryWorkbench />);

    await user.click(screen.getByRole("button", { name: "Conflict" }));

    expect(screen.getAllByText("Resolve graph layer timing")).toHaveLength(2);
    expect(screen.queryByText("Archive obsolete NestJS-only plan")).not.toBeInTheDocument();
  });

  it("approves an API-backed memory operation", async () => {
    const user = userEvent.setup();
    mockReviewMemoryOperation.mockResolvedValue({
      id: "op_api",
      type: "create_memory",
      title: "Create summary memory",
      detail: "The user works in Go and wants to learn RL.",
      rationale: "The raw events describe durable user goals.",
      sources: ["evt_api_1"],
      sourceDetails: [
        {
          id: "evt_api_1",
          label: "evt_api_1",
          excerpt: "I use Go and want to learn RL.",
        },
      ],
      confidence: 0.9,
      status: "ready",
      reviewStatus: "approved",
    });

    render(
      <MemoryWorkbench
        refactorRuns={[
          {
            id: "run_api",
            title: "API-backed memory cleanup",
            status: "review",
            sourceCount: 1,
            operationCount: 1,
            confidence: 0.9,
            startedAt: "2026-05-03 12:30 UTC",
          },
        ]}
        operationsByRunId={{
          run_api: [
            {
              id: "op_api",
              type: "create_memory",
              title: "Create summary memory",
              detail: "The user works in Go and wants to learn RL.",
              rationale: "The raw events describe durable user goals.",
              sources: ["evt_api_1"],
              sourceDetails: [
                {
                  id: "evt_api_1",
                  label: "evt_api_1",
                  excerpt: "I use Go and want to learn RL.",
                },
              ],
              confidence: 0.9,
              status: "review",
              reviewStatus: "needs_review",
            },
          ],
        }}
        runDataSource="api"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Approve" }));

    expect(mockReviewMemoryOperation).toHaveBeenCalledWith({
      runId: "run_api",
      operationId: "op_api",
      decision: "approved",
    });
    expect(await screen.findByText("approved")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply" })).toBeEnabled();
  });

  it("applies an approved API-backed create memory operation", async () => {
    const user = userEvent.setup();
    mockApplyMemoryOperation.mockResolvedValue({
      id: "op_api",
      type: "create_memory",
      title: "Create summary memory",
      detail: "The user works in Go and wants to learn RL.",
      rationale: "The raw events describe durable user goals.",
      sources: ["evt_api_1"],
      sourceDetails: [
        {
          id: "evt_api_1",
          label: "evt_api_1",
          excerpt: "I use Go and want to learn RL.",
        },
      ],
      confidence: 0.9,
      status: "ready",
      reviewStatus: "applied",
    });

    render(
      <MemoryWorkbench
        refactorRuns={[
          {
            id: "run_api",
            title: "API-backed memory cleanup",
            status: "review",
            sourceCount: 1,
            operationCount: 1,
            confidence: 0.9,
            startedAt: "2026-05-03 12:30 UTC",
          },
        ]}
        operationsByRunId={{
          run_api: [
            {
              id: "op_api",
              type: "create_memory",
              title: "Create summary memory",
              detail: "The user works in Go and wants to learn RL.",
              rationale: "The raw events describe durable user goals.",
              sources: ["evt_api_1"],
              sourceDetails: [
                {
                  id: "evt_api_1",
                  label: "evt_api_1",
                  excerpt: "I use Go and want to learn RL.",
                },
              ],
              confidence: 0.9,
              status: "ready",
              reviewStatus: "approved",
            },
          ],
        }}
        runDataSource="api"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Apply" }));

    expect(mockApplyMemoryOperation).toHaveBeenCalledWith({
      runId: "run_api",
      operationId: "op_api",
    });
    expect(await screen.findByText("applied")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Applied" })).toBeDisabled();
  });

  it("rejects an API-backed memory operation", async () => {
    const user = userEvent.setup();
    mockReviewMemoryOperation.mockResolvedValue({
      id: "op_api",
      type: "create_memory",
      title: "Create summary memory",
      detail: "The user works in Go and wants to learn RL.",
      rationale: "The raw events describe durable user goals.",
      sources: ["evt_api_1"],
      sourceDetails: [
        {
          id: "evt_api_1",
          label: "evt_api_1",
          excerpt: "I use Go and want to learn RL.",
        },
      ],
      confidence: 0.9,
      status: "conflict",
      reviewStatus: "rejected",
    });

    render(
      <MemoryWorkbench
        refactorRuns={[
          {
            id: "run_api",
            title: "API-backed memory cleanup",
            status: "review",
            sourceCount: 1,
            operationCount: 1,
            confidence: 0.9,
            startedAt: "2026-05-03 12:30 UTC",
          },
        ]}
        operationsByRunId={{
          run_api: [
            {
              id: "op_api",
              type: "create_memory",
              title: "Create summary memory",
              detail: "The user works in Go and wants to learn RL.",
              rationale: "The raw events describe durable user goals.",
              sources: ["evt_api_1"],
              sourceDetails: [
                {
                  id: "evt_api_1",
                  label: "evt_api_1",
                  excerpt: "I use Go and want to learn RL.",
                },
              ],
              confidence: 0.9,
              status: "review",
              reviewStatus: "needs_review",
            },
          ],
        }}
        runDataSource="api"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Reject" }));

    expect(mockReviewMemoryOperation).toHaveBeenCalledWith({
      runId: "run_api",
      operationId: "op_api",
      decision: "rejected",
    });
    expect(await screen.findByText("rejected")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Rejected" })).toBeDisabled();
  });
});
