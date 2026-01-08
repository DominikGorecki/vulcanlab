-- Migration: 027_add_collections_tables.sql
-- Description: Create collections and collection_items tables for research organization

-- 1. Create collection_item_type enum
DO $$ BEGIN
    CREATE TYPE collection_item_type AS ENUM ('excerpt', 'research_result', 'research_query');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Create collections table
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Create collection_items table
CREATE TABLE IF NOT EXISTS collection_items (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    item_type collection_item_type NOT NULL,
    link VARCHAR(1000) NOT NULL,
    note TEXT,
    "order" NUMERIC(10, 3) NOT NULL DEFAULT 0,
    date_added TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 4. Create indexes
CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name);
CREATE INDEX IF NOT EXISTS idx_collections_tags ON collections USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_collections_created_at ON collections(created_at);

CREATE INDEX IF NOT EXISTS idx_collection_items_collection_id ON collection_items(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_items_item_type ON collection_items(item_type);
CREATE INDEX IF NOT EXISTS idx_collection_items_order ON collection_items("order");

-- 5. Create trigger functions for auto-updating timestamps
CREATE OR REPLACE FUNCTION update_collections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_collection_items_last_modified()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. Create triggers
DROP TRIGGER IF EXISTS trigger_update_collections_updated_at ON collections;
CREATE TRIGGER trigger_update_collections_updated_at
    BEFORE UPDATE ON collections
    FOR EACH ROW
    EXECUTE FUNCTION update_collections_updated_at();

DROP TRIGGER IF EXISTS trigger_update_collection_items_last_modified ON collection_items;
CREATE TRIGGER trigger_update_collection_items_last_modified
    BEFORE UPDATE ON collection_items
    FOR EACH ROW
    EXECUTE FUNCTION update_collection_items_last_modified();

-- 7. Grant privileges to app_user (loaded from config/init_db logic usually, 
-- but consistent with migrations that explicitly grant if needed)
-- Note: init_db handles ownership, but migrations sometimes include GRANTS
-- For consistency with 024_add_auto_eval_mode.sql and others, we leave it to the runner or init_db
-- unless explicit GRANTS are standard here. Checking 007_create_io_files_table.sql etc.
-- Actually, the pattern in init_db.py shows explicit ownership transfers.

