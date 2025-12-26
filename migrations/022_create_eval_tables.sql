-- Migration 022: Create evaluation experiment tables
-- This migration creates tables for the eval feature to support LLM response
-- comparison and evaluation experiments with blind testing.

-- Table: experiments
-- Stores evaluation experiments comparing two sets of answers (x vs y)
CREATE TABLE IF NOT EXISTS experiments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description_x TEXT,
    description_y TEXT,
    model_x VARCHAR(100),
    model_y VARCHAR(100),
    judge_model VARCHAR(100),
    eval_template_id INTEGER,  -- FK to templates table (nullable until T06)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_experiments_name ON experiments(name);
CREATE INDEX IF NOT EXISTS idx_experiments_eval_template_id ON experiments(eval_template_id);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_experiments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_experiments_updated_at
    BEFORE UPDATE ON experiments
    FOR EACH ROW
    EXECUTE FUNCTION update_experiments_updated_at();

-- Table: experiment_dimensions
-- Stores custom scoring dimensions for each experiment
CREATE TABLE IF NOT EXISTS experiment_dimensions (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    dimension_name VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT uq_experiment_dimension_name UNIQUE (experiment_id, dimension_name)
);

CREATE INDEX IF NOT EXISTS idx_experiment_dimensions_experiment_id ON experiment_dimensions(experiment_id);

-- Table: experiment_prompts
-- Stores test prompts for each experiment
CREATE TABLE IF NOT EXISTS experiment_prompts (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_experiment_prompts_experiment_id ON experiment_prompts(experiment_id);

-- Table: experiment_answers
-- Stores answer pairs with blind a/b assignment mapping
CREATE TABLE IF NOT EXISTS experiment_answers (
    id SERIAL PRIMARY KEY,
    prompt_id INTEGER NOT NULL REFERENCES experiment_prompts(id) ON DELETE CASCADE,
    answer_x TEXT NOT NULL,
    answer_y TEXT NOT NULL,
    is_x_mapped_to_a BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_experiment_answers_prompt_id ON experiment_answers(prompt_id);

-- Table: experiment_evaluations
-- Stores evaluation results with overall score and justification
CREATE TABLE IF NOT EXISTS experiment_evaluations (
    id SERIAL PRIMARY KEY,
    answer_id INTEGER NOT NULL REFERENCES experiment_answers(id) ON DELETE CASCADE,
    overall_score INTEGER NOT NULL CHECK (overall_score >= -10 AND overall_score <= 10),
    justification TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_experiment_evaluations_answer_id UNIQUE (answer_id)
);

CREATE INDEX IF NOT EXISTS idx_experiment_evaluations_answer_id ON experiment_evaluations(answer_id);

-- Table: experiment_dimension_results
-- Stores individual dimension scores for each evaluation
CREATE TABLE IF NOT EXISTS experiment_dimension_results (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES experiment_evaluations(id) ON DELETE CASCADE,
    dimension_name VARCHAR(100) NOT NULL,
    score INTEGER NOT NULL CHECK (score >= -10 AND score <= 10)
);

CREATE INDEX IF NOT EXISTS idx_experiment_dimension_results_evaluation_id ON experiment_dimension_results(evaluation_id);

-- Add comments to tables and columns
COMMENT ON TABLE experiments IS 'Evaluation experiments for comparing LLM responses';
COMMENT ON COLUMN experiments.name IS 'Human-readable experiment name';
COMMENT ON COLUMN experiments.description_x IS 'Description of answer set X';
COMMENT ON COLUMN experiments.description_y IS 'Description of answer set Y';
COMMENT ON COLUMN experiments.model_x IS 'Model name for answer set X';
COMMENT ON COLUMN experiments.model_y IS 'Model name for answer set Y';
COMMENT ON COLUMN experiments.judge_model IS 'Model name used as evaluation judge';
COMMENT ON COLUMN experiments.eval_template_id IS 'Foreign key to prompt template for evaluation';

COMMENT ON TABLE experiment_dimensions IS 'Custom scoring dimensions for experiments';
COMMENT ON COLUMN experiment_dimensions.dimension_name IS 'Name of scoring dimension (e.g., factual_correctness)';
COMMENT ON COLUMN experiment_dimensions.display_order IS 'Order for displaying dimension';

COMMENT ON TABLE experiment_prompts IS 'Test prompts for evaluation experiments';
COMMENT ON COLUMN experiment_prompts.prompt_text IS 'The actual prompt/question text';

COMMENT ON TABLE experiment_answers IS 'Answer pairs with blind a/b assignment';
COMMENT ON COLUMN experiment_answers.answer_x IS 'First answer (from model X)';
COMMENT ON COLUMN experiment_answers.answer_y IS 'Second answer (from model Y)';
COMMENT ON COLUMN experiment_answers.is_x_mapped_to_a IS 'Random mapping: true=x->a, false=x->b';

COMMENT ON TABLE experiment_evaluations IS 'Evaluation results for answer pairs';
COMMENT ON COLUMN experiment_evaluations.overall_score IS 'Overall comparison score (-10 to +10)';
COMMENT ON COLUMN experiment_evaluations.justification IS 'Text explanation of evaluation';

COMMENT ON TABLE experiment_dimension_results IS 'Individual dimension scores for evaluations';
COMMENT ON COLUMN experiment_dimension_results.dimension_name IS 'Dimension being scored (denormalized)';
COMMENT ON COLUMN experiment_dimension_results.score IS 'Score for this dimension (-10 to +10)';
