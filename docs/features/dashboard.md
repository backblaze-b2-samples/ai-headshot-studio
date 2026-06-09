<!-- last_verified: 2026-06-09 -->
# Feature: Dashboard

## Purpose
Give an at-a-glance overview of the headshot workload: how many subjects,
headshots, and trained models exist, and how B2 storage is split across
artifact types.

## Used By
- UI: `/` page (dashboard home)
- API: `GET /stats/studio`, `GET /subjects`

## Core Functions
- `apps/web/src/components/dashboard/stats-cards.tsx` — 4 metric cards
- `apps/web/src/components/dashboard/storage-breakdown.tsx` — storage by artifact type (bar chart)
- `apps/web/src/components/dashboard/recent-subjects-table.tsx` — most recent subjects
- `apps/web/src/lib/api-client.ts` — `getStudioStats()`, `getSubjects()`
- `services/api/app/runtime/generation.py` — `GET /stats/studio` handler
- `services/api/app/service/stats.py` — `get_studio_stats()` aggregation
- `services/api/app/repo/b2_client.py` — `list_files()` over the `subjects/` prefix

## Canonical Files
- Stats aggregation: `services/api/app/service/stats.py`
- Stat cards: `apps/web/src/components/dashboard/stats-cards.tsx`

## Inputs
- None (dashboard loads data automatically)

## Outputs
- `GET /stats/studio` → `StudioStats`: `subjects`, `headshots_generated`,
  `models_trained`, `storage_bytes`, `storage_human`, and a `breakdown` of
  `StorageSlice` (per category: selfies, captions, models, headshots, other)
- `GET /subjects` → `SubjectSummary[]` for the recent-subjects table

## Flow
- Page loads → parallel calls for studio stats and the subjects list
- Stat cards: Subjects, Headshots Generated, Models Trained, B2 Storage Used
- Storage breakdown: megabytes per artifact category, scoped to `subjects/`
- Recent subjects table: name, headshot count, created date, status badge

## Edge Cases
- API unavailable → inline `ErrorState` with Retry (cards don't lie with zeros)
- No subjects → empty chart + empty table messages
- Large object count → `list_files` is bounded; stats aggregate the `subjects/` prefix

## UX States
- Loading: skeleton placeholders for cards and table
- Empty: "No artifacts yet" / "No subjects yet"
- Loaded: populated cards, chart, table

## Verification
- Test files: `services/api/tests/test_subjects_api.py` (`test_studio_stats_aggregates_by_artifact`)
- Quick verify: `pnpm test:api` and `pnpm build`
- Pass criteria: stats aggregate by artifact category; dashboard builds and renders

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
