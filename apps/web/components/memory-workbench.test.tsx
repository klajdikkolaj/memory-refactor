import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { MemoryWorkbench } from "@/components/memory-workbench";

describe("MemoryWorkbench", () => {
  it("renders the review workspace", () => {
    render(<MemoryWorkbench />);

    expect(screen.getByRole("heading", { name: "Memory PR review" })).toBeInTheDocument();
    expect(screen.getAllByText("Developer direction cleanup")).toHaveLength(2);
    expect(screen.getAllByText("Merge AI infrastructure product goals")).toHaveLength(2);
  });

  it("filters operations by conflict status", async () => {
    const user = userEvent.setup();
    render(<MemoryWorkbench />);

    await user.click(screen.getByRole("button", { name: "Conflict" }));

    expect(screen.getByText("Resolve graph layer timing")).toBeInTheDocument();
    expect(screen.queryByText("Archive obsolete NestJS-only plan")).not.toBeInTheDocument();
  });
});
