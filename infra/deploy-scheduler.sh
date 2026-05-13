#!/usr/bin/env bash
# ──────────────────────────────────────────────────────
# MAK Lead Engine — Cloud Scheduler Setup
# Creates a daily trigger at 09:00 IST (03:30 UTC)
# that invokes the Cloud Run Job via OIDC-authenticated HTTP.
# ──────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-mak-lead-engine}"
REGION="${GCP_REGION:-asia-south1}"
JOB_NAME="daily-lead-pipeline"
SCHEDULER_NAME="daily-lead-trigger"
SCHEDULE="30 3 * * *"  # 03:30 UTC = 09:00 IST
TIMEZONE="Asia/Kolkata"

echo "⏰ Setting up Cloud Scheduler for MAK Lead Engine"
echo "   Project:   ${PROJECT_ID}"
echo "   Schedule:  ${SCHEDULE} (${TIMEZONE}) = 09:00 IST daily"
echo ""

# Get the Cloud Run Job URL
# Cloud Run Jobs are triggered via the jobs.run method, not a URL.
# We use gcloud scheduler jobs create http to hit the Cloud Run Admin API.

# Service account for scheduler
SA_EMAIL="scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account if not exists
echo "🔑 Ensuring service account exists..."
gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null || \
gcloud iam service-accounts create "scheduler-sa" \
    --project="${PROJECT_ID}" \
    --display-name="Cloud Scheduler SA for Lead Pipeline"

# Grant the SA permission to invoke Cloud Run Jobs
echo "🔓 Granting Cloud Run Invoker role..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.invoker" \
    --condition=None \
    --quiet

# The Cloud Run Jobs execution endpoint
RUN_URL="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

# Create or update the scheduler job
echo "📅 Creating Cloud Scheduler job..."
if gcloud scheduler jobs describe "${SCHEDULER_NAME}" --project="${PROJECT_ID}" --location="${REGION}" &>/dev/null; then
    gcloud scheduler jobs update http "${SCHEDULER_NAME}" \
        --project="${PROJECT_ID}" \
        --location="${REGION}" \
        --schedule="${SCHEDULE}" \
        --time-zone="${TIMEZONE}" \
        --uri="${RUN_URL}" \
        --http-method="POST" \
        --oauth-service-account-email="${SA_EMAIL}" \
        --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform"
    echo "   ✓ Scheduler job updated"
else
    gcloud scheduler jobs create http "${SCHEDULER_NAME}" \
        --project="${PROJECT_ID}" \
        --location="${REGION}" \
        --schedule="${SCHEDULE}" \
        --time-zone="${TIMEZONE}" \
        --uri="${RUN_URL}" \
        --http-method="POST" \
        --oauth-service-account-email="${SA_EMAIL}" \
        --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform"
    echo "   ✓ Scheduler job created"
fi

echo ""
echo "✅ Cloud Scheduler setup complete!"
echo "   Daily run: 09:00 IST (03:30 UTC)"
echo "   To trigger now: gcloud scheduler jobs run ${SCHEDULER_NAME} --project=${PROJECT_ID} --location=${REGION}"
echo "   To pause:       gcloud scheduler jobs pause ${SCHEDULER_NAME} --project=${PROJECT_ID} --location=${REGION}"
