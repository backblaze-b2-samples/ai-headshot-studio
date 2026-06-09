<!-- last_verified: 2026-05-21 -->
# Dev Workflows

Engineering workflows for this repo.

## New Feature

- [ ] Read `AGENTS.md` and `ARCHITECTURE.md`
- [ ] Read the relevant feature doc in `docs/features/`
- [ ] For non-trivial changes, create a plan in `docs/exec-plans/active/`
- [ ] Implement the smallest coherent change
- [ ] Add or update tests
- [ ] Run: `pnpm typecheck && pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- [ ] Update docs in the same PR (see AGENTS.md §8)
- [ ] Move plan to `docs/exec-plans/completed/` after validation

## Engines (training & generation)

The core loop is **really wired, never simulated**. Two real engines, selected
by `TRAINER_PROVIDER` / `GENERATOR_PROVIDER`:

- `local` (default) — real SD-1.5 LoRA fine-tune + generation via `diffusers`+`peft`,
  $0 / no keys. First run downloads SD-1.5 weights to the HF cache.
- `replicate` (opt-in) — real hosted FLUX calls; needs `REPLICATE_API_TOKEN`; costs money.

Rules when touching an engine:
- [ ] Keep heavy SDK imports **lazy and inside the adapter method** (see AGENTS.md §3 SDK containment)
- [ ] Never add a simulated/mock trainer or generator
- [ ] Verify the real loop with a tiny test pipeline (e.g. `hf-internal-testing/tiny-stable-diffusion-pipe`),
      1–2 selfies, 1–2 steps — confirm a real `.safetensors` and real PNGs are written
- [ ] The full SD-1.5 and hosted FLUX paths are also verified offline for imports/types/wiring

## Bugfix

- [ ] Add a failing test that reproduces the bug
- [ ] Confirm the test fails
- [ ] Implement the fix
- [ ] Rerun tests until green
- [ ] Update docs if behavior changed

## Refactor

- [ ] Read `ARCHITECTURE.md` — respect layering rules
- [ ] Ensure structural tests still pass: `pnpm check:structure`
- [ ] No behavior changes without updating feature docs

## Documentation Update

- [ ] Update only the canonical location (see AGENTS.md §8 doc update mapping)
- [ ] Never duplicate content — link instead
- [ ] Update `<!-- last_verified: YYYY-MM-DD -->` header

## Pull Request

- [ ] One coherent change per PR
- [ ] Run full lint + test suite before submitting
- [ ] Docs updated in the same PR as code changes
- [ ] Only change files relevant to the task — no drive-by improvements

## Testing

### Test types
- **Unit**: pure logic (service layer)
- **Integration**: HTTP handlers, B2 connectivity (`tests/`)
- **Structural**: layering rules, import boundaries (`tests/test_structure.py`)
- **E2E**: Playwright browser-driven smoke tests

### Test placement
- Backend: `services/api/tests/`
- E2E: project root (Playwright)

### Commands
- Quick (backend): `pnpm test:api`
- Structure: `pnpm check:structure`
- Frontend typecheck: `pnpm typecheck`
- Frontend lint: `pnpm lint`
- Backend lint: `pnpm lint:api`
- Full suite: `pnpm typecheck && pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- E2E: `pnpm test:e2e` (run `pnpm --filter @ai-headshot-studio/web exec playwright install chromium` once first)

### When to run
- After behavior change: run relevant subset
- Before PR: run full suite

## Frontend Conventions

- Tailwind v4: config via CSS `@theme` blocks, NOT `tailwind.config.ts`
- Colors: OKLch format
- Dark mode: `next-themes` with `@custom-variant dark (&:is(.dark *))`
- Animations: `tw-animate-css` (not `tailwindcss-animate`)
- shadcn/ui components in `src/components/ui/` are generated — never modify them

## Data Fetching

All API reads/writes flow through TanStack Query hooks in
`apps/web/src/lib/queries.ts`. Don't add bare `useEffect + fetch` patterns
to components.

**Read** — use the hooks directly:

```tsx
const { data, isLoading, error, refetch } = useFiles(prefix, limit);
const { data: stats } = useFileStats();
```

Surface errors via `<ErrorState error={error} onRetry={() => refetch()} />`
rather than silently rendering empty UI.

**Write** — wrap mutations with `useMutation` and invalidate on success:

```tsx
const deleteMutation = useDeleteFile();
deleteMutation.mutate(file.key, {
  onSuccess: () => toast.success("Deleted"),
});
```

`useDeleteFile()` already calls `queryClient.invalidateQueries({ queryKey: qk.all })`
on success — every consumer of `useFiles` / `useFileStats` re-fetches lazily.

**Add a new endpoint** — three places to touch:
1. `services/api/app/runtime/<router>.py` — FastAPI route
2. `apps/web/src/lib/api-client.ts` — typed fetch wrapper
3. `apps/web/src/lib/queries.ts` — `useQuery` / `useMutation` hook + entry in `qk`

Defaults (in `apps/web/src/lib/query-client.tsx`):
- `staleTime: 30s` — file lists / stats don't change second-to-second
- `retry: 1` for transient errors; never retry 4xx (won't get better)
- `refetchOnWindowFocus`: on (TanStack default) — dashboard self-heals
  when the user comes back to the tab
