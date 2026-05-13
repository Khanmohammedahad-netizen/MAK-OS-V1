# MAK Lead Engine - GCP Edition

An autonomous, zero-cost B2B lead generation and outreach engine tailored for MAK Software Solutions.

## Architecture

The system is split into two main components:
1. **Pipeline (Backend):** A Python-based Cloud Run Job (`apps/job`) that runs daily via Cloud Scheduler. It scrapes leads from Overpass/Places, enriches via Companies House, audits websites, scores the leads, drafts emails using Gemini 1.5 Flash, and sends via Brevo.
2. **Dashboard (Frontend):** A Next.js 14 web app (`apps/dashboard`) that acts as a UI layer for managing leads, adjusting scores, and viewing outreach logs directly from Supabase.

## Zero-Cost Constraints
* **GCP Cloud Run Jobs:** Fits entirely within the 2M free requests / 360k GB-seconds tier.
* **Database:** Supabase Free Tier (500MB database).
* **AI Personalization:** Gemini 1.5 Flash Free Tier (1M tokens/day, 15 RPM).
* **Email Outreach:** Brevo Free Tier (300 emails/day, hard-capped at 30/day via config).
* **Frontend Hosting:** Vercel Free Tier.

---

## Setup Instructions

### 1. Database Setup (Supabase)
1. Create a new Supabase project.
2. Open the **SQL Editor** in Supabase.
3. Copy the contents of `infra/schema.sql` and run it to create all tables, indexes, and RLS policies.
4. Go to **Project Settings > API** and copy your `URL`, `anon key`, and `service_role key`.

### 2. Backend Setup (Cloud Run Job)
Ensure you have the Google Cloud CLI (`gcloud`) installed and authenticated.

1. **Set Environment Variables:**
   Create a `.env` file in the root based on `.env.example`.

2. **Provision Secrets:**
   Run the secret setup script. It uses your `.env` file to securely store keys in Google Cloud Secret Manager.
   ```bash
   ./infra/secrets-setup.sh
   ```

3. **Deploy the Job:**
   Build and deploy the Python app as a Cloud Run Job.
   ```bash
   ./infra/deploy-job.sh
   ```

4. **Schedule the Job:**
   Configure Cloud Scheduler to run the job daily at 9:00 AM IST.
   ```bash
   ./infra/deploy-scheduler.sh
   ```

### 3. Frontend Setup (Next.js Dashboard)
The dashboard uses Supabase SSR auth.

1. Navigate to the dashboard directory:
   ```bash
   cd apps/dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   Create `apps/dashboard/.env.local`:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

5. **Deployment:** Connect the `apps/dashboard` directory to Vercel. Supabase `anon` key is required in Vercel environment variables.

---

## Pipeline Logic Details
* **Scraping Strategy:** Uses Overpass API with highly specific bounding boxes to extract B2B data (e.g., accounting firms, agencies).
* **Deduplication:** Hash-based deterministic IDs using business name + city + domain prevent duplicate outreach across pipeline runs.
* **AI Fallback:** If Gemini hits a `429` Rate Limit, the system catches the error and silently falls back to a Jinja2 template defined in the codebase.
* **RLS Policies:** The dashboard (using `anon_key`) can only read data, preventing unauthorized public mutations. The backend pipeline (using `service_role`) bypasses RLS for full control.
