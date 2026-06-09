# Plan — `ai-headshot-studio`

Scaffold a new B2 sample from `vibe-coding-starter-kit`. Source of truth for the
delta: `.claude/scratch/vcsk-fbc5e8dd-1edc-4621-9606-def2393fe4f2/` (cloned Phase 0).

---

## 0. Differentiation from the existing `lora-training-studio` sibling

`.local/lora-training-studio` already ships the **generic LoRA fine-tuning workbench**
(dataset → caption → train → loss curve → download `.safetensors`; Library = *runs*).
`ai-headshot-studio` must NOT be a reskin of it. It is a **consumer headshot vertical**
where the framing and the dominant B2 data both flip:

| | lora-training-studio | **ai-headshot-studio** |
|---|---|---|
| Unit of work | a **training run** | a **subject** (a person's likeness) |
| Hero artifact | the trained `.safetensors` | **hundreds of finished headshots** across style packs |
| Dominant B2 data | dataset + checkpoints + 1 LoRA | the **generated headshot gallery** (output-heavy) |
| Killer feature | loss curve / training mechanics | **Style Packs** (Corporate / LinkedIn / Creative / Outdoor / Editorial B&W) + **one-click face-data purge** |
| Scoped explorer | `/library` (runs) | `/gallery` (headshots by subject → style) |
| Privacy story | none | **face-data lifecycle / right-to-be-forgotten** — first-class |

Training here is a *means*; the product is the **styled-headshot generation phase** and
the **privacy lifecycle**, neither of which `lora-training-studio` has. (A further contrast:
`lora-training-studio` **simulates** training by default; `ai-headshot-studio` **really
trains** by default — §4.) The builder builds from the starter kit + this plan only — it
must NOT read the `lora-training-studio` tree.

---

## 1. Purpose

`ai-headshot-studio` is a B2 sample that turns 10–20 selfies into a gallery of
professional headshots. Upload your selfies → (auto-caption) → fine-tune a likeness
LoRA → generate dozens-to-hundreds of headshots across curated **style packs**
(Corporate, LinkedIn, Creative, Outdoor, Editorial B&W) → browse, download, and purge.
**Every artifact in the lifecycle lives on Backblaze B2** — the selfies, the captions,
the trained LoRA, and every generated variant — so the app is a concrete demo of B2 as
the storage layer for a real *train-then-generate-at-scale* AI loop, plus a clean
**face-data privacy lifecycle**. Audience: vibe coders / AI builders evaluating where to
park training data and high-volume generated assets, and the "AI headshot generator"
search crowd (HeadshotPro / Aragon category).

**Real by default — never simulated.** The core capability (train a likeness LoRA →
generate headshots) is genuinely executed, not faked. The **default engine runs locally**
(`diffusers` + `peft` real fine-tuning + generation) at **$0 API cost and no keys** —
heavier deps and modest SD-class quality, but every artifact is real. A **hosted FLUX path
(Replicate)** is a real, opt-in upgrade for quality (~$3–5/run, needs a key — §4). No
simulation anywhere in the pipeline.

---

## 2. Architecture delta from vibe-coding-starter-kit

Starter kit = the ceiling. Strip what this app doesn't need; keep the B2-backed
scaffolding; add the headshot domain.

### KEEP (as-is — starter contract + skill non-negotiables)
- **UI kit / design system**: `apps/web/src/components/ui/`, tokens in `globals.css`, `/design` page. (never edit generated `ui/`)
- **Bucket explorer (`/files`)** — full-bucket browse. **Non-negotiable keep.** `apps/web/src/app/files/`, `components/files/`, `lib/file-tree.ts`.
- **Upload (`/upload`)** — generic drag-and-drop B2 upload. `components/upload/`. (reused by the Studio selfie step)
- **`/settings`**, sidebar shell (`layout/`), command palette, health banner, theme.
- **Backend layering** `types→config→repo→service→runtime`; `repo/b2_client.py` S3 wrapper; `/health`, `/metrics`; structural tests; structured JSON logging.
- **Metadata extraction** (`service/metadata.py`) — still relevant (selfie dims / EXIF / checksum on upload).
- Monorepo tooling: pnpm workspace, `scripts/{dev,doctor,pick-port}`, ruff/eslint, `packages/shared`.

### TRIM (remove from starter)
- **Default Dashboard widgets** — replace upload-centric `stats-cards` / `upload-chart` / `recent-uploads-table` with headshot metrics (§ below). (rewrite, not delete — same files)
- Starter's "this is a template / Use this template" framing in README (replace with product README).
- `docs/features/_template.md` stays (it's the template); no other deletes.

> No removal of `/files` or `/upload`. If that ever seems needed — STOP and ask. (It isn't here.)

### ADD (new for ai-headshot-studio)
**Frontend**
- **`/studio`** — the create flow: upload selfies (reuse dropzone) → caption → "Train likeness" → pick style packs → "Generate". Drives the manifest-backed jobs and polls progress.
- **`/gallery`** — **sample-specific scoped asset explorer** (skill non-negotiable *add*): lists subjects under the `subjects/` prefix; each opens a per-style headshot grid. This is the scoped counterpart to the full-bucket `/files`.
- **`/gallery/[subjectId]`** — per-subject detail: training status, headshot grid grouped by style pack, download, and **Delete subject** (privacy purge).
- New component groups: `components/studio/` (selfie-step, caption-step, train-panel, style-picker, generate-panel), `components/gallery/` (subject-grid, headshot-grid, style-section, purge-dialog), `components/dashboard/` (rewritten cards + storage breakdown).
- New sidebar entries: **Studio** (`Camera`/`Wand2`) and **Gallery** (`Images`). Keep Dashboard/Upload/Files/Settings/Design.
- TanStack Query hooks in `lib/queries.ts`: subjects list/detail, training progress (poll @1.5s while `status` in {captioning,training,generating}), generation progress, stats. No bare `useEffect+fetch`.

**Backend** (all new external SDKs lazy-imported, contained in `repo/`)
- `repo/subjects_store.py` — manifest (`subject.json`) read/write + B2 key generators (§ prefix layout). System-of-record, like the starter's stats but per-subject.
- `repo/trainer/` — `base.py` (Trainer interface + progress callback), `local.py` (**DEFAULT**, `TRAINER_PROVIDER=local`: **real** SD-1.5 LoRA fine-tuning via `diffusers`+`peft`; heavy ML stack lazy-imported inside the adapter only), `replicate.py` (**real opt-in**, `TRAINER_PROVIDER=replicate`: real Replicate FLUX-LoRA training calls — offline-verified, see §Dependencies & verification), `__init__.get_trainer()` dispatcher. **No `simulated` trainer.**
- `repo/generator/` — **the headshot-specific addition**: `base.py`, `local.py` (**DEFAULT**: **real** generation from the trained LoRA via `diffusers`), `replicate.py` (**real opt-in**: FLUX generation with the trained LoRA), `__init__.get_generator()`. **No `simulated` generator** — every headshot in the gallery is a real model output.
- `repo/captioner.py` — optional Claude-vision selfie captioner (Anthropic, §4); templated offline default when no key.
- `service/`: `subjects.py` (create / list / get / **purge**), `captioning.py`, `training.py` (BackgroundTasks job, manifest progress), `generation.py` (BackgroundTasks job across selected style packs), `styles.py` (style-pack registry), `stats.py` (rewritten aggregations).
- `runtime/`: `subjects.py` (create, list, get, DELETE purge), `generation.py` (start generate + progress). Keep `files.py`, `upload.py`, `health.py`, `metrics.py`. Training start/progress folded into `subjects.py` or a small `training.py` router.
- `types/`: `subject.py`, `style.py`, `headshot.py`, rewritten `stats.py`. Keep `files.py`, `formatting.py`; `upload.py` stays.
- `config/settings.py` — add `trainer_provider` (default `local`), `generator_provider` (default `local`), `base_model` (default `runwayml/stable-diffusion-v1-5`), `train_steps`, `headshots_per_style` (default 6), optional `anthropic_api_key`, `replicate_api_token`, style-pack defaults.

**Async pattern (reused, proven):** FastAPI `BackgroundTasks` + manifest polling. `subject.json` on B2 is the single source of truth for status/progress; the frontend polls a `/progress` endpoint. No DB, no in-memory job store.

---

## 3. B2 surface (S3-only — no b2-native)

All operations go through `repo/b2_client.py` (boto3, S3 v4, custom UA). **No b2-native API.**

| App action | S3 operation |
|---|---|
| Upload selfies / write captions / save LoRA / save each headshot / write `subject.json` | `PutObject` |
| `/files` full-bucket browse, `/gallery` scoped list, dashboard stats | `ListObjectsV2` (scoped with `Prefix=subjects/…`) |
| File/headshot metadata, dims | `HeadObject` |
| Preview / download selfie, LoRA, headshot | `GetObject` via **presigned URL** (short expiry, forced attachment) |
| Delete one file | `DeleteObject` |
| **Purge a subject** (privacy lifecycle) | `ListObjectsV2(Prefix=subjects/{id}/)` → batch `DeleteObjects` |

The **purge / batch-delete** path is the new S3 surface vs. the starter and the headline
privacy feature. No b2-native calls anywhere — flag any if they appear in review.

### B2 object-key layout
```
subjects/{subject_id}/
  subject.json                          # manifest: status, config, captions, training metrics, style packs run, artifact keys
  selfies/{image_id}.{ext}              # uploaded training selfies
  captions/{image_id}.txt               # one caption per selfie
  model/{subject_id}.safetensors        # trained likeness LoRA (placeholder in simulated mode)
  headshots/{style_slug}/{NN}.png       # generated headshots, grouped by style pack
```
Server-assigned `subject_id` (UUID); keys are deterministic from subject context — no
user-supplied prefixes (matches the starter's sanitize-don't-trust posture). The generic
`/upload` path keeps writing to the starter's `uploads/` prefix.

---

## 4. Key features (seed README + `docs/features/*`)

1. **Subject training** — upload 10–20 selfies, auto-caption, fine-tune a likeness LoRA. → `docs/features/subject-training.md`
2. **Style packs** — curated prompt sets (Corporate, LinkedIn, Creative, Outdoor, Editorial B&W); data-driven registry, easy to extend. → `docs/features/style-packs.md`
3. **Headshot generation** — apply the likeness LoRA across selected packs to fill a gallery (`headshots_per_style`, default 6 → ~30/run; crank up toward "hundreds"). → `docs/features/headshot-generation.md`
4. **Headshot gallery** — scoped `/gallery` explorer (subject → style), preview/download, on top of the kept full-bucket `/files`. → `docs/features/headshot-gallery.md`
5. **Face-data privacy lifecycle** — one-click **Delete subject** purges every B2 object under `subjects/{id}/` (selfies, captions, LoRA, headshots) via batch delete; presigned-only access, no public objects. → `docs/features/privacy-lifecycle.md`
6. **Headshot dashboard** — cards (Subjects, Headshots generated, Models trained, B2 storage used) + storage breakdown by artifact type. → rewrite `docs/features/dashboard.md`

### External APIs — core vs peripheral (per the corrected `api-provider-selection.md`)
**Core capability = train likeness LoRA → generate headshots. It is REALLY wired, never simulated, never stubbed.**
- **Default engine: local real training & generation** (`diffusers` + `peft`, base model **Stable Diffusion 1.5**). Genuinely fine-tunes a LoRA on the uploaded selfies and generates each headshot from it. **$0 API cost, no keys.** Tradeoffs: heavy Python ML deps (`torch`, `diffusers`, `transformers`, `peft`, `accelerate`) and SD-class quality (modest, but real); usable speed wants GPU/MPS, runs (slowly) on CPU. Heavy stack **lazy-imported inside the `local` adapters only**, so the rest of the app and `pnpm dev` stay light. Default run cost **$0 — does not trip the $1 flag.**
- **Quality opt-in: hosted Replicate FLUX** (`TRAINER_PROVIDER=replicate`, `GENERATOR_PROVIDER=replicate`). Real Replicate calls — FLUX LoRA training + generation — written **for real (not a stub)**, **verified offline** (no key/spend during scaffolding). One full hosted run ≈ **$2–4 train + ~$1 generate ≈ $3–5 → exceeds $1**, so it is **documented + flagged**, gated, and **never the default**. Env var **`REPLICATE_API_TOKEN`**.
- Why these two: a *custom-likeness* LoRA can't be produced by Anthropic/OpenAI image endpoints, so the real high-quality path is FLUX-on-Replicate and the key-free real path is local `diffusers`. Both are genuinely real — neither simulates.

**Peripheral (the < $1 budget applies): Anthropic Claude — optional selfie auto-captioning.** Model **`claude-haiku-4-5`** (cheapest vision tier); ~10–20 small vision calls ≈ **< $0.10 ✓**; env **`ANTHROPIC_API_KEY`**; **templated caption fallback when unset** (default needs no key). Improves training conditioning; it is *not* the core capability, so the budget rule rightly applies here.

Keys are separate from `B2_*`, placeholders only in `.env.example`, documented where to obtain, never committed.

---

## 5. Doc transforms

**Rewrite**
- `README.md` — product README (headshot framing, what-it-looks-like, quick start, simulated-default note, privacy note, feature list, UTM tag). Drop "Use this template" template framing.
- `ARCHITECTURE.md` — new components (studio/gallery, trainer/generator/captioner adapters), data flows (train job, generate job, purge), `subjects/` key layout, the batch-delete trust-boundary note.
- `AGENTS.md` — keep §2 "Building on This Starter Kit" contract intact; update repo map, add invariants: `replicate`/`diffusers`/`anthropic` SDKs lazy-imported and contained in `repo/` only; generation/training run via BackgroundTasks + manifest.
- `docs/features/dashboard.md` — headshot metrics.
- `docs/app-workflows.md`, `docs/dev-workflows.md`, `docs/SECURITY.md` — rename refs + add a **face-data handling** subsection to SECURITY (presigned-only, purge, no public objects).

**Keep (light touch / rename only)**
- `docs/features/file-upload.md`, `file-browser.md`, `metadata-extraction.md` — still accurate; rename refs only.
- `docs/design-system.md`, `docs/RELIABILITY.md`, `docs/features/_template.md` — keep.

**New stubs** (from §4): `subject-training.md`, `style-packs.md`, `headshot-generation.md`, `headshot-gallery.md`, `privacy-lifecycle.md`.

**exec-plans**: on finalize, this plan moves to `docs/exec-plans/completed/initial-scaffold.md`.

---

## 6. Rename table (`vibe-coding-starter-kit` → `ai-headshot-studio`)

| Kind | From | To | Where |
|---|---|---|---|
| kebab pkg name | `vibe-coding-starter-kit` | `ai-headshot-studio` | root `package.json`, `pnpm-workspace.yaml` |
| npm scope (web) | `@vibe-coding-starter-kit/web` | `@ai-headshot-studio/web` | `apps/web/package.json`, root scripts, `next.config.ts`, component/lib imports |
| npm scope (shared) | `@vibe-coding-starter-kit/shared` | `@ai-headshot-studio/shared` | `packages/shared/package.json`, importers |
| Title Case | `Vibe Coding Starter Kit` | `AI Headshot Studio` | `README.md`, page titles, sidebar brand |
| user_agent_extra | `b2ai-oss-start` | `b2ai-ai-headshot-studio` | `services/api/app/repo/b2_client.py`, `scripts/doctor.mjs` |
| UTM content tag | `utm_content=b2ai-oss-start` | `utm_content=b2ai-ai-headshot-studio` | `README.md`, `app-sidebar.tsx` |
| env var (deviation fix) | `B2_KEY_ID` (no `B2_REGION`) | **`B2_APPLICATION_KEY_ID`** + add **`B2_REGION`** | `.env.example`, `config/settings.py`, `doctor.mjs`, README, b2_client |

> **Env-var standardization (parent CLAUDE.md Standard #3):** the starter ships `B2_KEY_ID`
> and **no** `B2_REGION`. The new sample MUST use the five standard names:
> `B2_APPLICATION_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET_NAME`, `B2_REGION`, `B2_ENDPOINT`.

Files touched for kebab/scope renames (from grep): `apps/web/{next.config.ts,package.json}`,
`apps/web/src/components/files/{file-browser,file-metadata-panel,file-preview}.tsx`,
`components/layout/command-palette.tsx`, `components/upload/upload-progress.tsx`,
`lib/{api-client,file-tree,queries}.ts`, `docs/{dev-workflows,SECURITY}.md`,
root + `packages/shared` `package.json`, `README.md`.
`b2ai-oss-start` in: `app-sidebar.tsx`, `README.md`, `scripts/doctor.mjs`, `repo/b2_client.py`.

---

## Open questions resolved (from the concept brief)
- **Train locally or via provider?** → **Real local training by default** (`diffusers`+`peft`, $0, no keys); **hosted Replicate FLUX** as a real opt-in for quality, flagged >$1. **Never simulated.**
- **Privacy / face-data lifecycle?** → First-class **Delete-subject purge** (batch delete of the whole `subjects/{id}/` prefix), presigned-only access, no public objects, documented in `SECURITY.md` + `privacy-lifecycle.md`.

## Dependencies & verification
- **New backend deps** (the one sanctioned deviation from "lean"): `torch`, `diffusers`, `transformers`, `peft`, `accelerate`, plus optional `anthropic`. All ML deps are **lazy-imported inside the `local` adapters only** and contained in `repo/` — the AGENTS.md SDK-containment invariant extends to them (no `torch`/`diffusers`/`anthropic` outside `repo/`).
- **Verification = a tiny REAL local run (not simulated):** the builder proves the end-to-end loop with a minimal *real* train+generate — a tiny test SD pipeline (e.g. `hf-internal-testing/tiny-stable-diffusion-pipe`), 1–2 selfies at low res, 1–2 train steps, 1–2 generated images — confirming a **real `.safetensors` and real PNG headshots land under `subjects/{id}/` on B2**. Fast, $0, no GPU, no large downloads. The full SD-1.5 default path and the hosted FLUX path are additionally verified for lint/types/structure/wiring offline. This satisfies the corrected builder rule (core wired with real calls + real B2 artifacts) and the user's choice of local-real verification.

## Build size guardrails
Lean everywhere except the sanctioned ML stack above: keep additions tight, files < 300
lines, reuse starter primitives. The energy goes into **real** generation + style packs +
gallery + privacy, which are the real delta. Do NOT read or copy from `lora-training-studio`.
