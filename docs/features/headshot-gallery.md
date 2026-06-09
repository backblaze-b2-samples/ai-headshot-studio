<!-- last_verified: 2026-06-09 -->
# Feature: Headshot Gallery

## Purpose
A sample-specific, scoped asset explorer for generated headshots: browse
subjects, then drill into a per-style grid — the scoped counterpart to the kept
full-bucket `/files` browser.

## Used By
- UI: `/gallery` (subject list), `/gallery/[subjectId]` (per-subject detail)
- API: `GET /subjects`, `GET /subjects/{id}`, `GET /subjects/{id}/gallery`, `GET /subjects/{id}/progress`

## Core Functions
- `services/api/app/service/subjects.py` — `list_subjects`, `get_subject_gallery`
- `apps/web/src/components/gallery/subject-grid.tsx` — subject cards
- `apps/web/src/components/gallery/subject-detail.tsx` — per-subject detail
- `apps/web/src/components/gallery/style-section.tsx` — per-style headshot grid
- `apps/web/src/lib/queries.ts` — `useSubjects`, `useSubject`, `useSubjectGallery`, `useSubjectProgress`

## Canonical Files
- Gallery service: `services/api/app/service/subjects.py`

## Inputs
- None for the list; `subjectId` (route param) for the detail

## Outputs
- `GET /subjects` → `SubjectSummary[]` (scans the `subjects/` prefix for manifests)
- `GET /subjects/{id}/gallery` → `StyleSection[]` — headshots grouped by style pack,
  each with a short-lived presigned preview URL

## Flow
- `/gallery` lists subjects (status badge, selfie/headshot counts)
- Clicking a subject opens `/gallery/[subjectId]`: training/generation progress
  (polled), headshots grouped by style pack, per-image download, and Delete subject
- Images render via `next/image` with `unoptimized` from presigned B2 URLs

## Edge Cases
- Unknown subject id → 404
- No headshots yet → empty state ("Train and generate from the Studio")
- A headshot whose style slug is no longer in the registry is skipped

## UX States
- Loading: skeletons
- Empty: "No subjects yet" / "No headshots yet"
- Live: progress bars while `training`/`generating` (polled @1.5s)

## Verification
- Test files: `services/api/tests/test_subjects_api.py`
- Required cases: create→list→get, unknown subject 404, styles endpoint
- Quick verify: `pnpm test:api` and `pnpm build`
- Pass criteria: tests green; `/gallery` and `/gallery/[subjectId]` build and route

## Related Docs
- [Privacy Lifecycle](privacy-lifecycle.md)
- [File Browser](file-browser.md)
- [Headshot Generation](headshot-generation.md)
