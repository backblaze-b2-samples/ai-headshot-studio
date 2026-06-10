<!-- last_verified: 2026-06-09 -->
# Feature: Subject Training

## Purpose
Turn a person's uploaded selfies into a trained likeness LoRA so headshots can
be generated in their image — really fine-tuned, never simulated.

## Used By
- UI: `/studio` (steps 1–3: name → upload selfies → caption & train)
- API: `POST /subjects`, `POST /subjects/{id}/selfies`, `POST /subjects/{id}/caption`, `POST /subjects/{id}/train`, `GET /subjects/{id}/progress`
- Job: FastAPI `BackgroundTask` `service.training.run_training`

## Core Functions
- `services/api/app/service/subjects.py` — `create_subject`, `get_subject`
- `services/api/app/service/captioning.py` — `add_selfie`, `caption_subject`
- `services/api/app/service/training.py` — `start_training`, `run_training`
- `services/api/app/repo/trainer/local.py` — REAL SD-1.5 LoRA fine-tune (default)
- `services/api/app/repo/trainer/replicate.py` — REAL hosted FLUX-LoRA (opt-in)
- `services/api/app/repo/captioner.py` — Claude vision captioner / templated fallback
- `apps/web/src/components/studio/studio-flow.tsx`, `selfie-step.tsx`

## Canonical Files
- Real trainer: `services/api/app/repo/trainer/local.py`
- Orchestration: `services/api/app/service/training.py`

## Inputs
- Subject name: string (UI)
- 4–20 selfies: JPEG/PNG/WebP (multipart)
- Engine: `TRAINER_PROVIDER` (`local` default | `replicate`)
- Hyperparameters: `TRAIN_RESOLUTION`, `TRAIN_LORA_RANK` (default 16), `TRAIN_LEARNING_RATE`
- Step budget: scales with selfie count — `TRAIN_STEPS_PER_IMAGE` (default 100) × selfies, clamped to `[TRAIN_STEPS_MIN, TRAIN_STEPS_MAX]` (defaults 600–1200). Set `TRAIN_STEPS` > 0 to pin an explicit budget (e.g. `TRAIN_STEPS=40` for a fast smoke test); `0` (default) = auto. Resolved by `service.training.effective_train_steps`.

## Outputs
- A real `.safetensors` LoRA at `subjects/{id}/model/{id}.safetensors`
- Captions at `subjects/{id}/captions/{image_id}.txt`
- Manifest updates: `status`, `train_steps_done/total`, `lora_key`

## Flow
- Create subject → manifest written; selfies uploaded under the subject prefix
- Auto-caption (Claude if `ANTHROPIC_API_KEY` set, else template); the Studio
  shows each selfie next to its caption so the user can sanity-check it
- `POST /train` flips status to `training` and schedules the BackgroundTask
- The trainer center-crops each selfie to a square (no aspect distortion),
  encodes to latents, injects rank-16 LoRA layers on the UNet, and runs a real
  diffusion training loop on a cosine LR schedule (5% warmup), writing the LoRA to B2
- Progress callback writes whole-percent updates into the manifest; the UI polls
  the subject manifest live and unblocks "Generate" when status reaches `trained`

## Edge Cases
- Fewer than `MIN_SELFIES` (default 4) → 400, training refused
- Job already running → 409
- Undecodable selfie → skipped; if none usable → job fails with manifest error
- `replicate` engine without `REPLICATE_API_TOKEN` → adapter raises on construction

## UX States
- Loading: progress bar with `train_steps_done/total`
- Error: manifest `error` surfaced inline
- Done: status `trained`, "Generate" enabled

## Verification
- Test files: `services/api/tests/test_subjects_api.py`, `test_subjects_store.py`, `test_training.py` (step-budget scaling/clamping/override)
- Real-loop check: a tiny SD test pipeline (`hf-internal-testing/tiny-stable-diffusion-pipe`),
  2 selfies, 2 steps — confirms a real `.safetensors` lands under `subjects/{id}/model/`
- Quick verify: `pnpm test:api`
- Full verify: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: tests green; a parseable `.safetensors` with LoRA tensors is produced

## Related Docs
- [Headshot Generation](headshot-generation.md)
- [Style Packs](style-packs.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
