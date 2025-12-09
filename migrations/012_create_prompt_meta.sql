-- Migration 012: Create prompt_meta table for prompt template metadata
-- This table stores metadata about prompt template variables (one record per function_tag)

CREATE TABLE IF NOT EXISTS prompt_meta (
    id SERIAL PRIMARY KEY,
    function_tag VARCHAR(100) UNIQUE NOT NULL,
    variables JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on function_tag for efficient lookups
CREATE INDEX IF NOT EXISTS idx_prompt_meta_function_tag ON prompt_meta(function_tag);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_prompt_meta_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_prompt_meta_updated_at
    BEFORE UPDATE ON prompt_meta
    FOR EACH ROW
    EXECUTE FUNCTION update_prompt_meta_updated_at();

-- Add comment to the table
COMMENT ON TABLE prompt_meta IS 'Metadata for prompt templates including variable descriptions';
COMMENT ON COLUMN prompt_meta.function_tag IS 'Unique identifier for the prompt function (links to prompt_templates.function_tag)';
COMMENT ON COLUMN prompt_meta.variables IS 'JSONB array of objects with variable_name and variable_description fields';


--Insert new prompt variables:
-- Query expansion
INSERT INTO prompt_meta (function_tag, variables) VALUES
('query_expansion', '[
{
"variable_name": "n",
"variable_description": "The number of alternative query reformulations the assistant must generate for multi-query expansion, controlling how many distinct search-style variants are produced."
},
{
"variable_name": "query",
"variable_description": "The original user query or information need, expressed in natural language, that the assistant will expand, answer hypothetically, classify by intent, and use to extract key entities."
}
]'::jsonb);

-- Heading hierarchy:
INSERT INTO prompt_meta (function_tag, variables) VALUES
('markdown_heading_hierarchy', '[
{
"variable_name": "title",
"variable_description": "The document title string used to identify the work whose headings and structure are being normalized."
},
{
"variable_name": "authors",
"variable_description": "The author or authors of the document, providing context that may help the model recognize the work and its typical structure."
},
{
"variable_name": "toc_text",
"variable_description": "The table of contents text from the database, including headings and their order, serving as the authoritative high level outline for aligning heading levels."
},
{
"variable_name": "titles_codeblock",
"variable_description": "The raw list of current document headings, each with its original line number and heading text, that must be relabeled with correct markdown levels or removal actions."
}
]'::jsonb);


-- RAG augmentation
INSERT INTO prompt_meta (function_tag, variables) VALUES
('rag_augmentation', '[
{
"variable_name": "intent",
"variable_description": "The high-level intent label for the user&apos;s question (e.g., DEFINITION, MECHANISM, COMPARISON) that guides how the answer should be structured and emphasized."
},
{
"variable_name": "entities_str",
"variable_description": "A string listing the key entities, theories, and constructs relevant to the question, used to focus the explanation on the most important concepts."
},
{
"variable_name": "context_blocks",
"variable_description": "The set of retrieved source passages, each labeled with [S#] and optional metadata, that serve as the primary evidence base for constructing the answer and citations."
},
{
"variable_name": "user_question",
"variable_description": "The original natural-language question posed by the user that the assistant must answer using the provided context and hybrid evidence policy."
}
]'::jsonb);

-- Vector suggestions
INSERT INTO prompt_meta (function_tag, variables) VALUES
('vectorization_suggestions', '[
{
"variable_name": "bib_section",
"variable_description": "Optional bibliographic or citation information for the document, providing context about the work whose headings are being evaluated for vectorization."
},
{
"variable_name": "titles_content",
"variable_description": "The raw markdown-style list of document headings, including line numbers and title text, that must be analyzed and labeled as SKIP or VECTORIZE."
}
]'::jsonb);

-- ToC extraction (manual prompt - no variables, static template)
INSERT INTO prompt_meta (function_tag, variables) VALUES
('toc_extraction', '[]'::jsonb);
