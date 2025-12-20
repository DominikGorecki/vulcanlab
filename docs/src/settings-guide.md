# VulcanLab Settings Guide

This guide covers all VulcanLab settings available through the Settings page, with the exception of RAG Configuration which is covered in a separate [RAG Settings Guide](rag-settings-guide.md).

## Overview

The VulcanLab Settings page provides a centralized interface for configuring your application. Settings are organized into tabs for easy navigation:

- **Init/Status** - Database health monitoring and initialization
- **Models** - LLM provider and model selection
- **Database** - PostgreSQL connection configuration
- **Paths** - Input/output directory configuration
- **Conversion** - Document processing pipeline settings
- **Templates** - Prompt template management
- **RAG Settings** - RAG pipeline configuration (see [RAG Settings Guide](rag-settings-guide.md))

---

## Init/Status Tab

The Init/Status tab provides database health monitoring and initialization tools.

### Database Health Checks

VulcanLab performs comprehensive health checks on your PostgreSQL database:

**Connection Check**
- Verifies database is accessible
- Tests credentials and network connectivity
- Status: ✅ Pass or ❌ Fail

**Extension Check**
- Confirms `pgvector` extension is installed and enabled
- Required for vector similarity search
- Status: ✅ Pass or ❌ Fail

**Schema Check**
- Validates all required tables exist
- Checks: `works`, `chunks`, `queries`, `templates`, `rag_config`, etc.
- Status: ✅ Pass or ❌ Fail

**Migration Check**
- Ensures all database migrations have been applied
- Checks migration history and pending updates
- Status: ✅ Pass or ❌ Fail

### Initialize Database

If health checks fail, you can initialize or reinitialize the database:

1. Click **"Initialize Database"** button
2. System will:
   - Run all pending migrations
   - Create required tables and indexes
   - Enable necessary extensions
   - Set up default data (templates, RAG config)

**Warning:** Never run database initialization on a production database without backing up your data first.

### Refresh Health Checks

Click **"Refresh Health Checks"** to re-run all validation tests after making changes.

---

## Models Tab

Configure which AI models VulcanLab uses for different tasks.

### Provider Selection

**Available Providers:**
- **Gemini** (Google's AI models)
- **OpenAI** (GPT models)

Select your preferred provider from the dropdown. VulcanLab will use this provider for all LLM operations unless specified otherwise.

### Model Configuration

VulcanLab uses two tiers of models for different tasks:

#### Light Models (Fast & Economical)
Used for:
- Query expansion
- Intent classification
- Entity extraction
- Simple document classification
- Heading hierarchy generation

**Default Light Models:**
- OpenAI: `gpt-4o-mini`
- Gemini: `gemini-flash-latest`

#### Full Models (Powerful & Accurate)
Used for:
- Complex document parsing and structuring
- RAG response generation
- Detailed content analysis
- Template-based generation

**Default Full Models:**
- OpenAI: `gpt-4o`
- Gemini: `gemini-2.5-pro`

### Customizing Models

You can customize which models are used for each tier:

1. Expand the provider section (OpenAI or Gemini)
2. Enter model names in **Light Model** and **Full Model** fields
3. Click **"Save Models"**

**Valid Model Names:**

*OpenAI Models:*
- `gpt-4o` (most capable)
- `gpt-4o-mini` (fast and affordable)
- `gpt-4-turbo`
- `gpt-3.5-turbo`

*Gemini Models:*
- `gemini-2.5-pro` (most capable)
- `gemini-flash-latest` (fast and affordable)
- `gemini-pro`
- `gemini-flash-2.0`

**Note:** Ensure you have valid API keys configured in your `.env` file for the provider you select.

---

## Database Tab

Configure PostgreSQL database connection settings.

### Database Settings

| Setting | Description | Example |
|---------|-------------|---------|
| **Admin User** | PostgreSQL superuser for migrations | `postgres` |
| **Host** | Database server hostname or IP | `127.0.0.1` or `localhost` |
| **Port** | Database server port | `5432` |
| **Database Name** | Name of the VulcanLab database | `vulcanlab` |
| **App User** | Application-level database user | `vulcanlab_app_user` |

### Admin User vs. App User

**Admin User:**
- Used only for database initialization and migrations
- Requires superuser privileges to create extensions and run DDL
- Credentials stored in `.env` as `POSTGRES_ADMIN_PASSWORD`

**App User:**
- Used for all application operations (reading/writing data)
- Has limited permissions for security
- Credentials stored in `.env` as `POSTGRES_PASSWORD`

### When to Update Database Settings

Update these settings when:
- Setting up VulcanLab for the first time
- Moving to a different database server
- Changing database names or users
- Migrating from development to production

### Saving Database Settings

1. Update the desired fields
2. Click **"Save Database Settings"**
3. Settings are saved to `vulcanlab.config.json`
4. Passwords remain in `.env` file for security

**Important:** After changing database settings, you may need to restart the API server for changes to take effect.

---

## Paths Tab

Configure file system directories for document input and output.

### Directory Settings

| Setting | Description | Requirements |
|---------|-------------|--------------|
| **Input Directory** | Where VulcanLab looks for documents to import | Must be absolute path, must exist |
| **Output Directory** | Where VulcanLab saves processed markdown files | Must be absolute path, will be created if needed |

### Absolute vs. Relative Paths

**VulcanLab requires absolute paths** for both directories.

✅ **Valid (Absolute Paths):**
- Linux/Mac: `/home/user/vulcanlab/input`
- Windows: `C:\Users\User\vulcanlab\input`

❌ **Invalid (Relative Paths):**
- `./input` (relative to current directory)
- `../documents` (relative path)
- `input` (no path specified)

### Supported Document Types

Documents placed in the input directory can be:
- PDF files (`.pdf`)
- EPUB files (`.epub`)
- Word documents (`.docx`)
- Text files (`.txt`)
- Markdown files (`.md`)

### Output Structure

Processed documents are saved to the output directory with:
- Sanitized markdown content
- Metadata files (JSON)
- Heading hierarchy information
- Suggested chunk boundaries

### Saving Path Settings

1. Enter absolute paths for input and output directories
2. Click **"Save Paths"**
3. Settings are saved to `vulcanlab.config.json`
4. VulcanLab will validate that paths are absolute before saving

---

## Conversion Tab

Configure document processing and pipeline behavior.

### Token Threshold

**Purpose:** Determines how documents are classified and processed.

**Default:** 15,000 tokens

**How It Works:**
- VulcanLab converts each document to tokens using the selected LLM's tokenizer
- Documents **below** the threshold → "Small Document" → Simple Conversion
- Documents **above** the threshold → "Large Document" → Full Conversion

**Simple Conversion (Small Documents):**
- Faster processing
- Structural chunking based on headings and paragraphs
- No AI-based content analysis
- Suitable for well-structured documents

**Full Conversion (Large Documents):**
- Comprehensive AI-powered parsing
- Hierarchical heading extraction
- Suggested chunk boundaries
- Content structure analysis
- Best for complex academic papers and textbooks

**When to Adjust:**
- **Lower threshold (5,000-10,000):** Process more documents with full conversion for better quality
- **Higher threshold (20,000-30,000):** Process more documents with simple conversion for faster throughput

### Advanced Mode

**Purpose:** Controls visibility of advanced features in the VulcanLab UI.

**Options:**
- **Disabled (Default):** Simplified interface, shows only essential features
- **Enabled:** Shows advanced features like manual chunking, detailed metadata editing, and pipeline controls

**What Changes When Enabled:**
- Advanced navigation items appear
- Additional document metadata fields are shown
- Manual override controls become available
- Detailed pipeline status and logs are visible

**When to Enable:**
- You need fine-grained control over document processing
- You want to manually adjust chunk boundaries
- You're debugging or optimizing the pipeline
- You're an advanced user familiar with VulcanLab's internals

### Use Full Model for Simple Conversion

**Purpose:** Controls which LLM tier is used during simple conversion.

**Options:**
- **Disabled (Default):** Use light/fast models for simple conversion
- **Enabled:** Use full/powerful models for simple conversion

**Impact:**

*When Disabled:*
- Simple conversion uses light models (e.g., `gpt-4o-mini`, `gemini-flash-latest`)
- Faster processing
- Lower API costs
- Suitable for well-structured, straightforward documents

*When Enabled:*
- Simple conversion uses full models (e.g., `gpt-4o`, `gemini-2.5-pro`)
- Slower processing
- Higher API costs
- Better quality for complex or poorly structured documents

**When to Enable:**
- Simple conversion results are not meeting quality expectations
- Documents have unusual or complex structure
- You need maximum accuracy even for smaller documents
- API cost is not a concern

### Saving Conversion Settings

All conversion settings are saved automatically:
- Token threshold saves when you click out of the input field
- Toggle settings (Advanced Mode, Use Full Model) save immediately when changed
- Settings are stored in `vulcanlab.config.json`

---

## Templates Tab

Manage prompt templates used throughout VulcanLab's AI operations.

### What Are Templates?

Templates are reusable prompt structures that VulcanLab uses to interact with LLMs. Each template defines:
- System instructions
- Variable placeholders
- Output format expectations
- Task-specific guidance

### Template Functions

VulcanLab uses templates for four main functions:

#### 1. Query Expansion (`query_expansion`)
**Purpose:** Expand user queries into multiple variations for better retrieval.

**Variables:**
- `{query}` - Original user query
- `{intent}` - Classified intent (DEFINITION, MECHANISM, etc.)
- `{entities}` - Extracted entities from the query

**Example Use:**
- User query: "What is CBT?"
- Expanded: "What is cognitive behavioral therapy?", "CBT definition", "How does CBT work?"

#### 2. RAG Augmentation (`rag_augmentation`)
**Purpose:** Generate the final prompt sent to the LLM with retrieved context.

**Variables:**
- `{query}` - User's question
- `{intent}` - Question intent
- `{entities}` - Extracted entities
- `{context}` - Retrieved and formatted document chunks with citations
- `{citation_format}` - Citation style instructions

**Example Use:**
- Combines user question with relevant document excerpts
- Adds citation requirements and evidence policy
- Formats for optimal LLM response

#### 3. Vectorization Suggestions (`vectorization_suggestions`)
**Purpose:** Generate suggestions for which documents or sections to vectorize.

**Variables:**
- Document metadata
- Content preview
- User preferences

**Example Use:**
- Helps users decide what content is most valuable to process
- Prioritizes high-value documents for vectorization

#### 4. Heading Hierarchy (`heading_hierarchy`)
**Purpose:** Extract and structure document headings during full conversion.

**Variables:**
- `{content}` - Document content
- `{title}` - Document title
- `{context}` - Additional context

**Example Use:**
- Analyzes document structure
- Identifies hierarchical relationships
- Generates properly nested heading tree

### Template Versioning

Each template function can have multiple versions:
- **Active Version** - Currently used by the system (marked with ✅)
- **Inactive Versions** - Historical or alternative templates for testing

### Managing Templates

#### View All Templates
1. Navigate to **Settings → Templates** tab
2. See list of all template functions
3. Click **"View"** to see versions for a specific function

#### Create New Template Version
1. Select a template function
2. Click **"New Version"** or navigate to template editor
3. Enter template title and content
4. Use variable placeholders (e.g., `{query}`, `{context}`)
5. Click **"Create"** or **"Save"**

#### Edit Existing Template
1. Select a template function and version
2. Click **"Edit"**
3. Update title or content
4. Click **"Update"**

#### Activate a Template Version
1. Select the version you want to activate
2. Click **"Activate"**
3. This version becomes the active template for that function
4. Previous active version becomes inactive

### Template Best Practices

**Clear Instructions:**
- Be explicit about expected output format
- Provide examples when possible
- Define success criteria

**Variable Usage:**
- Always include required variables for the function
- Use descriptive variable names
- Document what each variable contains

**Testing:**
- Create a new version for testing instead of editing the active template
- Test thoroughly before activating
- Keep previous working version as backup

**Documentation:**
- Use descriptive titles (e.g., "RAG Augmentation v2 - Enhanced Citation")
- Document changes and rationale
- Keep metadata about when and why each version was created

---

## Configuration Storage

VulcanLab stores settings in two locations:

### 1. Configuration File (`vulcanlab.config.json`)

**Location:** Project root directory

**Stored Settings:**
- Database connection parameters (except passwords)
- LLM provider and model selections
- File system paths
- Conversion settings (token threshold, advanced mode, full model usage)
- Logging configuration

**Format:** JSON
```json
{
  "database": {
    "admin_user": "postgres",
    "host": "127.0.0.1",
    "port": 5432,
    "db_name": "vulcanlab",
    "app_user": "vulcanlab_app_user"
  },
  "llm": {
    "provider": "gemini",
    "models": {
      "openai": {
        "light": "gpt-4o-mini",
        "full": "gpt-4o"
      },
      "gemini": {
        "light": "gemini-flash-latest",
        "full": "gemini-2.5-pro"
      }
    }
  },
  "paths": {
    "input_dir": "/absolute/path/to/input",
    "output_dir": "/absolute/path/to/output"
  },
  "conversion": {
    "token_threshold": 15000,
    "advanced_mode_enabled": false,
    "use_full_model": false
  },
  "logging": {
    "enabled": false,
    "log_dir": "logs"
  }
}
```

### 2. Database (PostgreSQL)

**Stored Settings:**
- RAG configuration presets
- Prompt templates and versions
- Template activation status

**Advantages:**
- Multi-user support
- Version history
- Transactional updates
- Easier preset management

---

## Environment Variables (`.env`)

Sensitive credentials are stored in `.env` file, **not** in `vulcanlab.config.json`:

```bash
# Database passwords
POSTGRES_ADMIN_PASSWORD=your_admin_password
POSTGRES_PASSWORD=your_app_password

# API keys
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Other sensitive data
SECRET_KEY=...
```

**Security Note:** Never commit `.env` to version control. Use `.env.example` as a template.

---

## API Endpoints

All settings are accessible via REST API for programmatic access:

### Application Settings
- `GET /settings/` - Get all settings
- `GET /settings/database` - Get database config
- `PUT /settings/database` - Update database config
- `GET /settings/llm` - Get LLM config
- `PUT /settings/llm` - Update LLM config
- `GET /settings/paths` - Get paths config
- `PUT /settings/paths` - Update paths config

### Conversion Settings
- `GET /api/conversion/settings` - Get conversion settings
- `PUT /api/conversion/settings` - Update conversion settings

### Templates
- `GET /settings/templates/` - List all template functions
- `GET /settings/templates/{function}/` - Get all versions for function
- `GET /settings/templates/{function}/{version}` - Get specific version
- `POST /settings/templates/{function}/` - Create new version
- `PUT /settings/templates/{function}/{version}` - Update version
- `PUT /settings/templates/{function}/{version}/activate` - Activate version

---

## Troubleshooting

### Database Connection Issues

**Symptom:** Health checks fail on connection test

**Solutions:**
1. Verify database is running: `sudo systemctl status postgresql`
2. Check host and port settings are correct
3. Verify passwords in `.env` match database users
4. Check firewall allows connection to database port
5. Test connection manually: `psql -h HOST -p PORT -U USER -d DATABASE`

### Path Validation Errors

**Symptom:** "Path must be absolute" error when saving paths

**Solutions:**
1. Use full absolute paths (e.g., `/home/user/input` not `./input`)
2. On Windows, use format `C:\path\to\directory`
3. Ensure no trailing slashes (may cause issues on some systems)

### Model Not Found Errors

**Symptom:** API errors about invalid model names

**Solutions:**
1. Verify model name is exactly correct (case-sensitive)
2. Check your API key has access to the specified model
3. Ensure provider is set correctly (OpenAI vs. Gemini)
4. Test model name directly with provider's API documentation

### Template Rendering Issues

**Symptom:** Template variables not being replaced

**Solutions:**
1. Verify variable names match exactly (e.g., `{query}` not `{Query}`)
2. Check all required variables are present in template
3. Review template syntax for typos
4. Test with a minimal template first

---

## Best Practices

### General Configuration

1. **Backup Configuration:** Keep backups of `vulcanlab.config.json` before major changes
2. **Document Changes:** Maintain notes about why settings were changed
3. **Test in Development:** Test configuration changes in development before production
4. **Use Version Control:** Track configuration file in git (but not `.env`)

### Database Settings

1. **Use Strong Passwords:** Ensure both admin and app user have strong, unique passwords
2. **Separate Users:** Never use admin user for regular application operations
3. **Regular Backups:** Back up PostgreSQL database regularly
4. **Connection Pooling:** For production, consider using pgBouncer for connection pooling

### Model Selection

1. **Balance Cost and Quality:** Use light models where appropriate to reduce API costs
2. **Monitor Usage:** Track API usage to avoid unexpected bills
3. **Test Model Changes:** Verify model changes don't degrade output quality
4. **Keep Fallbacks:** Document which models work well as alternatives

### Paths Configuration

1. **Use Absolute Paths:** Always use absolute paths to avoid confusion
2. **Sufficient Space:** Ensure output directory has enough disk space
3. **Permissions:** Verify application has read/write access to directories
4. **Organize Input:** Keep input directory organized by document type or project

### Templates

1. **Version Everything:** Create new versions instead of overwriting
2. **Test Before Activating:** Thoroughly test new templates before making them active
3. **Document Variables:** Comment what each variable is expected to contain
4. **Keep Simple:** Start with simple templates and add complexity as needed

---

## Summary

VulcanLab's settings system provides comprehensive control over:
- **Database connectivity** and health
- **LLM provider and model selection** for different tasks
- **File system paths** for input and output
- **Document processing** thresholds and modes
- **Prompt templates** for AI interactions

All settings are easily accessible through the Settings page UI or via REST API for programmatic access. Settings are stored securely with sensitive credentials in `.env` and non-sensitive configuration in `vulcanlab.config.json` or the database.

For RAG-specific settings, see the [RAG Settings Guide](rag-settings-guide.md).
