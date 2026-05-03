import { expect, test } from "@playwright/test";

const memoryApiBaseUrl = process.env.E2E_MEMORY_API_BASE_URL ?? "http://localhost:8000";

test("reviewer can filter to conflicted memory operations", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Memory PR review" })).toBeVisible();
  await page.getByRole("button", { name: "Conflict", exact: true }).click();

  await expect(
    page
      .getByText("Resolve graph layer timing")
      .or(page.getByText("No operations match this view yet.")),
  ).toBeVisible();
  await expect(page.getByText("Archive obsolete NestJS-only plan")).toHaveCount(0);
});

test("reviewer can approve and reject an API-backed memory operation", async ({
  page,
  request,
}) => {
  const health = await request.get(`${memoryApiBaseUrl}/healthz`).catch(() => null);
  test.skip(!health?.ok(), "requires the memory API to be running");

  const preview = await request.post(`${memoryApiBaseUrl}/refactor-runs/preview`);
  expect(preview.ok()).toBeTruthy();
  const plan = await preview.json();
  const operationId = plan.operations[0].id;
  const reviewRequests: unknown[] = [];

  await page.route("**/refactor-runs/*/operations/*/review", async (route) => {
    const apiRequest = route.request();
    if (apiRequest.method() === "PATCH") {
      reviewRequests.push(apiRequest.postDataJSON());
    }

    await route.continue();
  });

  await page.goto("/");

  await expect(page.getByText(operationId)).toBeVisible();
  await page.getByRole("button", { name: "Approve" }).click();

  await expect(page.getByText("approved", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Apply" })).toBeDisabled();
  expect(reviewRequests).toContainEqual({ decision: "approved" });

  await page.getByRole("button", { name: "Reject" }).click();

  await expect(page.getByText("rejected", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Rejected" })).toBeDisabled();
  expect(reviewRequests).toContainEqual({ decision: "rejected" });
});
