import { expect, test } from "@playwright/test";

test("reviewer can filter to conflicted memory operations", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Memory PR review" })).toBeVisible();
  await page.getByRole("button", { name: "Conflict", exact: true }).click();

  await expect(page.getByText("Resolve graph layer timing")).toBeVisible();
  await expect(page.getByText("Archive obsolete NestJS-only plan")).toHaveCount(0);
});
