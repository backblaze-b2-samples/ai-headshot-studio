<!-- last_verified: 2026-06-09 -->
# Security

Security principles and implementation for AI Headshot Studio.

## Trust Boundaries

- **Frontend -> API**: CORS-restricted to configured origins, scoped to `GET/POST/DELETE/OPTIONS`
- **API -> B2**: Authenticated via `B2_APPLICATION_KEY_ID` + `B2_APPLICATION_KEY`, signature v4, custom user agent
- **Client -> B2**: Presigned URLs only (short expiry, `Content-Disposition: attachment`); no public objects
- **Purge**: `DELETE /subjects/{id}` batch-deletes the whole `subjects/{id}/` prefix; the id is validated as a 32-char hex UUID before it forms a prefix, so a purge can never escape one subject's namespace

## Upload Validation

- Filename sanitization: path traversal, null bytes, unsafe chars stripped
- MIME/extension consistency check against allowlist
- Chunked streaming with size enforcement (100MB default)
- Content-type allowlist (images, PDFs, text, archives, audio/video)
- Empty file rejection

## File Key Validation

- Empty keys rejected
- Path traversal patterns rejected (`../`, `%2e%2e`, backslashes, null bytes)
- The bucket is the only access boundary — add prefix scoping in
  `services/api/app/service/files.py::validate_key` if your deployment
  shares a bucket with other workloads

## Download Safety

- Presigned URLs force `Content-Disposition: attachment`
- Prevents inline rendering of user-uploaded content (XSS mitigation)

## Face-Data Handling

Selfies and generated headshots are biometric/face data and are treated as
first-class sensitive data:

- **Presigned-only access.** No B2 object is public. Gallery previews and
  downloads use short-lived presigned URLs (forced attachment). The bucket
  CORS / public settings must not be loosened for this app.
- **Right-to-be-forgotten.** Every subject ships with a real *Delete subject*
  purge (`DELETE /subjects/{id}` → `repo.b2_client.delete_prefix`) that removes
  every object under `subjects/{id}/` — selfies, captions, the trained LoRA,
  and all headshots — via batch `DeleteObjects`. See
  [docs/features/privacy-lifecycle.md](features/privacy-lifecycle.md).
- **Bounded scope.** Subject ids are server-assigned UUIDs validated as 32-char
  hex; all keys derive from them, so user input never forms a B2 prefix.
- **Sole store.** B2 is the only data store — there is no shadow database that
  could retain face data after a purge.
- **External engines.** When `replicate` is enabled, selfies/LoRA are sent to a
  third party (Replicate). The default `local` engine keeps all processing on
  your own machine. Captioning with Anthropic sends selfies to Claude only when
  `ANTHROPIC_API_KEY` is set; the default templated caption sends nothing.

## Secrets Management

- All secrets loaded via environment variables (pydantic-settings)
- Never committed to source control
- `.env.example` documents required variables without values

## Agent Security Rules

- Never commit `.env`, credentials, or API keys
- Never weaken validation without explicit instruction
- Never bypass CORS, auth, or input sanitization
- Always validate at system boundaries
