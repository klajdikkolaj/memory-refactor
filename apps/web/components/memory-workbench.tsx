"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Database,
  FileText,
  GitMerge,
  GitPullRequest,
  Layers3,
  Network,
  Play,
  Search,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { memoryOperations, refactorRuns, timeline } from "@/lib/sample-data";
import type { MemoryOperation, RefactorStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

type Filter = "all" | RefactorStatus;

const filterOptions: { label: string; value: Filter }[] = [
  { label: "All", value: "all" },
  { label: "Review", value: "review" },
  { label: "Conflict", value: "conflict" },
  { label: "Ready", value: "ready" },
];

const statusStyles: Record<RefactorStatus, string> = {
  review: "border-moss/25 bg-moss/10 text-moss",
  running: "border-blue-500/25 bg-blue-50 text-blue-700",
  ready: "border-emerald-500/25 bg-emerald-50 text-emerald-700",
  conflict: "border-flame/25 bg-flame/10 text-flame",
};

const operationIcons: Record<MemoryOperation["type"], typeof GitMerge> = {
  merge: GitMerge,
  supersede: Layers3,
  archive: FileText,
  flag_contradiction: AlertTriangle,
};

export function MemoryWorkbench() {
  const [selectedRunId, setSelectedRunId] = useState(refactorRuns[0].id);
  const [filter, setFilter] = useState<Filter>("all");
  const [selectedOperationId, setSelectedOperationId] = useState(memoryOperations[0].id);

  const selectedRun = refactorRuns.find((run) => run.id === selectedRunId) ?? refactorRuns[0];

  const visibleOperations = useMemo(() => {
    if (filter === "all") {
      return memoryOperations;
    }

    return memoryOperations.filter((operation) => operation.status === filter);
  }, [filter]);

  const selectedOperation =
    memoryOperations.find((operation) => operation.id === selectedOperationId) ??
    visibleOperations[0] ??
    memoryOperations[0];

  return (
    <main className="min-h-screen bg-paper text-ink">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[232px_minmax(0,1fr)_360px]">
        <aside className="border-b border-line bg-white/76 px-5 py-5 lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-ink text-white">
              <Network className="h-4 w-4" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold">Memory Refactor</p>
              <p className="text-xs text-zinc-500">Compiler workspace</p>
            </div>
          </div>

          <nav className="mt-8 grid gap-1 text-sm">
            {[
              { label: "Memory PRs", icon: GitPullRequest, active: true },
              { label: "Explorer", icon: Search, active: false },
              { label: "Workflows", icon: Workflow, active: false },
              { label: "Sources", icon: Database, active: false },
              { label: "Audit", icon: ShieldCheck, active: false },
            ].map((item) => (
              <button
                key={item.label}
                className={cn(
                  "flex h-10 items-center gap-3 rounded-lg px-3 text-left text-zinc-600 transition",
                  item.active ? "bg-zinc-950 text-white" : "hover:bg-zinc-100 hover:text-zinc-950",
                )}
                type="button"
              >
                <item.icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          <div className="mt-8 border-t border-line pt-5">
            <p className="text-xs font-medium uppercase text-zinc-500">Active stack</p>
            <div className="mt-3 grid gap-2 text-sm">
              {["Next.js", "FastAPI", "Temporal", "Postgres + pgvector"].map((item) => (
                <div key={item} className="flex items-center gap-2 text-zinc-700">
                  <CheckCircle2 className="h-4 w-4 text-moss" aria-hidden="true" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <section className="min-w-0 px-4 py-5 sm:px-6 lg:px-8">
          <header className="flex flex-col gap-4 border-b border-line pb-5 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <h1 className="text-2xl font-semibold">Memory PR review</h1>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-zinc-600">
                Review typed memory operations before they become canonical state.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                className="inline-flex h-10 items-center gap-2 rounded-lg border border-line bg-white px-3 text-sm font-medium text-zinc-700 shadow-sm transition hover:border-zinc-300"
                type="button"
              >
                <Clock3 className="h-4 w-4" aria-hidden="true" />
                Schedule
              </button>
              <button
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-ink px-3 text-sm font-medium text-white shadow-sm transition hover:bg-zinc-800"
                type="button"
              >
                <Play className="h-4 w-4" aria-hidden="true" />
                Run refactor
              </button>
            </div>
          </header>

          <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <section className="rounded-lg border border-line bg-white shadow-panel">
              <div className="border-b border-line px-4 py-3">
                <p className="text-sm font-semibold">Refactor runs</p>
              </div>
              <div className="divide-y divide-line">
                {refactorRuns.map((run) => (
                  <button
                    key={run.id}
                    className={cn(
                      "grid w-full gap-3 px-4 py-4 text-left transition hover:bg-zinc-50",
                      selectedRunId === run.id && "bg-zinc-50",
                    )}
                    onClick={() => setSelectedRunId(run.id)}
                    type="button"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium">{run.title}</p>
                        <p className="mt-1 text-xs text-zinc-500">{run.startedAt}</p>
                      </div>
                      <StatusBadge status={run.status} />
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs text-zinc-600">
                      <Metric label="Sources" value={run.sourceCount.toString()} />
                      <Metric label="Ops" value={run.operationCount.toString()} />
                      <Metric label="Conf." value={`${Math.round(run.confidence * 100)}%`} />
                    </div>
                  </button>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-line bg-white shadow-panel">
              <div className="flex flex-col gap-3 border-b border-line px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-semibold">Proposed operations</p>
                  <p className="mt-1 text-xs text-zinc-500">{selectedRun.title}</p>
                </div>
                <div className="flex rounded-lg border border-line bg-zinc-50 p-1">
                  {filterOptions.map((option) => (
                    <button
                      key={option.value}
                      className={cn(
                        "h-8 rounded-md px-3 text-xs font-medium text-zinc-600 transition",
                        filter === option.value && "bg-white text-zinc-950 shadow-sm",
                      )}
                      onClick={() => setFilter(option.value)}
                      type="button"
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="divide-y divide-line">
                {visibleOperations.map((operation) => {
                  const Icon = operationIcons[operation.type];

                  return (
                    <button
                      key={operation.id}
                      className={cn(
                        "grid w-full gap-3 px-4 py-4 text-left transition hover:bg-zinc-50",
                        selectedOperation.id === operation.id && "bg-zinc-50",
                      )}
                      onClick={() => setSelectedOperationId(operation.id)}
                      type="button"
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-line bg-white text-zinc-700">
                          <Icon className="h-4 w-4" aria-hidden="true" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-medium">{operation.title}</p>
                            <StatusBadge status={operation.status} />
                          </div>
                          <p className="mt-1 text-sm leading-6 text-zinc-600">{operation.detail}</p>
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 pl-11 text-xs text-zinc-500">
                        {operation.sources.map((source) => (
                          <span key={source} className="rounded-md border border-line px-2 py-1">
                            {source}
                          </span>
                        ))}
                        <span>{Math.round(operation.confidence * 100)}% confidence</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>
          </div>

          <section className="mt-4 rounded-lg border border-line bg-white shadow-panel">
            <div className="border-b border-line px-4 py-3">
              <p className="text-sm font-semibold">Durable workflow</p>
            </div>
            <div className="grid gap-3 p-4 md:grid-cols-5">
              {timeline.map((event) => (
                <div key={event.id} className="min-w-0">
                  <div
                    className={cn(
                      "mb-3 h-1 rounded-full",
                      event.state === "complete" && "bg-moss",
                      event.state === "current" && "bg-flame",
                      event.state === "pending" && "bg-zinc-200",
                    )}
                  />
                  <p className="text-sm font-medium">{event.label}</p>
                  <p className="mt-1 text-xs leading-5 text-zinc-500">{event.detail}</p>
                </div>
              ))}
            </div>
          </section>
        </section>

        <aside className="border-t border-line bg-white px-5 py-5 lg:border-l lg:border-t-0">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">Operation detail</p>
              <p className="mt-1 text-xs text-zinc-500">{selectedOperation.id}</p>
            </div>
            <StatusBadge status={selectedOperation.status} />
          </div>

          <div className="mt-5 rounded-lg border border-line p-4">
            <p className="text-xs font-medium uppercase text-zinc-500">Proposal</p>
            <h2 className="mt-2 text-lg font-semibold">{selectedOperation.title}</h2>
            <p className="mt-3 text-sm leading-6 text-zinc-600">{selectedOperation.detail}</p>
          </div>

          <div className="mt-4 rounded-lg border border-line p-4">
            <p className="text-xs font-medium uppercase text-zinc-500">Sources</p>
            <div className="mt-3 grid gap-2">
              {selectedOperation.sources.map((source) => (
                <button
                  key={source}
                  className="flex h-10 items-center justify-between rounded-lg border border-line px-3 text-left text-sm transition hover:border-zinc-300"
                  type="button"
                >
                  <span>{source}</span>
                  <FileText className="h-4 w-4 text-zinc-400" aria-hidden="true" />
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-2">
            <button
              className="h-10 rounded-lg border border-line bg-white text-sm font-medium text-zinc-700 transition hover:border-zinc-300"
              type="button"
            >
              Reject
            </button>
            <button
              className="h-10 rounded-lg bg-moss text-sm font-medium text-white transition hover:bg-[#285f43]"
              type="button"
            >
              Approve
            </button>
          </div>
        </aside>
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: RefactorStatus }) {
  return (
    <span className={cn("rounded-md border px-2 py-1 text-xs font-medium", statusStyles[status])}>
      {status}
    </span>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-white px-2 py-2">
      <p className="font-semibold text-zinc-950">{value}</p>
      <p className="mt-0.5 text-zinc-500">{label}</p>
    </div>
  );
}
