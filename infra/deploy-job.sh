#!/usr/bin/env bash
# ──────────────────────────────────────────────────────
# MAK Lead Engine — Cloud Run Job Deployment
# Builds Docker image via Cloud Build, pushes to
# Artifact Registry, and deploys as a Cloud Run Job.
# ──────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-mak-lead-engine}"
REGION="${GCP_REGION:-asia-south1}"
REPO_NAME="mak-lead-engine"
IMAGE_NAME="lead-engine-job"
JOB_NAME="daily-lead-pipeline"

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"

echo "🏗️  Building and deploying MAK Lead Engine Job"
echo "   Project:  ${PROJECT_ID}"
echo "   Region:   ${REGION}"
echo "   Image:    ${IMAGE_URI}"
echo ""

# Step 1: Create Artifact Registry repo (idempotent)
echo "📦 Ensuring Artifact Registry repo exists..."
gcloud artifacts repositories describe "${REPO_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" &>/dev/null || \
gcloud artifacts repositories create "${REPO_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --repository-format=docker \
    --description="MAK Lead Engine container images"
echo "   ✓ Artifact Registry ready"

# Step 2: Build with Cloud Build
echo "🐳 Building Docker image via Cloud Build..."
gcloud builds submit ./apps/job \
    --project="${PROJECT_ID}" \
    --tag="${IMAGE_URI}" \
    --timeout=600
echo "   ✓ Image built and pushed"

# Step 3: Deploy as Cloud Run Job
echo "🚀 Deploying Cloud Run Job..."
gcloud run jobs deploy "${JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE_URI}" \
    --memory="512Mi" \
    --cpu="1" \
    --max-retries=1 \
    --task-timeout="600s" \
    --set-secrets="SUPABASE_URL=SUPABASE_URL:latest" \
    --set-secrets="SUPABASE_SERVICE_ROLE_KEY=SUPABASE_SERVICE_ROLE_KEY:latest" \
    --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest" \
    --set-secrets="BREVO_API_KEY=BREVO_API_KEY:latest" \
    --set-secrets="COMPANIES_HOUSE_API_KEY=COMPANIES_HOUSE_API_KEY:latest" \
    --set-secrets="GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest" \
    --set-secrets="YELP_API_KEY=YELP_API_KEY:latest" \
    --set-env-vars="TARGET_NICHE=restaurant,TARGET_COUNTRY=GB,TARGET_CITY=London,TARGET_BBOX=51.28,-0.49,51.69,0.24,LEAD_SCRAPE_CAP=50,EMAIL_DAILY_CAP=30,AUTO_APPROVE=true,DRY_RUN=false,SCORE_THRESHOLD=40,BREVO_SENDER_EMAIL=ahad@maksoftware.co,BREVO_SENDER_NAME=Ahad Khan,LOG_LEVEL=INFO,LOG_FORMAT=json"
echo "   ✓ Cloud Run Job deployed"

echo ""
echo "✅ Deployment complete!"
echo "   To run manually:  gcloud run jobs execute ${JOB_NAME} --project=${PROJECT_ID} --region=${REGION}"
echo "   To view logs:     gcloud logging read 'resource.type=cloud_run_job' --project=${PROJECT_ID} --limit=50"
