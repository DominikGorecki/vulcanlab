# Eval Page Documentation

## Overview

The Eval page provides a blind evaluation system for comparing LLM responses. It allows users to create experiments, add test prompts, submit answer pairs from different models, and evaluate them using blind randomization. The system supports both manual evaluation (user judges) and automatic evaluation (LLM judges) with comprehensive statistical analysis.

### Pages

- **Experiment List**: `/eval` - List all evaluation experiments
- **New Experiment**: `/eval/new` - Create a new experiment
- **Experiment Detail**: `/eval/[id]` - View and manage experiment
- **Prompt Detail**: `/eval/[id]/prompts/[promptId]` - Manage answer pairs and evaluations for a specific prompt

### User Workflow

#### Creating an Experiment

1. Navigate to `/eval/new`
2. Configure experiment:
   - Name and description
   - Answer Set X: Description and model name
   - Answer Set Y: Description and model name
   - Judge model name
   - Select evaluation template
   - Review core evaluation dimensions (always included)
   - Add optional custom dimensions
3. Submit to create experiment

#### Adding Prompts

1. Navigate to experiment detail page
2. Scroll to "Prompts" section
3. Enter prompt text in textarea
4. Click "Add Prompt"
5. Repeat for all test prompts

#### Manual Evaluation Workflow

1. Navigate to prompt detail page
2. Click "Add Answers" button
3. Enter Answer X and Answer Y in dialog
4. Submit (answers are randomly assigned to A/B positions for blind evaluation)
5. Click "Copy Eval Prompt" to copy the evaluation prompt
6. Paste prompt into external LLM or evaluation system
7. Click "Paste Result" and submit LLM's evaluation
8. Repeat for additional answer pairs

#### Automatic Evaluation Workflow

1. Navigate to experiment detail page
2. Enable "Automatic Mode" toggle
3. Select providers (OpenAI or Gemini) for answer generation and judging
4. Navigate to prompt detail page
5. Click "New Eval" button
6. System automatically:
   - Generates Answer X using model X
   - Generates Answer Y using model Y
   - Submits both to judge model
   - Stores evaluation results
7. Review results in answer pairs table

#### Viewing Results

1. Navigate to experiment detail page
2. Review statistical analysis card:
   - Total evaluations
   - X Win Rate
   - Mean/Median scores
   - Tie Rate
   - Harm Rate
   - Wilcoxon test p-value
3. Export results:
   - Download CSV of evaluations
   - Download JSONL of answers

## API Calls

### GET `/api/v1/eval/experiments`

**Called By**: Experiment list page on mount

**Request**: No parameters

**Response**:
```json
{
  "experiments": [
    {
      "id": 1,
      "name": "GPT-4 vs Claude Comparison",
      "description_x": "GPT-4 Turbo responses",
      "description_y": "Claude 3 Opus responses",
      "created_at": "2024-12-09T10:00:00Z",
      "prompt_count": 25,
      "eval_count": 73
    }
  ]
}
```

**Purpose**: List all evaluation experiments with summary statistics.

### POST `/api/v1/eval/experiments`

**Called By**: New experiment page when user submits form

**Request**:
```json
{
  "name": "GPT-4 vs Claude Comparison",
  "description_x": "GPT-4 Turbo responses",
  "description_y": "Claude 3 Opus responses",
  "model_x": "gpt-4-turbo",
  "model_y": "claude-3-opus",
  "judge_model": "gpt-4",
  "eval_template_id": 5,
  "dimensions": [
    {
      "name": "factual_correctness",
      "description": "Accuracy of factual claims",
      "is_core": true
    },
    {
      "name": "creativity",
      "description": "Novel and creative responses",
      "is_core": false
    }
  ]
}
```

**Response**:
```json
{
  "experiment_id": 1,
  "message": "Experiment created successfully"
}
```

**Purpose**: Create a new evaluation experiment with configuration.

**Core Dimensions**: Always included automatically:
- `factual_correctness`
- `completeness`
- `coherence`
- `hallucination_risk`
- `academic_response`

### GET `/api/v1/eval/experiments/{id}`

**Called By**: Experiment detail page on mount

**Request**: Path parameter `id` (integer)

**Response**:
```json
{
  "id": 1,
  "name": "GPT-4 vs Claude Comparison",
  "description_x": "GPT-4 Turbo responses",
  "description_y": "Claude 3 Opus responses",
  "model_x": "gpt-4-turbo",
  "model_y": "claude-3-opus",
  "judge_model": "gpt-4",
  "eval_template_id": 5,
  "auto_mode_enabled": true,
  "auto_answer_provider": "openai",
  "auto_judge_provider": "openai",
  "created_at": "2024-12-09T10:00:00Z",
  "updated_at": "2024-12-09T15:30:00Z",
  "dimensions": [
    {
      "dimension_id": 1,
      "name": "factual_correctness",
      "description": "Accuracy of factual claims",
      "is_core": true
    }
  ],
  "stats": {
    "eval_count": 73,
    "x_win_rate": 0.52,
    "mean_score": 0.48,
    "median_score": 0.50,
    "tie_percentage": 0.12,
    "harm_rate": 0.03,
    "wilcoxon_p_value": 0.34
  }
}
```

**Purpose**: Retrieve experiment details with configuration, dimensions, and statistics.

### PATCH `/api/v1/eval/experiments/{id}`

**Called By**: Experiment detail page when toggling automatic mode or changing providers

**Request**:
```json
{
  "auto_mode_enabled": true,
  "auto_answer_provider": "gemini",
  "auto_judge_provider": "openai"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Experiment updated"
}
```

**Purpose**: Update experiment configuration (automatic mode settings).

**Providers**: `"openai"` or `"gemini"`

### DELETE `/api/v1/eval/experiments/{id}`

**Called By**: Experiment detail page when user confirms deletion

**Request**: Path parameter `id` (integer)

**Response**:
```json
{
  "success": true,
  "message": "Experiment and all related data deleted"
}
```

**Purpose**: Permanently delete experiment and all associated prompts, answers, and evaluations.

**Cascading**: Deletes all child records (prompts → answers → evaluations).

### GET `/api/v1/eval/experiments/{id}/prompts`

**Called By**: Experiment detail page to display prompts table

**Request**: Path parameter `id` (integer)

**Response**:
```json
{
  "prompts": [
    {
      "prompt_id": 10,
      "prompt_text": "Explain quantum entanglement to a 5-year-old.",
      "created_at": "2024-12-09T10:30:00Z",
      "answer_count": 5,
      "eval_count": 5
    }
  ]
}
```

**Purpose**: List all prompts for an experiment with evaluation counts.

### POST `/api/v1/eval/experiments/{id}/prompts`

**Called By**: Experiment detail page when user adds a new prompt

**Request**:
```json
{
  "prompt_text": "Explain quantum entanglement to a 5-year-old."
}
```

**Response**:
```json
{
  "prompt_id": 10,
  "message": "Prompt added successfully"
}
```

**Purpose**: Add a new test prompt to the experiment.

### DELETE `/api/v1/eval/prompts/{promptId}`

**Called By**: Experiment detail page or prompt detail page when deleting a prompt

**Request**: Path parameter `promptId` (integer)

**Response**:
```json
{
  "success": true,
  "message": "Prompt and all related data deleted"
}
```

**Purpose**: Delete a prompt and all associated answers and evaluations.

### GET `/api/v1/eval/prompts/{promptId}`

**Called By**: Prompt detail page on mount

**Request**: Path parameter `promptId` (integer)

**Response**:
```json
{
  "prompt_id": 10,
  "prompt_text": "Explain quantum entanglement to a 5-year-old.",
  "experiment_id": 1,
  "created_at": "2024-12-09T10:30:00Z"
}
```

**Purpose**: Retrieve prompt details.

### GET `/api/v1/eval/prompts/{promptId}/answers`

**Called By**: Prompt detail page to display answer pairs table

**Request**: Path parameter `promptId` (integer)

**Response**:
```json
{
  "answers": [
    {
      "answer_id": 25,
      "answer_a": "Quantum entanglement is like having magic twins...",
      "answer_b": "Imagine you have two special coins...",
      "is_a_x": true,
      "is_evaluated": true,
      "created_at": "2024-12-09T11:00:00Z"
    }
  ]
}
```

**Purpose**: List all answer pairs for a prompt with evaluation status.

**Blind Randomization**: `is_a_x` indicates whether Answer A corresponds to Model X (true) or Model Y (false).

### POST `/api/v1/eval/prompts/{promptId}/answers`

**Called By**: Prompt detail page when user submits "Add Answers" dialog (manual mode)

**Request**:
```json
{
  "answer_x": "Quantum entanglement is like having magic twins...",
  "answer_y": "Imagine you have two special coins..."
}
```

**Response**:
```json
{
  "answer_id": 25,
  "is_a_x": true,
  "message": "Answer pair added"
}
```

**Purpose**: Add a new answer pair for manual evaluation.

**Randomization**: Backend randomly assigns X/Y to A/B positions to ensure blind evaluation.

### GET `/api/v1/eval/answers/{answerId}/eval-prompt`

**Called By**: Prompt detail page when user clicks "Copy Eval Prompt"

**Request**: Path parameter `answerId` (integer)

**Response**:
```json
{
  "eval_prompt": "You are evaluating two responses to the following prompt:\n\nPrompt: Explain quantum entanglement to a 5-year-old.\n\nAnswer A: Quantum entanglement is like having magic twins...\n\nAnswer B: Imagine you have two special coins...\n\nEvaluate both answers on the following dimensions:...",
  "answer_id": 25
}
```

**Purpose**: Generate evaluation prompt with blinded answers for manual judging.

### POST `/api/v1/eval/answers/{answerId}/evaluate`

**Called By**: Prompt detail page when user submits "Paste Result" dialog (manual mode)

**Request**:
```json
{
  "evaluation_result": "{\"winner\": \"A\", \"scores\": {\"factual_correctness\": 0.8, \"completeness\": 0.7}, \"reasoning\": \"Answer A is more accurate...\"}"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Evaluation recorded"
}
```

**Purpose**: Submit evaluation result from manual judging.

### DELETE `/api/v1/eval/answers/{answerId}`

**Called By**: Prompt detail page when user deletes an answer pair

**Request**: Path parameter `answerId` (integer)

**Response**:
```json
{
  "success": true,
  "message": "Answer pair deleted"
}
```

**Purpose**: Delete an answer pair and its evaluation (if exists).

### GET `/api/v1/eval/experiments/{id}/export-csv`

**Called By**: Experiment detail page when user clicks "Export CSV"

**Request**: Path parameter `id` (integer)

**Response**: CSV file download

**CSV Format**:
```csv
prompt_id,prompt_text,answer_id,answer_x,answer_y,winner,score,factual_correctness,completeness,coherence,hallucination_risk,academic_response
10,"Explain quantum...",25,"Quantum entanglement...","Imagine you have...",X,0.6,0.8,0.7,0.6,0.2,0.9
```

**Purpose**: Export all evaluations to CSV format for external analysis.

### GET `/api/v1/eval/experiments/{id}/export-jsonl`

**Called By**: Experiment detail page when user clicks "Export JSONL"

**Request**: Path parameter `id` (integer)

**Response**: JSONL file download

**JSONL Format** (one JSON object per line):
```jsonl
{"prompt_id": 10, "prompt_text": "Explain quantum...", "answer_id": 25, "answer_x": "Quantum entanglement...", "answer_y": "Imagine you have...", "winner": "X", "scores": {"factual_correctness": 0.8}}
```

**Purpose**: Export all answers to JSONL format for LLM training or fine-tuning.

### GET `/api/v1/settings/templates`

**Called By**: New experiment page to load available evaluation templates

**Request Parameters**:
- `template_type` (string): "eval"

**Response**:
```json
{
  "templates": [
    {
      "template_id": 5,
      "function_tag": "eval_default",
      "name": "Default Evaluation Template",
      "content": "You are an expert evaluator..."
    }
  ]
}
```

**Purpose**: Load evaluation templates for experiment creation.

### GET `/api/v1/settings/templates/{function_tag}`

**Called By**: New experiment page to preview template content

**Request**: Path parameter `function_tag` (string)

**Response**:
```json
{
  "template_id": 5,
  "function_tag": "eval_default",
  "name": "Default Evaluation Template",
  "content": "You are an expert evaluator tasked with comparing two responses..."
}
```

**Purpose**: Retrieve full template content for preview.

## API Implementation

### Backend Modules Used

**Eval API Router**: `src/vulcanlab/api/eval.py`
- All eval endpoints

**Eval Service**: `src/vulcanlab/services/eval_service.py`
- `create_experiment()` - Experiment creation logic
- `add_prompt()` - Prompt creation
- `add_answer_pair()` - Answer submission with randomization
- `evaluate_answer()` - Evaluation processing
- `calculate_statistics()` - Statistical analysis
- `export_csv()` / `export_jsonl()` - Data export

**LLM Service**: `src/vulcanlab/services/llm_service.py`
- `generate_answer()` - Automatic answer generation
- `judge_answers()` - Automatic evaluation

**Statistics Service**: `src/vulcanlab/services/statistics_service.py`
- `wilcoxon_signed_rank_test()` - Statistical significance testing
- `calculate_win_rates()` - Win rate computation

### Blind Randomization Logic

**Purpose**: Prevent bias by hiding which model produced which answer

**Implementation**:
1. When answer pair is submitted, backend randomly assigns:
   - `is_a_x = True`: Answer X → Position A, Answer Y → Position B
   - `is_a_x = False`: Answer X → Position B, Answer Y → Position A
2. Evaluation prompt shows only "Answer A" and "Answer B"
3. Judge selects winner as "A" or "B"
4. Backend maps back to X or Y using `is_a_x` flag

**Database Storage**:
```sql
answers (
  id, prompt_id,
  answer_x TEXT,    -- Original X answer
  answer_y TEXT,    -- Original Y answer
  is_a_x BOOLEAN    -- True if A=X, False if A=Y
)

evaluations (
  id, answer_id,
  winner CHAR(1),   -- 'A' or 'B' from judge
  scores JSONB      -- Dimension scores
)
```

### Statistical Analysis

**Metrics Calculated**:

1. **X Win Rate**: `(count(winner='X') / total_evaluations)`
2. **Mean Score**: Average preference score across all evaluations
3. **Median Score**: Median preference score
4. **Tie Rate**: `(count(winner='TIE') / total_evaluations)`
5. **Harm Rate**: `(count(harm_detected) / total_evaluations)`
6. **Wilcoxon p-value**: Statistical significance test

**Wilcoxon Signed-Rank Test**:
- Tests if X vs Y win rates are significantly different
- Null hypothesis: No difference between models
- p < 0.05: Statistically significant difference
- Used for paired comparisons

**Implementation**:
```python
from scipy.stats import wilcoxon

# Create paired scores (X_score - Y_score for each evaluation)
paired_diffs = [eval.x_score - eval.y_score for eval in evaluations]

# Run test
statistic, p_value = wilcoxon(paired_diffs)
```

### Automatic Evaluation Flow

**Steps**:
1. User clicks "New Eval" on prompt detail page
2. Backend generates Answer X using model_x via selected provider (OpenAI/Gemini)
3. Backend generates Answer Y using model_y via selected provider
4. Backend randomly assigns A/B positions
5. Backend generates evaluation prompt with blinded answers
6. Backend submits to judge_model via selected provider
7. Backend parses judge response (winner, scores, reasoning)
8. Backend stores evaluation in database
9. Frontend refreshes to show new evaluation

**Provider Integration**:
- **OpenAI**: Uses OpenAI API for GPT models
- **Gemini**: Uses Google Gemini API for Gemini models

## Database Tables

### experiments

**Description**: Stores evaluation experiment configuration

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Experiment identifier
- `name` (TEXT): Experiment name
- `description_x` (TEXT): Description of Answer Set X
- `description_y` (TEXT): Description of Answer Set Y
- `model_x` (TEXT): Model name for Set X
- `model_y` (TEXT): Model name for Set Y
- `judge_model` (TEXT): Model name for judging
- `eval_template_id` (INTEGER FOREIGN KEY): References templates.id
- `auto_mode_enabled` (BOOLEAN): Automatic evaluation enabled
- `auto_answer_provider` (TEXT): Provider for answer generation ('openai', 'gemini')
- `auto_judge_provider` (TEXT): Provider for judging ('openai', 'gemini')
- `created_at` (TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP): Last modification timestamp

### experiment_dimensions

**Description**: Stores evaluation dimensions for each experiment

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Dimension identifier
- `experiment_id` (INTEGER FOREIGN KEY): References experiments.id
- `name` (TEXT): Dimension name (e.g., "factual_correctness")
- `description` (TEXT): Dimension description
- `is_core` (BOOLEAN): Whether dimension is always included

**Core Dimensions** (is_core = TRUE):
- factual_correctness
- completeness
- coherence
- hallucination_risk
- academic_response

### prompts

**Description**: Stores test prompts for experiments

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Prompt identifier
- `experiment_id` (INTEGER FOREIGN KEY): References experiments.id
- `prompt_text` (TEXT): The test prompt
- `created_at` (TIMESTAMP): Creation timestamp

### answers

**Description**: Stores answer pairs for evaluation

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Answer identifier
- `prompt_id` (INTEGER FOREIGN KEY): References prompts.id
- `answer_x` (TEXT): Answer from Model X
- `answer_y` (TEXT): Answer from Model Y
- `is_a_x` (BOOLEAN): True if A=X, False if A=Y (blind randomization)
- `created_at` (TIMESTAMP): Creation timestamp

### evaluations

**Description**: Stores evaluation results

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Evaluation identifier
- `answer_id` (INTEGER FOREIGN KEY): References answers.id
- `winner` (CHAR(1)): 'A', 'B', or 'T' (tie)
- `scores` (JSONB): Dimension scores as JSON object
- `reasoning` (TEXT): Judge's reasoning
- `harm_detected` (BOOLEAN): Whether harmful content detected
- `created_at` (TIMESTAMP): Creation timestamp

**Scores JSONB Format**:
```json
{
  "factual_correctness": 0.8,
  "completeness": 0.7,
  "coherence": 0.9,
  "hallucination_risk": 0.1,
  "academic_response": 0.85,
  "creativity": 0.6
}
```

### templates

**Description**: Stores evaluation prompt templates

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Template identifier
- `function_tag` (TEXT UNIQUE): Template identifier
- `name` (TEXT): Template display name
- `content` (TEXT): Template prompt text
- `template_type` (TEXT): "eval"

## UI Components

### AutoModeToggle

**Location**: `/src/components/eval/AutoModeToggle.tsx`

**Purpose**: Toggle automatic evaluation mode and select providers

**Features**:
- Switch to enable/disable automatic mode
- Dropdown to select answer provider (OpenAI/Gemini)
- Dropdown to select judge provider (OpenAI/Gemini)
- Saves settings to experiment configuration

### AddAnswersDialog

**Location**: `/src/components/eval/AddAnswersDialog.tsx`

**Purpose**: Manual answer pair submission

**Features**:
- Text areas for Answer X and Answer Y
- Validation (requires non-empty answers)
- Implements blind randomization on submit
- Error handling

### PasteResultDialog

**Location**: `/src/components/eval/PasteResultDialog.tsx`

**Purpose**: Manual evaluation result submission

**Features**:
- Text area for pasting judge's evaluation
- JSON validation
- Parses winner, scores, reasoning
- Error handling for invalid JSON

### NewEvalDialog

**Location**: `/src/components/eval/NewEvalDialog.tsx`

**Purpose**: Trigger automatic evaluation

**Features**:
- Confirmation dialog
- Initiates automatic answer generation and judging
- Loading state during processing
- Error handling

### ExperimentStatsCard

**Location**: `/src/components/eval/ExperimentStatsCard.tsx`

**Purpose**: Display statistical analysis

**Features**:
- Shows all computed metrics
- Highlights statistically significant results (p < 0.05)
- Progress bars for win rates
- Formatted percentages and scores

## Key Features

### Blind Evaluation

**Purpose**: Eliminate bias by hiding model identities

**Implementation**:
- Random A/B assignment for each answer pair
- Judge sees only "Answer A" and "Answer B"
- Backend maps results back to X/Y

**Benefits**:
- Unbiased comparisons
- Fair evaluation
- Credible results

### Statistical Rigor

**Wilcoxon Test**: Determines if differences are statistically significant

**Win Rates**: Simple, interpretable metric

**Tie Detection**: Identifies cases where models are equivalent

**Harm Detection**: Flags problematic outputs

### Flexible Execution Modes

**Manual Mode**:
- User generates answers externally
- User judges using external LLM
- Full control over process
- Supports any model or judging criteria

**Automatic Mode**:
- System generates answers via API
- System judges via API
- Faster, scalable
- Requires API access and credits

### Export Capabilities

**CSV Export**:
- Import into Excel, R, Python for analysis
- Shareable format
- Human-readable

**JSONL Export**:
- LLM training data format
- Fine-tuning datasets
- Machine-readable

## Error Handling

### Validation Errors (422)

**Duplicate Dimension Name**:
```json
{
  "error": "Duplicate dimension",
  "detail": "Dimension 'factual_correctness' already exists"
}
```

**Invalid JSON in Manual Evaluation**:
```json
{
  "error": "Invalid JSON",
  "detail": "Could not parse evaluation result"
}
```

### Not Found Errors (404)

**Experiment Not Found**: Experiment ID doesn't exist or was deleted

**Prompt Not Found**: Prompt ID doesn't exist or was deleted

**Answer Not Found**: Answer ID doesn't exist or was deleted

### LLM API Errors (503)

**Provider Unavailable**:
```json
{
  "error": "LLM provider error",
  "detail": "OpenAI API returned 503 Service Unavailable"
}
```

**Rate Limit Exceeded**:
```json
{
  "error": "Rate limit exceeded",
  "detail": "OpenAI rate limit reached, retry after 60 seconds"
}
```

## Technical Implementation

**Framework**: Next.js 13+ App Router

**State Management**: React hooks (useState, useEffect, useCallback)

**Form Handling**: React Hook Form with validation

**UI Library**: shadcn/ui (Card, Table, Button, Form, Dialog, Switch, Badge, Accordion)

**Icons**: Lucide React (FlaskConical, Copy, Trash2, Eye, Plus)

**Styling**: Tailwind CSS

**Data Fetching**: Fetch API with error handling

**File Downloads**: Blob API for CSV/JSONL exports

**Statistical Analysis**: Backend computation (scipy.stats)

## Use Cases

### Model Comparison Research

**Goal**: Compare two LLM models objectively

**Workflow**:
1. Create experiment with both models
2. Add diverse test prompts (20-100)
3. Run automatic evaluation on all prompts
4. Analyze statistics
5. Export results for publication

### Prompt Engineering

**Goal**: Test which prompt format yields better responses

**Workflow**:
1. Create experiment: Prompt A vs Prompt B (same model)
2. Add test cases
3. Evaluate responses
4. Identify winning prompt format

### Quality Assurance

**Goal**: Verify model outputs meet quality standards

**Workflow**:
1. Create experiment: Production model vs Baseline
2. Add real user prompts
3. Manual evaluation by domain experts
4. Check if production model statistically better
