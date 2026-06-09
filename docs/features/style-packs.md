<!-- last_verified: 2026-06-09 -->
# Feature: Style Packs

## Purpose
Provide curated headshot looks (prompt scaffolding) so a single trained
likeness can be rendered as Corporate, LinkedIn, Creative, Outdoor, or
Editorial B&W — and make adding a new look a one-line change.

## Used By
- UI: `/studio` style picker; `/gallery/[subjectId]` style sections
- API: `GET /styles`

## Core Functions
- `services/api/app/service/styles.py` — `list_style_packs`, `get_style_pack`, `valid_slugs`, `build_prompt`
- `services/api/app/types/style.py` — `StylePack` model
- `apps/web/src/components/studio/style-picker.tsx`
- `apps/web/src/components/gallery/style-section.tsx`

## Canonical Files
- Registry: `services/api/app/service/styles.py`

## Inputs
- A style slug + the subject's `trigger_token` (server-side, at generation time)

## Outputs
- `GET /styles` → `StylePack[]` (slug, label, description, prompt_template, negative_prompt)
- `build_prompt(slug, trigger_token)` → a fully expanded prompt

## Flow
- Each pack's `prompt_template` carries a `{subject}` placeholder
- At generation time `build_prompt` substitutes the subject's trigger token
- `valid_slugs` filters user-selected slugs to the known registry (drops unknowns/dupes)

## Edge Cases
- Unknown slug requested → silently dropped by `valid_slugs`; if all dropped → 400
- Adding a pack: append one `StylePack` to `_STYLE_PACKS` — it appears in the
  picker and gallery automatically (data-driven; no other code change)

## Verification
- Test files: `services/api/tests/test_styles.py`
- Required cases: all built-ins present, every template has `{subject}`, prompt substitution, unknown/dupe filtering
- Quick verify: `pnpm test:api`
- Pass criteria: tests green; `GET /styles` lists all five built-in packs

## Related Docs
- [Headshot Generation](headshot-generation.md)
- [Subject Training](subject-training.md)
