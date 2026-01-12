-- Migration 028: Add research tables for deep research feature
-- Description: Create research_sessions, research_sections, and research_reports tables
-- for managing manual and automated research workflows with JSONB state storage.
-- NOTE: This migration should be run as the application user to ensure proper ownership

-- ============================================================================
-- 1. Create research_sessions table
-- ============================================================================
CREATE TABLE IF NOT EXISTS research_sessions (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL,
    thread_id VARCHAR(255) UNIQUE NOT NULL,
    current_phase VARCHAR(50),
    research_plan JSONB,
    state_data JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_research_sessions_session_type CHECK (session_type IN ('manual', 'automated')),
    CONSTRAINT chk_research_sessions_status CHECK (status IN ('in_progress', 'completed', 'failed', 'paused'))
);

-- ============================================================================
-- 2. Create research_sections table
-- ============================================================================
CREATE TABLE IF NOT EXISTS research_sections (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    question_id VARCHAR(50),
    question_text TEXT,
    section_content TEXT,
    context_data JSONB,
    matching_results JSONB,
    metadata JSONB,
    reuse_info JSONB,
    quality_status VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_research_sections_quality_status CHECK (
        quality_status IS NULL OR quality_status IN ('pending', 'pass', 'fail', 'needs_review')
    )
);

-- ============================================================================
-- 3. Create research_reports table
-- ============================================================================
CREATE TABLE IF NOT EXISTS research_reports (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    report_content TEXT NOT NULL,
    executive_summary TEXT,
    quality_evaluation JSONB,
    metadata JSONB,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================================================
-- 4. Create indexes
-- ============================================================================
-- research_sessions indexes
CREATE INDEX IF NOT EXISTS idx_research_sessions_collection ON research_sessions(collection_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_thread ON research_sessions(thread_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status);

-- research_sections indexes
CREATE INDEX IF NOT EXISTS idx_research_sections_session ON research_sections(session_id);
CREATE INDEX IF NOT EXISTS idx_research_sections_question ON research_sections(question_id);
CREATE INDEX IF NOT EXISTS idx_research_sections_quality ON research_sections(quality_status);

-- research_reports indexes
CREATE INDEX IF NOT EXISTS idx_research_reports_session ON research_reports(session_id);

-- ============================================================================
-- 5. Create trigger functions for auto-updating timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION update_research_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_research_sections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. Create triggers
-- ============================================================================
DROP TRIGGER IF EXISTS trigger_update_research_sessions_updated_at ON research_sessions;
CREATE TRIGGER trigger_update_research_sessions_updated_at
    BEFORE UPDATE ON research_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_research_sessions_updated_at();

DROP TRIGGER IF EXISTS trigger_update_research_sections_updated_at ON research_sections;
CREATE TRIGGER trigger_update_research_sections_updated_at
    BEFORE UPDATE ON research_sections
    FOR EACH ROW
    EXECUTE FUNCTION update_research_sections_updated_at();

-- ============================================================================
-- 7. Verification queries
-- ============================================================================
SELECT 'research_sessions table created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'research_sessions'
);

SELECT 'research_sections table created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'research_sections'
);

SELECT 'research_reports table created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'research_reports'
);
