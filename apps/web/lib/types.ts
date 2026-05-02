export type RefactorStatus = "review" | "running" | "ready" | "conflict";

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
  type: "merge" | "supersede" | "archive" | "flag_contradiction";
  title: string;
  detail: string;
  sources: string[];
  confidence: number;
  status: RefactorStatus;
};

export type TimelineEvent = {
  id: string;
  label: string;
  detail: string;
  state: "complete" | "current" | "pending";
};
