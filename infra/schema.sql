-- ============================================================
-- MAK Lead Engine — Supabase Postgres Schema
-- Run this in the Supabase SQL Editor (or psql).
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ──────────────────────────────────────────────
-- 1. leads
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source          TEXT NOT NULL,
    source_id       TEXT,
    business_name   TEXT NOT NULL,
    website         TEXT,
    email           TEXT,
    phone           TEXT,
    city            TEXT,
    region          TEXT,
    country         TEXT,
    category        TEXT,
    address         TEXT,
    socials         JSONB DEFAULT '{}',
    dedupe_key      TEXT UNIQUE NOT NULL,
    raw_payload     JSONB DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'new'
                    CHECK (status IN (
                        'new','enriched','audited','scored',
                        'queued','sent','replied','blacklisted','skipped'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_dedupe_key ON leads (dedupe_key);
CREATE INDEX IF NOT EXISTS idx_leads_status     ON leads (status);
CREATE INDEX IF NOT EXISTS idx_leads_country    ON leads (country);

-- ──────────────────────────────────────────────
-- 2. enrichment_companies_house
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS enrichment_companies_house (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id             UUID NOT NULL UNIQUE REFERENCES leads(id) ON DELETE CASCADE,
    company_number      TEXT,
    company_status      TEXT,
    incorporation_date  DATE,
    sic_codes           TEXT[],
    officers_summary    JSONB DEFAULT '{}',
    match_confidence    NUMERIC,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- 3. audits
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audits (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id             UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    reachable           BOOLEAN,
    https               BOOLEAN,
    has_title           BOOLEAN,
    has_meta_desc       BOOLEAN,
    has_viewport        BOOLEAN,
    has_contact_form    BOOLEAN,
    has_cta             BOOLEAN,
    has_booking         BOOLEAN,
    has_whatsapp        BOOLEAN,
    generic_email       BOOLEAN,
    weakness_summary    TEXT,
    audit_score         INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audits_lead_id ON audits (lead_id);

-- ──────────────────────────────────────────────
-- 4. scores
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    final_score     INTEGER NOT NULL DEFAULT 0,
    breakdown       JSONB DEFAULT '{}',
    reasons         TEXT[] DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scores_lead_id     ON scores (lead_id);
CREATE INDEX IF NOT EXISTS idx_scores_final_score ON scores (final_score DESC);

-- ──────────────────────────────────────────────
-- 5. drafts
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS drafts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    subject         TEXT NOT NULL,
    body            TEXT NOT NULL,
    generator       TEXT NOT NULL CHECK (generator IN ('gemini', 'template')),
    approved        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drafts_lead_id ON drafts (lead_id);

-- ──────────────────────────────────────────────
-- 6. outreach_logs
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS outreach_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id             UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    subject             TEXT NOT NULL,
    body                TEXT NOT NULL,
    brevo_message_id    TEXT,
    status              TEXT NOT NULL DEFAULT 'queued'
                        CHECK (status IN ('queued','sent','failed','bounced','opened','replied')),
    sent_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_logs_lead_id ON outreach_logs (lead_id);

-- ──────────────────────────────────────────────
-- 7. blacklist
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS blacklist (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE,
    domain          TEXT,
    reason          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- 8. pipeline_runs
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running'
                    CHECK (status IN ('running','completed','failed')),
    metrics         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- 9. config (dashboard-editable settings)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS config (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed default config
INSERT INTO config (key, value) VALUES
    ('target_niche',    'restaurant'),
    ('target_country',  'GB'),
    ('target_city',     'London'),
    ('target_bbox',     '51.28,-0.49,51.69,0.24'),
    ('lead_scrape_cap', '50'),
    ('email_daily_cap', '30'),
    ('auto_approve',    'true'),
    ('dry_run',         'false'),
    ('score_threshold', '40')
ON CONFLICT (key) DO NOTHING;

-- ============================================================
-- Row Level Security
-- ============================================================

ALTER TABLE leads                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrichment_companies_house ENABLE ROW LEVEL SECURITY;
ALTER TABLE audits                   ENABLE ROW LEVEL SECURITY;
ALTER TABLE scores                   ENABLE ROW LEVEL SECURITY;
ALTER TABLE drafts                   ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_logs            ENABLE ROW LEVEL SECURITY;
ALTER TABLE blacklist                ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs            ENABLE ROW LEVEL SECURITY;
ALTER TABLE config                   ENABLE ROW LEVEL SECURITY;

-- Anon role: read-only on key tables
CREATE POLICY "anon_read_leads"          ON leads          FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_enrichment"     ON enrichment_companies_house FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_audits"         ON audits         FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_scores"         ON scores         FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_drafts"         ON drafts         FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_outreach_logs"  ON outreach_logs  FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_pipeline_runs"  ON pipeline_runs  FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_blacklist"      ON blacklist      FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_config"         ON config         FOR SELECT TO anon USING (true);

-- Authenticated role: full access (dashboard user = Ahad)
CREATE POLICY "auth_all_leads"          ON leads          FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_all_enrichment"     ON enrichment_companies_house FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_all_audits"         ON audits         FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_all_scores"         ON scores         FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_all_drafts"         ON drafts         FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_all_outreach_logs"  ON outreach_logs  FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_all_pipeline_runs"  ON pipeline_runs  FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_all_blacklist"      ON blacklist      FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_all_config"         ON config         FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Service role (Cloud Run Job) has full bypass via service_role key.
