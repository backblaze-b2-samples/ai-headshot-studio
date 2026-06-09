<!-- last_verified: 2026-06-09 -->
# App Workflows

User journeys inside the application.

## Create headshots (the main flow)

- User navigates to `/studio`
- **Step 1 — Name the subject.** Enter a name → `POST /subjects` returns a UUID
- **Step 2 — Upload selfies.** Drop 4–20 selfies; each uploads to the subject
  prefix (`POST /subjects/{id}/selfies`) with per-file progress
- **Step 3 — Caption & train.** "Auto-caption" runs Claude vision (or a
  templated fallback); "Train likeness" starts a real LoRA fine-tune as a
  background job. A progress bar polls `GET /subjects/{id}/progress` @1.5s
- **Step 4 — Pick style packs & generate.** Select packs (Corporate, LinkedIn,
  Creative, Outdoor, Editorial B&W) → "Generate" renders real headshots per
  pack as a background job, with a progress bar
- On completion: "View gallery" opens the subject detail
- See: [Subject Training](features/subject-training.md), [Headshot Generation](features/headshot-generation.md)

## Browse the gallery

- User navigates to `/gallery` — a grid of subjects (status, counts)
- Clicking a subject opens `/gallery/[subjectId]`:
  - Live training/generation progress while a job runs
  - Headshots grouped by style pack; hover an image to download
  - **Delete subject** opens a confirmation that batch-purges all face data
- Empty state when no subjects/headshots yet
- See: [Headshot Gallery](features/headshot-gallery.md), [Privacy Lifecycle](features/privacy-lifecycle.md)

## Delete a subject (right-to-be-forgotten)

- On a subject detail page, click **Delete subject**
- Confirm the irreversible action in the dialog
- `DELETE /subjects/{id}` batch-deletes every object under `subjects/{id}/`
- Toast reports the number of objects removed; user returns to `/gallery`
- See: [Privacy Lifecycle](features/privacy-lifecycle.md)

## View the dashboard

- User navigates to `/` (home)
- Parallel calls load studio stats and the subjects list
- Stat cards: Subjects, Headshots Generated, Models Trained, B2 Storage Used
- Storage breakdown chart: megabytes per artifact type (selfies, captions, models, headshots)
- Recent subjects table: name, headshot count, created date, status
- See: [Dashboard](features/dashboard.md)

## Browse the full bucket (kept scaffolding)

- `/upload` — generic drag-and-drop upload to the `uploads/` prefix
- `/files` — full-bucket tree browser with preview, download, delete
- See: [File Upload](features/file-upload.md), [File Browser](features/file-browser.md)
