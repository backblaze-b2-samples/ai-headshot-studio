<!-- last_verified: 2026-06-09 -->
# Architecture

## Components

- **apps/web/** — Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  - **Studio** (`/studio`) — guided create flow: selfies → caption → train → pick style packs → generate
  - **Gallery** (`/gallery`, `/gallery/[subjectId]`) — scoped subject → per-style headshot explorer, with download + purge
  - **Dashboard** (`/`) — headshot metrics (subjects, headshots, models, storage) + storage breakdown by artifact type
  - **Files** (`/files`) full-bucket browser + **Upload** (`/upload`) drag-and-drop — the kept reusable B2 scaffolding
  - Dark mode via `next-themes`
- **services/api/** — FastAPI backend (layered architecture)
  - Subject lifecycle (create / list / get / purge), selfie ingestion, captioning
  - Real LoRA training and headshot generation via swappable engine adapters
  - B2 S3 integration via boto3 (incl. batch `DeleteObjects` for purge)
  - Health check, structured JSON logging, Prometheus-format metrics
- **packages/shared/** — TypeScript type definitions mirroring the Pydantic models

## Backend Layering

```
types/     Pydantic models — no logic, no imports from other layers
  |
config/    Settings (pydantic-settings) — depends only on types
  |
repo/      Data access + external-SDK adapters (boto3, diffusers, replicate, anthropic)
  |
service/   Business logic — orchestrates repo, returns types
  |
runtime/   FastAPI routes — calls service, never repo directly
```

### Layering Rules

1. Dependencies flow downward only: `types` -> `config` -> `repo` -> `service` -> `runtime`
2. No backward imports
3. `boto3` only in `repo/` layer (verified by `tests/test_structure.py`)
4. **All external SDKs (`diffusers`/`torch`/`transformers`/`peft`, `replicate`, `anthropic`) are confined to `repo/` and lazy-imported inside their adapters** — never imported at app load, so `pnpm dev` and test collection stay light
5. All boundary data uses Pydantic models
6. Each file stays under 300 lines

### Directory Structure

```
services/api/
  main.py                  App entrypoint, middleware, router registration
  app/
    types/                 Pydantic models (subject, style, headshot, stats, files, upload)
    config/                Settings (B2 + engine providers + hyperparameters)
    repo/                  Data access + adapters:
      b2_client.py           B2 S3 wrapper (put/get/list/delete/batch-delete/presign)
      subjects_store.py      Manifest read/write + B2 key generators (system of record)
      trainer/               base.py, local.py (REAL SD-1.5 LoRA), replicate.py (FLUX), __init__ dispatcher
      generator/             base.py, local.py (REAL diffusers), replicate.py (FLUX), __init__ dispatcher
      captioner.py           Optional Claude vision captioner (templated fallback)
    service/               Business logic:
      subjects.py, captioning.py, training.py, generation.py, styles.py, stats.py
      upload.py, files.py, metadata.py   (kept generic scaffolding)
    runtime/               FastAPI routers:
      subjects.py, generation.py, files.py, upload.py, health.py, metrics.py
  tests/                   pytest (structural + integration with in-memory B2)
```

## Engine adapters (the headshot core)

Training and generation each have a small adapter interface and two real
implementations, selected by `TRAINER_PROVIDER` / `GENERATOR_PROVIDER`:

- **`local` (default)** — `repo/trainer/local.py` really fine-tunes an SD-1.5
  LoRA with `diffusers`+`peft`; `repo/generator/local.py` loads that LoRA and
  renders real PNGs. $0, no keys. Heavy ML imports happen lazily inside these
  two files only.
- **`replicate` (opt-in)** — `repo/trainer/replicate.py` and
  `repo/generator/replicate.py` make real hosted FLUX-LoRA calls. Gated behind
  `REPLICATE_API_TOKEN`; costs money; never the default.

There is **no simulated trainer or generator** — every LoRA is fit on the
subject's selfies and every headshot is a genuine model output.

## Async pattern

Training and generation run as FastAPI **`BackgroundTasks`**. Progress is
written into the subject's manifest (`subjects/{id}/subject.json`) on B2 — the
single source of truth — and the frontend polls `GET /subjects/{id}/progress`
(every 1.5s while the status is `captioning`/`training`/`generating`). No DB,
no in-memory job store.

## Data Stores

- **Backblaze B2** — the sole data store (S3-compatible API). No application
  database. Object layout:

```
subjects/{subject_id}/
  subject.json                       manifest: status, config, captions, metrics, artifact keys
  selfies/{image_id}.{ext}           uploaded training selfies
  captions/{image_id}.txt            one caption per selfie
  model/{subject_id}.safetensors     trained likeness LoRA
  headshots/{style_slug}/{NN}.png    generated headshots, grouped by style pack
```

Subject ids are server-assigned UUIDs; all keys are derived from them, so no
user-supplied prefix ever reaches B2. The generic `/upload` path keeps writing
to the starter's `uploads/` prefix.

## Trust Boundaries

See [docs/SECURITY.md](docs/SECURITY.md) for full documentation.

- **Frontend -> API** — CORS-restricted to configured origins
- **API -> B2** — authenticated via application keys, signature v4, custom user agent
- **Client -> B2** — presigned URLs only (short expiry, forced attachment); no public objects
- **Purge / batch-delete** — `DELETE /subjects/{id}` lists `subjects/{id}/` and
  removes it with `DeleteObjects` in 1000-key chunks. The id is validated as a
  32-char hex UUID before it ever forms a prefix, so the purge can never escape
  a single subject's namespace.

## Data Flows

- **Create subject**: `POST /subjects` -> server-assigned UUID -> manifest written to B2
- **Add selfie**: `POST /subjects/{id}/selfies` (multipart) -> repo writes `selfies/{image_id}.ext` -> manifest updated
- **Caption**: `POST /subjects/{id}/caption` -> captioner (Claude or template) -> `captions/*.txt` + manifest
- **Train (async)**: `POST /subjects/{id}/train` -> status TRAINING -> BackgroundTask runs the real trainer -> LoRA written to `model/` -> status TRAINED; progress polled from the manifest
- **Generate (async)**: `POST /subjects/{id}/generate` -> status GENERATING -> BackgroundTask renders per style pack -> PNGs written to `headshots/{slug}/` -> status COMPLETE
- **Gallery**: `GET /subjects/{id}/gallery` -> presigned preview URLs grouped by style pack
- **Purge**: `DELETE /subjects/{id}` -> batch-delete the whole `subjects/{id}/` prefix
- **Stats**: `GET /stats/studio` -> aggregate the `subjects/` prefix into per-artifact storage slices

## Observability

- Structured JSON logging on all requests with `request_id`
- Request timing middleware; `/metrics` (Prometheus format); `/health` (B2 connectivity)

## Canonical Files

- B2 data access (repo): `services/api/app/repo/b2_client.py`
- System of record: `services/api/app/repo/subjects_store.py`
- Real training adapter: `services/api/app/repo/trainer/local.py`
- Real generation adapter: `services/api/app/repo/generator/local.py`
- Job orchestration: `services/api/app/service/{training,generation}.py`
- Style registry: `services/api/app/service/styles.py`
- Pydantic models: `services/api/app/types/`
- Config: `services/api/app/config/settings.py`
- Structural tests: `services/api/tests/test_structure.py`
- Frontend API client / hooks: `apps/web/src/lib/{api-client,queries}.ts`
- Shared TypeScript types: `packages/shared/src/types.ts`

## References

- [docs/SECURITY.md](docs/SECURITY.md) — security principles + face-data handling
- [docs/RELIABILITY.md](docs/RELIABILITY.md) — reliability expectations
- [AGENTS.md](AGENTS.md) — architectural invariants and agent instructions
