<!-- last_verified: 2026-06-09 -->
# Feature: Face-Data Privacy Lifecycle

## Purpose
Treat headshots as the face data they are: presigned-only access, no public
objects, and a real one-click *right-to-be-forgotten* purge that removes every
B2 object belonging to a subject.

## Used By
- UI: `/gallery/[subjectId]` → "Delete subject" (`purge-dialog.tsx`)
- API: `DELETE /subjects/{id}`

## Core Functions
- `services/api/app/service/subjects.py` — `purge_subject`, `validate_subject_id`
- `services/api/app/repo/b2_client.py` — `delete_prefix` (list + batch `DeleteObjects`), `list_keys`
- `apps/web/src/components/gallery/purge-dialog.tsx`
- `apps/web/src/lib/queries.ts` — `usePurgeSubject`

## Canonical Files
- Purge service: `services/api/app/service/subjects.py`
- Batch-delete data access: `services/api/app/repo/b2_client.py`

## Inputs
- `subjectId` (route param) — validated as a 32-char hex UUID before use

## Outputs
- `DELETE /subjects/{id}` → `{ purged, subject_id, objects_deleted }`
- Side effect: every object under `subjects/{id}/` removed from B2 (selfies,
  captions, the trained LoRA, all headshots, and the manifest)

## Flow
- User confirms in the alert dialog (irreversible, clearly worded)
- `validate_subject_id` ensures the id is a hex UUID — it can never form a
  prefix that escapes one subject's namespace
- `delete_prefix` lists `subjects/{id}/` (paginated) and deletes in 1000-key
  `DeleteObjects` batches
- The UI invalidates caches and returns to `/gallery`

## Security properties
- **Presigned-only access.** Headshots/selfies are never public; previews and
  downloads use short-lived presigned URLs with forced attachment.
- **Bounded blast radius.** The validated UUID + deterministic key layout mean
  a purge touches exactly one subject.
- **No orphaned data.** Because B2 is the sole store and all of a subject's data
  lives under one prefix, the purge is complete by construction.

## Edge Cases
- Invalid subject id → 400 (never reaches B2)
- B2 failure mid-purge → 500; the operation is idempotent and safe to retry
- Already-purged subject → deletes 0 objects, still returns success

## Verification
- Test files: `services/api/tests/test_subjects_api.py` (`test_purge_removes_every_object`), `test_subjects_store.py` (id validation)
- Quick verify: `pnpm test:api`
- Pass criteria: after purge, no object under `subjects/{id}/` remains

## Related Docs
- [docs/SECURITY.md](../SECURITY.md#face-data-handling)
- [Headshot Gallery](headshot-gallery.md)
