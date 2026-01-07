# Cleanup Page Documentation

## Overview

The Cleanup page is a data management tool that allows users to search for content chunks and permanently delete them from the database. When a chunk is deleted, all of its descendant chunks in the hierarchical structure are also deleted. This page is essential for removing unwanted or erroneous content from the corpus.

### Pages

- **Main Page**: `/cleanup` - Search and delete chunks

### User Workflow

1. Enter search query (searches both chunk titles and content)
2. Optional: Enable "Headings Only" filter to search only H1-H5 heading chunks
3. Click "Search" to execute query
4. Review paginated search results
5. For each result:
   - **View**: Click eye icon to see full chunk content in modal
   - **Delete**: Click trash icon to delete chunk and descendants
6. Before deletion, review confirmation dialog showing:
   - The chunk to be deleted
   - All descendant chunks (up to 50 shown)
   - Total count of chunks that will be deleted
7. Confirm deletion
8. Search results automatically update after deletion

## API Calls

### GET `/api/v1/chunks/search`

**Called By**: Cleanup page when user executes search

**Request Parameters**:
- `q` (string, required): Search query (searches content and breadcrumb)
- `page` (integer, default: 1): Current page number
- `page_size` (integer, default: 20): Results per page
- `headings_only` (boolean, default: false): Filter to H1-H5 headings only

**Response**:
```json
{
  "results": [
    {
      "chunk_id": 123,
      "work_id": 45,
      "work_title": "Introduction to Psychology",
      "work_author": "John Doe",
      "level": "h2",
      "heading_breadcrumb": "Chapter 1 > Memory Systems",
      "content_preview": "Working memory is a cognitive system with limited capacity...",
      "start_line": 100,
      "end_line": 125
    }
  ],
  "total": 47,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

**Purpose**: Search for chunks by content or heading breadcrumb, with optional headings-only filter.

**Search Behavior**: Searches both `content` and `heading_breadcrumb` fields using case-insensitive pattern matching.

### GET `/api/v1/chunks/{id}/descendants`

**Called By**: Cleanup page when user clicks delete button, before showing confirmation

**Request**: Path parameter `id` (integer) - chunk ID

**Response**:
```json
{
  "chunk_id": 123,
  "descendants": [
    {
      "chunk_id": 124,
      "level": "h3",
      "heading_breadcrumb": "Chapter 1 > Memory Systems > Working Memory",
      "content_preview": "The phonological loop is a component...",
      "start_line": 105,
      "end_line": 115
    },
    {
      "chunk_id": 125,
      "level": "sentence",
      "heading_breadcrumb": "Chapter 1 > Memory Systems > Working Memory",
      "content_preview": "Research has shown that working memory capacity...",
      "start_line": 116,
      "end_line": 118
    }
  ],
  "total_descendants": 15
}
```

**Purpose**: Fetch all descendant chunks that will be deleted along with the target chunk.

**Hierarchical Logic**: A chunk is a descendant if:
- It has a `parent_id` that traces back to the target chunk
- It appears in the document tree under the target chunk

### GET `/api/v1/chunks/{id}`

**Called By**: Cleanup page when user clicks view/eye icon

**Request**: Path parameter `id` (integer) - chunk ID

**Response**:
```json
{
  "chunk_id": 123,
  "work_id": 45,
  "work_title": "Introduction to Psychology",
  "work_author": "John Doe",
  "level": "h2",
  "heading_breadcrumb": "Chapter 1 > Memory Systems",
  "content": "Working memory is a cognitive system with limited capacity that is responsible for temporarily holding information available for processing. The concept was formalized by Baddeley and Hitch in 1974...",
  "start_line": 100,
  "end_line": 125
}
```

**Purpose**: Retrieve full content of a specific chunk for detailed viewing.

**Note**: Unlike search results which include `content_preview` (truncated), this returns the full `content` field.

### DELETE `/api/v1/chunks/{id}`

**Called By**: Cleanup page when user confirms deletion in dialog

**Request**: Path parameter `id` (integer) - chunk ID

**Response**:
```json
{
  "success": true,
  "deleted_count": 16,
  "message": "Chunk and 15 descendants deleted successfully"
}
```

**Error Response (404)**:
```json
{
  "error": "Chunk not found",
  "detail": "Chunk with ID 123 does not exist"
}
```

**Purpose**: Permanently delete the specified chunk and all its descendants from the database.

**Cascading Behavior**: Uses recursive deletion to remove all descendant chunks in the hierarchy.

## API Implementation

### Backend Modules Used

**Chunks API**: `src/vulcanlab/api/chunks.py`
- `search_chunks()` - Search endpoint
- `get_chunk()` - Retrieve single chunk
- `get_descendants()` - Get chunk descendants
- `delete_chunk()` - Delete chunk and descendants

**Chunk Service**: `src/vulcanlab/services/chunk_service.py`
- `search_chunks_by_content()` - Pattern matching search
- `get_chunk_by_id()` - Retrieve chunk details
- `get_descendants_recursive()` - Build descendant tree
- `delete_chunk_cascade()` - Cascading deletion logic

### Search Implementation

**Algorithm**: PostgreSQL pattern matching with ILIKE

**SQL Logic**:
```sql
SELECT
  c.id, c.work_id, c.level, c.heading_breadcrumb,
  LEFT(c.content, 100) AS content_preview,
  c.start_line, c.end_line,
  w.title AS work_title, w.authors AS work_author
FROM chunks c
JOIN works w ON c.work_id = w.id
WHERE
  c.content ILIKE '%' || $1 || '%'
  OR c.heading_breadcrumb ILIKE '%' || $1 || '%'
  AND ($2 = FALSE OR c.level IN ('h1', 'h2', 'h3', 'h4', 'h5'))
ORDER BY c.work_id, c.start_line
LIMIT 20 OFFSET $3;
```

**Headings Filter**: When enabled, adds `level IN ('h1', 'h2', 'h3', 'h4', 'h5')` condition.

### Descendants Retrieval

**Algorithm**: Recursive CTE (Common Table Expression)

**SQL Logic**:
```sql
WITH RECURSIVE descendant_tree AS (
  -- Base case: direct children
  SELECT id, parent_id, level, heading_breadcrumb,
         LEFT(content, 100) AS content_preview,
         start_line, end_line
  FROM chunks
  WHERE parent_id = $1

  UNION ALL

  -- Recursive case: children of children
  SELECT c.id, c.parent_id, c.level, c.heading_breadcrumb,
         LEFT(c.content, 100) AS content_preview,
         c.start_line, c.end_line
  FROM chunks c
  INNER JOIN descendant_tree dt ON c.parent_id = dt.id
)
SELECT * FROM descendant_tree
ORDER BY start_line;
```

**Performance**: Uses index on `parent_id` for efficient traversal.

### Cascading Deletion

**Algorithm**: Recursive deletion starting from leaf nodes

**Steps**:
1. Get all descendant IDs using recursive query
2. Delete from leaf nodes upward (to avoid foreign key conflicts)
3. Delete the target chunk last
4. Return total count of deleted chunks

**SQL Logic**:
```sql
WITH RECURSIVE descendant_ids AS (
  SELECT id FROM chunks WHERE id = $1
  UNION ALL
  SELECT c.id FROM chunks c
  INNER JOIN descendant_ids d ON c.parent_id = d.id
)
DELETE FROM chunks
WHERE id IN (SELECT id FROM descendant_ids)
RETURNING id;
```

**Transaction Safety**: Entire deletion operation wrapped in database transaction for atomicity.

## Database Tables

### chunks

**Description**: Stores semantic chunks with hierarchical parent-child relationships

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Chunk identifier
- `work_id` (INTEGER FOREIGN KEY): References works.id
- `parent_id` (INTEGER FOREIGN KEY): References chunks.id (NULL for root chunks)
- `level` (TEXT): Chunk type (h1, h2, h3, h4, h5, sentence)
- `heading_breadcrumb` (TEXT): Full heading path (e.g., "Ch 1 > Section A > Subsection B")
- `content` (TEXT): Full chunk text content
- `start_line` (INTEGER): Starting line in sanitized markdown
- `end_line` (INTEGER): Ending line in sanitized markdown
- `vector` (VECTOR): Embedding vector (nullable)

**Indexes**:
- `idx_chunks_content`: GIN/B-tree index for content search
- `idx_chunks_breadcrumb`: B-tree index for breadcrumb search
- `idx_chunks_parent_id`: B-tree index for parent-child traversal
- `idx_chunks_level`: B-tree index for headings-only filter

**Hierarchical Structure**: Chunks form a tree structure where:
- H1 chunks are roots (parent_id = NULL)
- H2 chunks are children of H1
- H3 chunks are children of H2
- Sentence chunks are children of their containing heading

### works

**Description**: Stores work metadata

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Work identifier
- `title` (TEXT): Work title
- `authors` (TEXT): Author name(s)

**Usage**: Joined with chunks to display bibliographic information in search results.

## UI Components

### Search Interface

**Features**:
- Text input for search query
- "Headings Only" checkbox filter
- Search button with loading state
- Real-time validation (requires non-empty query)

### Results Table

**Columns**:
- **Chunk Preview**: Truncated content (100 characters)
- **Breadcrumb**: Full heading path
- **Metadata**: Level badge, Work ID, Line numbers, Chunk ID
- **Actions**: View (eye icon) and Delete (trash icon) buttons

**Features**:
- Color-coded level badges (H1-H5, Sentence)
- Hover states on action buttons
- Disabled delete button during loading
- Empty state when no results found

### View Chunk Modal

**Triggered By**: Clicking eye icon on any search result

**Features**:
- Dialog showing full chunk content (scrollable)
- Metadata display (Chunk ID, Work ID, Level, Lines)
- Heading breadcrumb
- Delete button (alternative to row delete button)
- Close button

**Loading State**: Shows spinner while fetching chunk details

**Error Handling**: Displays error message if chunk not found (e.g., already deleted)

### Delete Confirmation Dialog

**Triggered By**: Clicking trash icon or delete button in view modal

**Features**:
- Shows chunk to be deleted with preview
- Lists all descendants (limited to first 50)
- Displays total count: "and X more descendants will also be deleted"
- Clear warning message about permanent deletion
- Cancel and Delete buttons
- Delete button disabled while loading descendants

**Safety Features**:
- Requires explicit confirmation
- Shows full impact (number of descendants)
- Prevents accidental deletion
- Cannot proceed if descendants fail to load

### Toast Notifications

**Success Notification**: "Chunk and X descendants deleted successfully"

**Error Notifications**:
- "Chunk not found" (404)
- "Invalid search query" (422)
- "Failed to load chunk details"
- "Failed to load descendants"
- Generic error messages for unexpected failures

## Key Features

### Search Capabilities

1. **Content Search**: Searches full chunk content
2. **Breadcrumb Search**: Searches heading paths
3. **Combined Search**: Results match either content or breadcrumb
4. **Case-Insensitive**: All searches ignore case
5. **Headings Filter**: Optional filter to H1-H5 only

### Deletion Safety

1. **Descendant Preview**: Shows all chunks that will be deleted
2. **Confirmation Dialog**: Requires explicit user confirmation
3. **Transaction Safety**: Atomic deletion (all or nothing)
4. **Error Recovery**: Clear error messages for failures
5. **Visual Feedback**: Loading states during operations

### User Experience

1. **Real-time Updates**: Search results refresh after deletion
2. **Pagination**: Handle large result sets efficiently
3. **Loading States**: Visual feedback during async operations
4. **Error Handling**: User-friendly error messages
5. **Accessibility**: Keyboard navigation, ARIA labels

## Error Handling

### Validation Errors (422)

**Empty Query**:
```json
{
  "error": "Invalid query",
  "detail": "Search query cannot be empty"
}
```

### Not Found Errors (404)

**Chunk Not Found**:
```json
{
  "error": "Chunk not found",
  "detail": "Chunk with ID 123 does not exist or was already deleted"
}
```

**Use Case**: Chunk deleted by another user/session between search and delete action.

### Client-Side Validation

- Prevents search with empty query
- Disables delete button during loading
- Prevents modal actions during async operations

### Error Recovery

**After Search Error**:
- Display error card with retry button
- Preserve search parameters for retry
- Clear error on new search attempt

**After Delete Error**:
- Display error toast notification
- Keep search results visible
- Allow retry of deletion

**After View Error**:
- Display error in modal
- Allow closing modal
- Results table remains functional

## Technical Implementation

**Framework**: Next.js 13+ App Router

**State Management**: React hooks (useState, useEffect)

**UI Library**: shadcn/ui (Card, Button, Input, Checkbox, Badge, Dialog, AlertDialog, ScrollArea, Toast)

**Icons**: Lucide React (Search, Trash2, Eye, Loader2, ChevronLeft, ChevronRight, AlertCircle)

**Styling**: Tailwind CSS with responsive utilities

**Error Boundaries**: Not implemented (errors handled at component level)

**Toast Provider**: shadcn/ui toast system for notifications

## Use Cases

### Removing Erroneous Content

**Scenario**: Conversion error created incorrect chunks

**Workflow**:
1. Search for distinctive text from error
2. Identify erroneous chunk in results
3. View chunk to verify it's the error
4. Delete chunk (removes it and any sub-chunks)

### Cleaning Up Specific Sections

**Scenario**: Remove entire chapter or section

**Workflow**:
1. Search for chapter heading (e.g., "Chapter 5")
2. Enable "Headings Only" to find the H1/H2 heading chunk
3. View descendants to verify all section content
4. Delete heading chunk (removes entire section tree)

### Quality Control

**Scenario**: Remove low-quality or duplicate content

**Workflow**:
1. Search for problematic content pattern
2. Review results to identify duplicates
3. Delete unwanted chunks individually
4. Verify deletion with new search

## Performance Considerations

**Search Performance**:
- Indexed content and breadcrumb fields for fast pattern matching
- Page size limited to 20 results for quick load times
- Content preview truncated to reduce payload

**Deletion Performance**:
- Recursive CTE optimized for hierarchical traversal
- Single transaction for all deletions (no repeated round trips)
- Parent ID index ensures fast descendant lookup

**UI Performance**:
- Lazy loading of chunk details (only on view)
- Lazy loading of descendants (only on delete click)
- Pagination prevents rendering thousands of results

## Security Considerations

**No Undo**: Deletions are permanent and irreversible

**Authorization**: Should implement user permissions (not shown in current implementation)

**SQL Injection**: Uses parameterized queries to prevent injection attacks

**Cascading Deletion**: Intentional behavior to maintain referential integrity
