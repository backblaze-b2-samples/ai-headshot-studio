<!-- last_verified: 2026-06-09 -->
# AI Headshot Studio

Turn 10–20 selfies into a gallery of professional headshots. Upload your
selfies → auto-caption them → fine-tune a likeness LoRA → generate dozens of
headshots across curated **style packs** (Corporate, LinkedIn, Creative,
Outdoor, Editorial B&W) → browse, download, and purge. **Every artifact in the
lifecycle lives on [Backblaze B2](https://www.backblaze.com/sign-up/ai-cloud-storage?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=b2ai-ai-headshot-studio)** — the
selfies, the captions, the trained model, and every generated image — so this
is a concrete demo of B2 as the storage layer for a real *train-then-generate-
at-scale* AI loop, plus a clean **face-data privacy lifecycle**.

**What you get out of the box:**
- A guided **Studio** flow: selfies → caption → train likeness → pick style packs → generate
- A scoped **Gallery** explorer: subjects → per-style headshot grids, with download
- **Style Packs** — a data-driven prompt registry, trivial to extend
- **Face-data privacy lifecycle** — one-click *Delete subject* batch-purges every B2 object under `subjects/{id}/`
- A headshot **Dashboard** — subjects, headshots generated, models trained, B2 storage by artifact type
- The reusable B2 scaffolding: full-bucket file browser, drag-and-drop upload, FastAPI layered backend, structural tests

## Real by default — never simulated

The core capability (train a likeness LoRA → generate headshots) is **genuinely
executed**, not faked.

- **Default engine: local real training & generation.** `diffusers` + `peft`
  fine-tune a LoRA on **Stable Diffusion 1.5** and render each headshot from it.
  **$0 API cost and no keys.** Tradeoffs: a heavier Python ML stack (`torch`,
  `diffusers`, `transformers`, `peft`, `accelerate`) and SD-class quality
  (modest, but real). Usable speed wants a GPU/MPS; it runs (slowly) on CPU.
  The heavy stack is **lazy-imported inside the local adapters only**, so the
  rest of the app and `pnpm dev` stay light.
- **Quality opt-in: hosted FLUX on Replicate.** Set
  `TRAINER_PROVIDER=replicate` / `GENERATOR_PROVIDER=replicate` and a
  `REPLICATE_API_TOKEN` for a real FLUX-LoRA train + generate. One full hosted
  run is roughly **$3–5**, so it is gated and **never the default**.
- **Optional selfie auto-captioning** uses Anthropic Claude (`claude-haiku-4-5`,
  ~<$0.10/run); with no `ANTHROPIC_API_KEY` it falls back to a templated caption,
  so the default path needs no key.

## Privacy

Headshots are face data. Access is **presigned-only** (short-lived URLs, no
public objects), and every subject ships with a real **right-to-be-forgotten**
purge: *Delete subject* runs a batch `DeleteObjects` over the entire
`subjects/{id}/` prefix — selfies, captions, the trained LoRA, and all
headshots — in one sweep. See [docs/SECURITY.md](docs/SECURITY.md#face-data-handling)
and [docs/features/privacy-lifecycle.md](docs/features/privacy-lifecycle.md).

## Quick Start

You need: Node.js >= 20, pnpm >= 9, Python >= 3.11, and a free **[Backblaze B2 account](https://www.backblaze.com/sign-up/ai-cloud-storage?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=b2ai-ai-headshot-studio)**.

**1. Install frontend dependencies**

```bash
pnpm install
```

**2. Set up the backend**

```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../..
```

> The first `diffusers` run downloads the SD-1.5 weights (~4 GB) from Hugging
> Face and caches them locally. Training/generation use your GPU/MPS if
> available and fall back to CPU otherwise.

**3. Add your B2 credentials**

```bash
cp .env.example .env
```

Open `.env`, then head to the [Backblaze B2 dashboard](https://secure.backblaze.com/b2_buckets.htm?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=b2ai-ai-headshot-studio) and:

1. **Create a bucket.** Paste each value into `.env`:
   - **Bucket Unique Name** → `B2_BUCKET_NAME`
   - **Endpoint** → `B2_ENDPOINT` (e.g. `https://s3.us-west-004.backblazeb2.com`)
   - The region in that endpoint → `B2_REGION` (e.g. `us-west-004`)
2. **Create an application key** with `Read and Write` permission:
   - **keyID** → `B2_APPLICATION_KEY_ID`
   - **applicationKey** → `B2_APPLICATION_KEY` *(only shown once — paste it now)*

> Want a walkthrough? See the docs for [creating a bucket](https://www.backblaze.com/docs/cloud-storage-create-and-manage-buckets?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=b2ai-ai-headshot-studio) and [creating app keys](https://www.backblaze.com/docs/cloud-storage-create-and-manage-app-keys?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=b2ai-ai-headshot-studio).

**4. Run it**

```bash
pnpm dev
```

Frontend at `localhost:3000`, API at `localhost:8000`. Open **Studio**, name a
subject, upload selfies, train, and generate. `pnpm dev` runs `pnpm doctor`
first — a preflight that catches the common setup gotchas and tells you how to
fix each one.

## How it works

The async pattern is **FastAPI `BackgroundTasks` + manifest polling**. Each
subject's `subject.json` on B2 is the single source of truth for status and
progress — there's no database and no in-memory job store. The frontend polls a
`/progress` endpoint (every 1.5s while a job runs) and re-renders. B2 object
layout:

```
subjects/{subject_id}/
  subject.json                       # manifest: status, config, captions, metrics, artifact keys
  selfies/{image_id}.{ext}           # uploaded training selfies
  captions/{image_id}.txt            # one caption per selfie
  model/{subject_id}.safetensors     # trained likeness LoRA
  headshots/{style_slug}/{NN}.png    # generated headshots, grouped by style pack
```

All storage goes through the S3-compatible API (`boto3`, signature v4, custom
user agent) — **no b2-native calls**. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Core Features

- [Subject Training](docs/features/subject-training.md) — upload selfies, auto-caption, fine-tune a likeness LoRA
- [Style Packs](docs/features/style-packs.md) — curated, data-driven prompt sets
- [Headshot Generation](docs/features/headshot-generation.md) — render the LoRA across selected packs to fill a gallery
- [Headshot Gallery](docs/features/headshot-gallery.md) — scoped subject → style explorer with preview/download
- [Privacy Lifecycle](docs/features/privacy-lifecycle.md) — one-click batch purge of all face data
- [Dashboard](docs/features/dashboard.md) — headshot metrics + storage breakdown
- [File Upload](docs/features/file-upload.md) / [File Browser](docs/features/file-browser.md) / [Metadata Extraction](docs/features/metadata-extraction.md) — the reusable B2 scaffolding
- [Design System](docs/design-system.md) — tokens, primitives, loader, error/empty states. Live at `/design`.

## Tech Stack

- TypeScript, Next.js 16, React 19, Tailwind v4, shadcn/ui, Recharts
- TanStack Query — caching, dedup, retry, polling for every fetch
- Python 3.11+, FastAPI, boto3, Pydantic v2, Pillow
- ML (local engine): `torch`, `diffusers`, `transformers`, `peft`, `accelerate` (lazy-imported in `repo/` adapters)
- Optional: `replicate` (hosted FLUX), `anthropic` (captioning)
- Backblaze B2 (S3-compatible object storage)
- pnpm workspaces (monorepo)

## Commands

| Command | What it does |
|---------|-------------|
| `pnpm dev` | Start frontend + backend |
| `pnpm dev:web` | Frontend only |
| `pnpm dev:api` | Backend only |
| `pnpm build` | Build frontend |
| `pnpm lint` | Lint frontend |
| `pnpm lint:api` | Lint backend (ruff) |
| `pnpm test:api` | Run backend tests |
| `pnpm check:structure` | Verify layering rules |
| `pnpm test:e2e` | Playwright e2e tests (run `pnpm --filter @ai-headshot-studio/web exec playwright install chromium` once first) |

## Documentation Map

| Doc | Purpose |
|-----|---------|
| [AGENTS.md](AGENTS.md) | Agent table of contents — start here |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System layout, layering, data flows |
| [docs/features/](docs/features/) | Feature docs |
| [docs/design-system.md](docs/design-system.md) | Design tokens, primitives, loader, error/empty states |
| [docs/app-workflows.md](docs/app-workflows.md) | User journeys |
| [docs/dev-workflows.md](docs/dev-workflows.md) | Engineering workflows and testing |
| [docs/SECURITY.md](docs/SECURITY.md) | Security principles + face-data handling |
| [docs/RELIABILITY.md](docs/RELIABILITY.md) | Reliability expectations |
| [docs/exec-plans/](docs/exec-plans/) | Execution plans and tech debt tracker |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Claude Agent B2 Skill

Manage Backblaze B2 from your terminal using natural language (list/search, audits, stale or large file detection, security checks, safe cleanup).

Repo: [https://github.com/backblaze-b2-samples/claude-skill-b2-cloud-storage](https://github.com/backblaze-b2-samples/claude-skill-b2-cloud-storage)
