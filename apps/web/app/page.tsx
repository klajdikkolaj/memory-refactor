import { MemoryWorkbench } from "@/components/memory-workbench";
import { fetchRefactorRuns } from "@/lib/refactor-runs";

export default async function Page() {
  const refactorRunResult = await fetchRefactorRuns();

  return (
    <MemoryWorkbench
      refactorRuns={refactorRunResult.runs}
      operationsByRunId={refactorRunResult.operationsByRunId}
      runDataSource={refactorRunResult.source}
      runDataError={refactorRunResult.error}
    />
  );
}
