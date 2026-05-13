#!/usr/bin/env bash
# ──────────────────────────────────────────────────────
# MAK Lead Engine — GCP Secret Manager Bootstrap
# Creates secret entries for all required API keys.
# Run once during initial setup.
# ──────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-mak-lead-engine}"

echo "🔐 Creating secrets in project: ${PROJECT_ID}"
echo "   You will be prompted to enter each secret value."
echo ""

SECRETS=(
    "SUPABASE_URL"
    "SUPABASE_SERVICE_ROLE_KEY"
    "GEMINI_API_KEY"
    "BREVO_API_KEY"
    "COMPANIES_HOUSE_API_KEY"
    "GOOGLE_MAPS_API_KEY"
    "YELP_API_KEY"
)

for SECRET_NAME in "${SECRETS[@]}"; do
    # Create the secret (idempotent — ignores if exists)
    if gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
        echo "✓ Secret ${SECRET_NAME} already exists"
    else
        gcloud secrets create "${SECRET_NAME}" \
            --project="${PROJECT_ID}" \
            --replication-policy="automatic"
        echo "✓ Created secret: ${SECRET_NAME}"
    fi

    # Prompt for value and add a version
    echo -n "  Enter value for ${SECRET_NAME} (or press Enter to skip): "
    read -r SECRET_VALUE
    if [ -n "${SECRET_VALUE}" ]; then
        echo -n "${SECRET_VALUE}" | gcloud secrets versions add "${SECRET_NAME}" \
            --project="${PROJECT_ID}" \
            --data-file=-
        echo "  ✓ Added version for ${SECRET_NAME}"
    else
        echo "  ⏭ Skipped ${SECRET_NAME}"
    fi
done

echo ""
echo "✅ Secret Manager setup complete."
echo "   Total secrets: ${#SECRETS[@]}"
echo "   Free tier: 6 active secret versions (you have ${#SECRETS[@]})"
