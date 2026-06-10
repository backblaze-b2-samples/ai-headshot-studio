<!-- last_verified: 2026-06-09 -->
# Feature: Headshot Generation

## Purpose
Render real professional headshots from a subject's trained likeness LoRA
across the selected style packs — every image is a genuine model output.

## Used By
- UI: `/studio` (step 4: pick style packs → generate)
- API: `POST /subjects/{id}/generate`, `GET /subjects/{id}/progress`
- Job: FastAPI `BackgroundTask` `service.generation.run_generation`

## Core Functions
- `services/api/app/service/generation.py` — `start_generation`, `run_generation`
- `services/api/app/repo/generator/local.py` — REAL diffusers generation (default)
- `services/api/app/repo/generator/replicate.py` — REAL hosted FLUX (opt-in)
- `services/api/app/service/styles.py` — `build_prompt`

## Canonical Files
- Real generator: `services/api/app/repo/generator/local.py`
- Orchestration: `services/api/app/service/generation.py`

## Inputs
- `style_slugs: string[]` (UI)
- `HEADSHOTS_PER_STYLE` (default 6 → ~30 across the five packs; raise toward "hundreds")
- `GENERATOR_PROVIDER` (`local` default | `replicate`), `GENERATE_STEPS` (default 30), `GENERATE_GUIDANCE` (default 7.0), `GENERATE_LORA_SCALE` (default 0.8 — how strongly the likeness LoRA is applied at inference)

## Outputs
- Real PNGs at `subjects/{id}/headshots/{style_slug}/{NN}.png`
- Manifest updates: `status`, `headshots_done/total`, appended `HeadshotRef`s

## Flow
- `POST /generate` validates the subject is `trained`/`complete` and has a `lora_key`
- Status flips to `generating`; the BackgroundTask runs
- The pipeline uses the DPM++ 2M Karras sampler and applies the LoRA at
  `GENERATE_LORA_SCALE` for sharper, more faithful faces
- For each style pack: build the prompt, render `HEADSHOTS_PER_STYLE` images from
  the loaded LoRA, write each PNG to B2, append to the manifest, bump progress
- Status flips to `complete`; the UI tracks progress live off the subject manifest

## Edge Cases
- Subject not trained / no `lora_key` → 409
- No valid style slug → 400
- LoRA missing on B2 at load time → job fails with manifest error
- Re-generating a style continues numbering after existing images (no overwrite)

## UX States
- Loading: progress bar `headshots_done/total`
- Done: "View gallery" link enabled; images visible in `/gallery/[subjectId]`

## Verification
- Test files: `services/api/tests/test_subjects_api.py` (generate-requires-trained-model guard)
- Real-loop check: tiny SD test pipeline renders 2 valid PNG headshots under `headshots/`
- Quick verify: `pnpm test:api`
- Full verify: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: tests green; generated objects are valid PNGs in B2

## Related Docs
- [Headshot Gallery](headshot-gallery.md)
- [Style Packs](style-packs.md)
- [Subject Training](subject-training.md)
