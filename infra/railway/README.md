# Railway Deployment

Deploy both services (web + api) on Railway.

## Setup

1. Create a new Railway project
2. Add two services from the same repo:

### Web Service (Next.js)
- **Root Directory**: `apps/web`
- **Build Command**: `pnpm install && pnpm build`
- **Start Command**: `pnpm start`
- **Port**: `3000`

### API Service (FastAPI)
- **Root Directory**: `services/api`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Environment Variables

Set these on the API service:

| Variable | Value |
|----------|-------|
| `B2_ENDPOINT` | Your B2 S3 endpoint |
| `B2_REGION` | Your B2 region (e.g. `us-west-004`) |
| `B2_APPLICATION_KEY_ID` | Your B2 application key ID |
| `B2_APPLICATION_KEY` | Your B2 application key |
| `B2_BUCKET_NAME` | Your bucket name |
| `API_CORS_ORIGINS` | Your web service URL (e.g., `https://web-production-xxx.up.railway.app`) |
| `TRAINER_PROVIDER` / `GENERATOR_PROVIDER` | `local` (default) or `replicate` |
| `REPLICATE_API_TOKEN` | Required only if using the hosted FLUX engine |
| `ANTHROPIC_API_KEY` | Optional — enables Claude selfie captioning |

> The default `local` engine runs real SD-1.5 training/generation on the API
> service. That is heavy (GPU strongly recommended) and downloads model
> weights at first use. For lightweight hosting, set the providers to
> `replicate` and supply `REPLICATE_API_TOKEN`.

Set this on the Web service:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Your API service URL (e.g., `https://api-production-xxx.up.railway.app`) |
