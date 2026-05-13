# Infrastructure — MAK Lead Engine

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | Full Supabase Postgres schema — run in SQL Editor |
| `secrets-setup.sh` | Bootstrap GCP Secret Manager with all API keys |
| `deploy-job.sh` | Build + deploy Cloud Run Job via Cloud Build |
| `deploy-scheduler.sh` | Create daily Cloud Scheduler trigger (09:00 IST) |

## Deployment Order

```bash
# 1. Set your GCP project
export GCP_PROJECT_ID=mak-lead-engine
export GCP_REGION=asia-south1

# 2. Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    --project=$GCP_PROJECT_ID

# 3. Create secrets
bash infra/secrets-setup.sh

# 4. Run Supabase schema
# → Copy infra/schema.sql into Supabase SQL Editor and execute

# 5. Deploy the Cloud Run Job
bash infra/deploy-job.sh

# 6. Set up daily scheduler
bash infra/deploy-scheduler.sh
```

## Cost: $0/month

All services used are within free tiers. The GCP $300 credit serves as a runway buffer only.
