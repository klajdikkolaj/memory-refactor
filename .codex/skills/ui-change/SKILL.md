---
name: ui-change
description: Use when changing the Next.js dashboard, React components, UI state, data fetching, accessibility, or browser flows.
---

# UI Change

## Goal

Keep the product UI useful, testable, accessible, and consistent with the memory-review workflow.

## Start Here

- Read `docs/testing-strategy.md`.
- Inspect `apps/web/components`, `apps/web/lib`, and the affected route under `apps/web/app`.
- Check whether the change needs API data or can remain local sample state.

## Workflow

1. Identify the user workflow.
   Success criteria: The affected reviewer action or dashboard state is clear.
2. Keep components focused.
   Success criteria: Shared types/data helpers live under `apps/web/lib`; reusable UI lives under `components`.
3. Preserve accessible queries.
   Success criteria: Buttons, headings, filters, and controls can be targeted by role/name in tests.
4. Add or update tests.
   Success criteria: Component tests cover local state; Playwright covers critical browser flow.
5. Run validation.
   Success criteria: `make check-web`, `make test-web-unit`, and `make test-web-e2e` for meaningful browser-flow changes.

## Rules

- Do not add a marketing landing page before the usable product surface.
- Do not introduce decorative UI that makes the operational dashboard harder to scan.
- Keep text within stable layout constraints across desktop and mobile.
- Use existing design tokens and component patterns unless a change is intentional.

## Output

Return:

- User flow changed.
- Components/files touched.
- Tests and browser checks run.
- Any responsive or accessibility risk.
