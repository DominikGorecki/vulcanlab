# Simple Conversion Page Documentation

## Overview

The Simple Conversion page provides a streamlined, single-page document conversion workflow that automates the process of converting PDF and EPUB files to markdown format and processing them through the entire pipeline (conversion → sanitization → chunking). It offers two execution modes: automatic (using LLM) and manual (user-provided LLM responses).

### Pages

- **Main Page**: `/simple-conversion` - File selection, metadata entry, and conversion history
- **Automatic Workflow**: `/simple-conversion/automatic/[work_id]` - Automated pipeline execution with status tracking
- **Manual Workflow**: `/simple-conversion/manual/[work_id]` - Manual LLM prompt/response workflow
- **History Detail**: `/simple-conversion/history/[work_id]` - View full conversion results and generated chunks

### User Workflow

#### Starting a Conversion

1. Select a file from the input folder dropdown
2. Enter bibliographic metadata (title, author, optional year)
3. Choose execution mode:
   - **Automatic**: Pipeline runs automatically using LLM
   - **Manual**: User copies prompt, pastes into their own LLM, submits result
4. Submit to start conversion

#### Automatic Mode Workflow

1. Pipeline executes automatically with real-time status updates
2. Status polling every 2 seconds shows progress through stages:
   - Parse & Classify (determines if document is small or large)
   - Sanitize (cleans and structures content)
   - Chunk (splits into semantic chunks)
   - Complete
3. View results table with all generated chunks
4. Click "View Full Results" to see detailed breakdown

#### Manual Mode Workflow

1. System generates and displays LLM prompt
2. User copies prompt to clipboard
3. User pastes prompt into their preferred LLM interface
4. User pastes LLM response back into the system
5. Option to switch to automatic execution if desired
6. Upon submission, pipeline processes with status polling
7. View results when complete

#### Viewing History

1. History table shows all past conversions with status
2. Click any row to view full results
3. See conversion metadata, chunk statistics, and all generated chunks
4. Search and filter chunks by content or heading

## API Calls

### GET `/conv/io-folder-data`

**Called By**: Main page (`/simple-conversion`) on component mount

**Request**: No parameters

**Response**:
```json
{
  "input_files": ["book1.pdf", "book2.epub"],
  "processed_files": []
}
```

**Purpose**: Fetch list of available files in the input folder for selection.

### POST `/api/simple-conversion/start`

**Called By**: Main page when user submits the conversion form

**Request**:
```json
{
  "file_path": "book1.pdf",
  "title": "Introduction to Psychology",
  "author": "John Doe",
  "year": 2024,
  "mode": "automatic"
}
```

**Response**:
```json
{
  "work_id": 123,
  "status": "started"
}
```

**Purpose**: Initiate a new conversion with metadata and execution mode. Creates a new work record and begins conversion process.

### GET `/api/simple-conversion/history`

**Called By**: Main page to display conversion history table

**Request**: No parameters

**Response**:
```json
{
  "items": [
    {
      "work_id": 123,
      "title": "Introduction to Psychology",
      "author": "John Doe",
      "classification": "small",
      "mode": "automatic",
      "status": "complete",
      "created_at": "2024-12-09T10:30:00Z",
      "error_message": null
    }
  ]
}
```

**Purpose**: Retrieve list of all past conversions with status and metadata.

**Status Values**: `complete`, `failed`, `converting`, `sanitized`

**Classification Values**: `small`, `large`, `null` (not yet classified)

### GET `/api/simple-conversion/automatic/status/{work_id}`

**Called By**: Automatic workflow page, polling every 2 seconds

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "work_id": 123,
  "status": "chunking",
  "classification": "small",
  "title": "Introduction to Psychology",
  "author": "John Doe",
  "year": 2024,
  "chunks": [],
  "error": null,
  "token_count": 45000
}
```

**Purpose**: Poll conversion status during automatic execution. Returns current pipeline stage and results when complete.

**Status Values**: `parsing`, `classifying`, `sanitizing`, `chunking`, `complete`, `failed`

### GET `/api/simple-conversion/manual-prompt/{work_id}`

**Called By**: Manual workflow page on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "prompt": "You are an expert at analyzing and classifying documents...",
  "work_id": 123
}
```

**Purpose**: Generate and retrieve the LLM prompt for manual execution mode.

### POST `/api/simple-conversion/manual-submit/{work_id}`

**Called By**: Manual workflow page when user submits LLM response

**Request**:
```json
{
  "llm_response": "{\n  \"classification\": \"small\",\n  \"reasoning\": \"...\"\n}"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Processing started"
}
```

**Purpose**: Submit user-provided LLM response and trigger pipeline processing.

### POST `/api/simple-conversion/execute-auto/{work_id}`

**Called By**: Manual workflow page when user switches to automatic execution

**Request**: No body parameters

**Response**:
```json
{
  "success": true,
  "message": "Automatic execution started"
}
```

**Purpose**: Switch from manual to automatic mode and execute pipeline automatically.

### GET `/api/simple-conversion/history/{work_id}`

**Called By**: History detail page on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "work_id": 123,
  "title": "Introduction to Psychology",
  "author": "John Doe",
  "year": 2024,
  "classification": "small",
  "mode": "automatic",
  "status": "complete",
  "created_at": "2024-12-09T10:30:00Z",
  "token_count": 45000,
  "chunks": [
    {
      "chunk_id": 1,
      "level": "h1",
      "heading_breadcrumb": "Introduction",
      "content": "Psychology is the scientific study of...",
      "start_line": 1,
      "end_line": 25
    }
  ],
  "error_message": null
}
```

**Purpose**: Retrieve full conversion results including all generated chunks and metadata.

## API Implementation

### Backend Modules Used

The Simple Conversion endpoints are implemented in:
- `src/vulcanlab/api/simple_conversion.py` - Main API router and endpoints
- `src/vulcanlab/services/simple_conversion_service.py` - Business logic and pipeline orchestration
- `src/vulcanlab/services/llm_service.py` - LLM interaction for automatic mode
- `src/vulcanlab/conv/` - Document conversion modules
- `src/vulcanlab/sanitization/` - Content sanitization modules
- `src/vulcanlab/chunking/` - Content chunking modules

### Pipeline Processing

#### Parse & Classify Stage

**Purpose**: Analyze document and determine if it's small (< 100k tokens) or large (≥ 100k tokens)

**Modules**:
- `conv.epub2md` or `conv.pdf2md` - Convert source file to markdown
- `llm_service.classify_document()` - Use LLM to classify document size

**Database Operations**:
- INSERT into `works` table with initial metadata
- UPDATE `works.classification` with size determination
- UPDATE `works.token_count` with estimated tokens

#### Sanitization Stage

**Purpose**: Clean and structure markdown content

**Modules**:
- `sanitization.extract_titles()` - Extract heading structure
- `sanitization.suggest_improvements()` - Generate title improvements
- `sanitization.apply_changes()` - Apply sanitization changes

**Database Operations**:
- UPDATE `works.sanitized_md` with cleaned content
- INSERT into `titles` table with heading structure

#### Chunking Stage

**Purpose**: Split document into semantic chunks for vectorization

**Modules**:
- `chunking.heading_chunker()` - Split by headings (H1-H5)
- `chunking.content_chunker()` - Split content within sections

**Database Operations**:
- INSERT into `chunks` table with all generated chunks
- UPDATE `works.status = 'ready_for_vectorization'`

### Error Handling

**Common Errors**:
- `file_not_found`: Source file missing from input folder
- `conversion_failed`: PDF/EPUB conversion error
- `classification_failed`: LLM classification error
- `sanitization_failed`: Content sanitization error
- `chunking_failed`: Chunk generation error
- `invalid_llm_response`: Manual mode LLM response parsing failed

**Error Response Format**:
```json
{
  "error": "classification_failed",
  "message": "Failed to classify document",
  "detail": "LLM returned invalid JSON"
}
```

## Database Tables

### works

**Description**: Stores work records with conversion metadata and pipeline status

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Work identifier
- `title` (TEXT): Work title
- `authors` (TEXT): Author name(s)
- `year` (INTEGER): Publication year
- `classification` (TEXT): 'small' or 'large'
- `mode` (TEXT): 'automatic' or 'manual'
- `status` (TEXT): Pipeline stage (converting, sanitizing, chunking, complete, failed)
- `sanitized_md` (TEXT): Cleaned markdown content
- `token_count` (INTEGER): Estimated token count
- `error_message` (TEXT): Error details if failed
- `created_at` (TIMESTAMP): Creation timestamp

**Usage**: Primary record for tracking conversion workflow and storing processed content.

### chunks

**Description**: Stores semantic chunks generated from sanitized content

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Chunk identifier
- `work_id` (INTEGER FOREIGN KEY): References works.id
- `level` (TEXT): Chunk type (h1-h5 for headings, sentence for content)
- `heading_breadcrumb` (TEXT): Full heading path
- `content` (TEXT): Chunk text content
- `start_line` (INTEGER): Starting line number in sanitized_md
- `end_line` (INTEGER): Ending line number in sanitized_md
- `parent_id` (INTEGER FOREIGN KEY): Parent chunk for hierarchical structure
- `vector` (VECTOR): Embedding vector (if vectorized)

**Usage**: Stores all chunks for RAG retrieval and search functionality.

### titles

**Description**: Stores extracted heading structure from sanitized content

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Title identifier
- `work_id` (INTEGER FOREIGN KEY): References works.id
- `level` (TEXT): Heading level (h1-h5)
- `title_text` (TEXT): Heading text
- `line_number` (INTEGER): Line number in sanitized_md

**Usage**: Tracks document structure for chunking and navigation.

## UI Components

### SimpleConversionSummaryCard

**Location**: `/src/components/simple-conversion/SimpleConversionSummaryCard.tsx`

**Purpose**: Display conversion metadata and metrics

**Features**:
- Shows title, author, year
- Classification badge (Small/Large)
- Mode indicator (Automatic/Manual)
- Status badge with color coding
- Token count and chunk statistics
- Error banner for failed conversions

### HistoryErrorBoundary

**Location**: `/src/components/simple-conversion/HistoryErrorBoundary.tsx`

**Purpose**: Prevent history section crashes from breaking the entire page

**Features**:
- Catches React rendering errors in history table
- Displays user-friendly fallback UI
- Prevents cascade failures

## Key Features

1. **Simplified Workflow**: Single page for file selection and metadata entry
2. **Two Execution Modes**: Automatic (LLM-powered) or Manual (user-provided responses)
3. **Real-time Status Updates**: 2-second polling for progress tracking
4. **Comprehensive History**: View all past conversions with detailed results
5. **Error Recovery**: Clear error messages with retry capabilities
6. **Form Validation**: Client-side validation for metadata fields
7. **Responsive Design**: Mobile and desktop optimized layouts
8. **Status Indicators**: Visual badges for classification, mode, and status
9. **Search and Filter**: Search through generated chunks in results view
10. **Clipboard Integration**: Copy prompts for manual mode workflow

## Differences from Standard Conversion Page

| Feature | Simple Conversion | Standard Conversion |
|---------|------------------|---------------------|
| Workflow | Single-page, automated | Multi-step, manual review |
| Inspection | No intermediate inspection | Full artifact inspection |
| Metadata Entry | Upfront, before conversion | After conversion review |
| Pipeline | Fully automated | Manual progression through stages |
| LLM Mode | Optional manual mode | Not available |
| Target Users | Quick processing, trust automation | Detailed review, quality control |
| History View | Built-in history table | Not included |

## Technical Implementation

**Framework**: Next.js 13+ App Router with React Server Components

**State Management**: React hooks (useState, useEffect, useCallback)

**Data Fetching**: Custom `usePageData` hook with error handling

**Form Handling**: React Hook Form with validation

**UI Library**: shadcn/ui (Card, Table, Button, Form, Alert, Badge, Dialog)

**Icons**: Lucide React

**Styling**: Tailwind CSS with responsive utilities

**Polling**: useEffect with setInterval for status updates (2-second intervals)

**Navigation**: Next.js useRouter for programmatic routing

**Error Boundaries**: React Error Boundaries for fault isolation
