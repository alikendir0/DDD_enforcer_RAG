# Feature Specification: Advanced Statistics and Configuration Panel

**Branch**: `002-advanced-stats-config` | **Date**: 2025-12-01
**Status**: Draft

## Overview

Enhance the RAG chatbot interface with advanced analytics, configuration controls, and file management capabilities. Users need transparency into system resource usage, costs, and the ability to fine-tune retrieval parameters without code changes. Power users require visibility into which documents and chunks influence each response, while all users need a simple way to manage their document corpus through the interface.

## User Scenarios & Testing

### User Story 1: Monitoring System Usage and Costs (P1)

**As a** chatbot user
**I want to** view detailed statistics about token usage, costs, and indexed documents
**So that** I can understand resource consumption and make informed decisions about usage

**Acceptance Criteria**:

- Users can toggle a statistics panel that displays:
  - Total tokens used (input and output separately)
  - Estimated cost based on current model
  - Number of files currently embedded
  - Total number of chunks in the vector database
  - Average tokens per query
  - Total queries processed in session
- Statistics update in real-time as queries are processed
- Cost estimates accurately reflect the pricing of the selected AI model
- Panel can be shown/hidden without losing data

**Testing Scenarios**:

```gherkin
Scenario: View comprehensive usage statistics
  Given I am using the chatbot interface
  When I click the "Statistics" button
  Then I see a panel displaying token counts, cost estimates, file counts, and chunk counts
  And the statistics reflect my current session usage

Scenario: Statistics update after queries
  Given the statistics panel is visible
  When I submit a new query and receive a response
  Then the token count increases by the tokens used in that exchange
  And the cost estimate updates accordingly
  And the query counter increments

Scenario: Toggle statistics visibility
  Given the statistics panel is open
  When I click the close button
  Then the panel hides but retains all statistical data
  When I reopen the panel
  Then all previous statistics are still displayed
```

### User Story 2: Configuring Retrieval Parameters (P1)

**As a** power user
**I want to** adjust RAG parameters like top-k, chunk size, and overlap
**So that** I can optimize retrieval quality for my specific use case

**Acceptance Criteria**:

- Users can access a configuration menu with the following adjustable parameters:
  - Top-K: Number of chunks to retrieve per query (range: 1-10, default: 3)
  - Chunk Size: Token count per chunk (range: 256-1024, default: 512)
  - Chunk Overlap: Overlapping tokens between chunks (range: 0-256, default: 0)
- Changes to configuration take effect for subsequent queries
- Configuration includes helpful descriptions of each parameter's impact
- Invalid values are prevented with clear validation messages
- Users can reset to default values with one action

**Testing Scenarios**:

```gherkin
Scenario: Adjust top-k retrieval count
  Given I open the configuration menu
  When I change top-k from 3 to 5
  And I submit a new query
  Then the system retrieves 5 chunks instead of 3
  And the response reflects information from all 5 chunks

Scenario: Modify chunk size
  Given I am in the configuration menu
  When I change chunk size from 512 to 256 tokens
  And I click "Apply"
  Then I see a message that I need to re-index documents for this change
  And the new chunk size is saved for future indexing

Scenario: Invalid configuration values
  Given I am adjusting configuration
  When I enter a top-k value of 15 (exceeds maximum of 10)
  Then I see an error message "Top-K must be between 1 and 10"
  And the invalid value is not saved

Scenario: Reset to defaults
  Given I have modified multiple configuration parameters
  When I click "Reset to Defaults"
  Then all parameters return to their original default values
  And a confirmation message appears
```

### User Story 3: Inspecting Retrieval Context (P2)

**As a** user seeking to understand response sources
**I want to** see which document chunks were used to generate each response
**So that** I can verify information accuracy and understand the AI's reasoning

**Acceptance Criteria**:

- Users can toggle "Show Context" for any response
- When enabled, each response displays:
  - Which documents contributed chunks
  - The specific chunk text that was retrieved
  - Similarity scores for each chunk
  - Chunk metadata (document name, chunk index, token count)
- Context information is formatted clearly and doesn't interfere with reading the response
- Users can expand/collapse individual chunk details
- Context toggle state persists across queries in the same session

**Testing Scenarios**:

```gherkin
Scenario: View retrieval context for a response
  Given I have received a response to my query
  When I toggle "Show Context" for that response
  Then I see a list of retrieved chunks with their source documents
  And each chunk shows its similarity score
  And I can see the actual text content of each chunk

Scenario: Expand chunk details
  Given context is visible for a response
  When I click on a specific chunk
  Then the full chunk text expands
  And I see metadata including document name, chunk index, and token count

Scenario: Context toggle persistence
  Given I have enabled "Show Context"
  When I submit a new query
  Then the new response also displays context automatically
  Until I toggle it off again
```

### User Story 4: Managing Document Files (P1)

**As a** chatbot administrator
**I want to** view, upload, and manage documents through the interface
**So that** I don't need file system access to update the knowledge base

**Acceptance Criteria**:

- Users can view a list of all documents in the data/documents folder
- The list shows for each file:
  - Filename
  - File type (PDF, TXT, MD, DOCX)
  - File size
  - Embedding status (embedded/not embedded)
  - Last modified date
- Users can upload new documents directly through the interface
- Supported file types are validated before upload
- After upload, users can trigger re-indexing to embed new files
- Users can see which files are currently embedded in the active index
- File upload progress is displayed for large files

**Testing Scenarios**:

```gherkin
Scenario: View existing documents
  Given I am on the file management page
  When the page loads
  Then I see a table of all documents in data/documents
  And each row shows filename, type, size, embedding status, and last modified date

Scenario: Upload a new document
  Given I am on the file management page
  When I click "Upload Document"
  And I select a valid PDF file
  Then the file uploads successfully
  And appears in the document list with status "Not Embedded"
  And I see a prompt to re-index documents

Scenario: Upload invalid file type
  Given I am uploading a document
  When I select a file with extension .exe
  Then I see an error "Unsupported file type. Please upload PDF, TXT, MD, or DOCX files"
  And the file is not uploaded

Scenario: Identify embedded vs non-embedded files
  Given there are 5 documents in the folder
  And only 3 have been indexed
  When I view the file list
  Then 3 files show status "Embedded"
  And 2 files show status "Not Embedded"
  And embedded files are visually distinguished (e.g., with a checkmark icon)
```

## Functional Requirements

### Statistics Panel (FR-SP)

**FR-SP-001**: System SHALL provide a toggleable statistics panel accessible from the main interface
**FR-SP-002**: Panel SHALL display real-time token usage broken down by input tokens and output tokens
**FR-SP-003**: Panel SHALL calculate and display estimated cost based on the current AI model's pricing
**FR-SP-004**: Panel SHALL show the count of files currently embedded in the vector database
**FR-SP-005**: Panel SHALL show the total number of chunks stored in the vector database
**FR-SP-006**: Panel SHALL track and display average tokens per query for the current session
**FR-SP-007**: Panel SHALL count and display total queries processed in the current session
**FR-SP-008**: Statistics SHALL persist when panel is toggled closed and reopened
**FR-SP-009**: Statistics SHALL reset when user starts a new session

**Assumptions**:
- Session is defined as the browser tab's lifetime
- Model pricing is configured in application settings
- Token counting uses the same method as the AI API

### Configuration Menu (FR-CM)

**FR-CM-001**: System SHALL provide a configuration menu for adjusting RAG parameters
**FR-CM-002**: Menu SHALL allow setting top-k value between 1 and 10 (inclusive)
**FR-CM-003**: Menu SHALL allow setting chunk size between 256 and 1024 tokens (inclusive)
**FR-CM-004**: Menu SHALL allow setting chunk overlap between 0 and 256 tokens (inclusive)
**FR-CM-005**: System SHALL validate all parameter values and reject invalid inputs with descriptive error messages
**FR-CM-006**: Top-k changes SHALL apply immediately to subsequent queries
**FR-CM-007**: Chunk size and overlap changes SHALL display a notification that re-indexing is required
**FR-CM-008**: Menu SHALL provide descriptions explaining the impact of each parameter
**FR-CM-009**: Menu SHALL include a "Reset to Defaults" button that restores original values
**FR-CM-010**: Configuration changes SHALL be saved to browser storage and persist across sessions

**Assumptions**:
- Default values: top-k=3, chunk-size=512, overlap=0
- Re-indexing is a manual operation triggered by the user
- Browser localStorage is available for persisting settings

### Context Visibility (FR-CV)

**FR-CV-001**: System SHALL provide a toggle control for showing/hiding retrieval context on responses
**FR-CV-002**: When enabled, responses SHALL display the source documents that contributed chunks
**FR-CV-003**: System SHALL show the actual text content of each retrieved chunk
**FR-CV-004**: Each chunk SHALL display its similarity score
**FR-CV-005**: Chunk metadata SHALL include document name, chunk index within document, and token count
**FR-CV-006**: Chunks SHALL be expandable/collapsible to manage screen space
**FR-CV-007**: Context toggle state SHALL persist for the duration of the session
**FR-CV-008**: Context information SHALL be formatted to remain readable and not obstruct the response text

**Assumptions**:
- Similarity scores are normalized between 0 and 1
- Chunk index starts at 0 for the first chunk in each document
- Session persistence uses browser state

### File Management (FR-FM)

**FR-FM-001**: System SHALL display a list of all files in the data/documents directory
**FR-FM-002**: File list SHALL show filename, file type, file size, embedding status, and last modified date for each file
**FR-FM-003**: System SHALL allow users to upload new documents through a file selection dialog
**FR-FM-004**: System SHALL validate uploaded file types and only accept PDF, TXT, MD, and DOCX formats
**FR-FM-005**: System SHALL reject files exceeding a maximum size limit with a clear error message
**FR-FM-006**: System SHALL display upload progress for files being uploaded
**FR-FM-007**: After successful upload, system SHALL update the file list to include the new document
**FR-FM-008**: System SHALL indicate which files are currently embedded in the vector database
**FR-FM-009**: System SHALL allow users to trigger document re-indexing from the file management interface
**FR-FM-010**: Non-embedded files SHALL be visually distinguished from embedded files

**Assumptions**:
- Maximum file size: 50MB per file
- File list refreshes automatically after upload
- Embedding status is determined by checking if chunks from that file exist in the vector database
- Users cannot delete files through the interface (safety consideration)

## Success Criteria

**SC-001 - Usage Transparency**: Users can view comprehensive resource usage statistics within 2 clicks, including token consumption and cost estimates

**SC-002 - Parameter Control**: Power users can adjust retrieval parameters and see the effects on subsequent queries without requiring application restart

**SC-003 - Source Verification**: Users viewing response context can identify the exact document passages that influenced the AI's answer within 1 click per response

**SC-004 - Self-Service File Management**: Users can upload new documents and update the knowledge base without needing file system access or technical assistance

**SC-005 - Configuration Persistence**: User configuration changes persist across browser sessions, maintaining customized settings

**SC-006 - Real-Time Feedback**: Statistics update immediately after each query, providing live feedback on resource consumption

**SC-007 - Usability**: 90% of users can successfully adjust RAG parameters and understand their impact without external documentation

## Assumptions

1. **Browser Environment**: Users access the chatbot through a modern web browser with JavaScript enabled and localStorage available
2. **File System Access**: The application has read/write access to the data/documents directory on the server
3. **Model Pricing Data**: AI model pricing information is configured in the application and kept up-to-date
4. **Session Definition**: A session is defined as a single browser tab's lifetime; closing/refreshing the tab starts a new session
5. **Re-indexing Workflow**: Users understand that changing chunk size or overlap requires manual re-indexing of documents
6. **Token Counting**: Token counting uses the same tokenizer as the AI model to ensure accuracy
7. **File Upload Security**: File uploads are scanned for security threats (not specified in this feature, assumed to be handled by existing infrastructure)
8. **Single User Context**: The application is designed for single-user or per-session usage; statistics and configuration are not shared across users

## Dependencies

1. **Existing RAG System**: This feature extends the current RAG chatbot and depends on the existing document indexing, chunking, embedding, and retrieval systems
2. **AI Model API**: Token counting and cost calculations depend on the AI provider's API documentation for token counting methodology and pricing structure
3. **File Storage**: File management functionality depends on server-side file system access to the data/documents directory
4. **Browser Storage API**: Configuration persistence and statistics tracking rely on browser localStorage or sessionStorage APIs

## Out of Scope

1. **Multi-User Statistics**: Aggregated statistics across multiple users or sessions
2. **Historical Analytics**: Long-term tracking of usage patterns beyond the current session
3. **File Deletion**: Ability to delete documents through the interface (safety/security consideration)
4. **Advanced File Management**: Features like file renaming, folder organization, or version control
5. **Automated Re-indexing**: Automatic re-indexing when files are uploaded or configuration changes
6. **Cost Alerts**: Notifications or limits when usage exceeds certain cost thresholds
7. **A/B Testing**: Built-in functionality to compare different parameter configurations
8. **Export Functionality**: Exporting statistics or configuration to external files
9. **Chunk Editing**: Modifying chunk content or boundaries through the interface
10. **Model Selection**: Changing which AI model is used for generation

## Key Entities

### Statistic
- **Attributes**:
  - session_id (identifier for the current session)
  - total_input_tokens (cumulative count)
  - total_output_tokens (cumulative count)
  - total_cost (calculated estimate)
  - query_count (number of queries processed)
  - average_tokens_per_query (computed metric)
  - embedded_file_count (current count from database)
  - total_chunk_count (current count from database)
  - timestamp_created (session start time)
  - timestamp_updated (last update time)

### Configuration
- **Attributes**:
  - user_id (browser/session identifier)
  - top_k (integer, 1-10)
  - chunk_size (integer, 256-1024)
  - chunk_overlap (integer, 0-256)
  - show_context_enabled (boolean toggle state)
  - timestamp_modified (when settings were last changed)

### RetrievalContext
- **Attributes**:
  - query_id (links to specific query)
  - chunks (list of chunk objects)
    - chunk_id
    - document_name
    - chunk_index
    - chunk_text
    - similarity_score
    - token_count
  - retrieval_timestamp

### DocumentFile
- **Attributes**:
  - filename
  - file_path (location in data/documents)
  - file_type (PDF, TXT, MD, DOCX)
  - file_size_bytes
  - is_embedded (boolean status)
  - last_modified (file system timestamp)
  - upload_timestamp (when uploaded through interface)
  - chunk_count (number of chunks if embedded, else 0)

## Edge Cases

1. **Statistics Overflow**: If token counts or query counts exceed display limits (e.g., millions of tokens)
   - **Handling**: Use abbreviated notation (e.g., "1.2M tokens") and provide tooltip with full number

2. **Cost Estimation Unavailable**: Model pricing data is missing or out-of-date
   - **Handling**: Display "Cost estimation unavailable" with explanation and prompt to check pricing configuration

3. **Invalid Configuration Persistence**: localStorage is full or unavailable
   - **Handling**: Fall back to default values, display warning that settings won't persist

4. **Large File Upload**: User attempts to upload a file exceeding the size limit
   - **Handling**: Show error before upload begins, suggest file compression or splitting

5. **Re-indexing During Active Query**: User triggers re-indexing while queries are being processed
   - **Handling**: Queue re-indexing to start after current queries complete, show waiting status

6. **Context for Non-Indexed Query**: User toggles context on a query that didn't use retrieval (empty index)
   - **Handling**: Display message "No document context was used for this response" instead of empty list

7. **File Upload Conflicts**: User uploads a file with the same name as an existing file
   - **Handling**: Prompt user to either replace existing file or rename the new file

8. **Configuration Applied Mid-Session**: Top-k changed after some queries already executed
   - **Handling**: Clearly show in statistics when parameters changed; consider showing "before/after configuration" in statistics

9. **Chunk Overlap Exceeds Chunk Size**: User sets overlap ≥ chunk size
   - **Handling**: Validation prevents this; show error "Overlap must be less than chunk size"

10. **Browser Compatibility**: Older browsers may not support all UI features
    - **Handling**: Detect browser capabilities; gracefully degrade features or show compatibility warning

---

**Specification Version**: 1.0
**Last Updated**: 2025-12-01
**Next Phase**: Run `/speckit.plan` to generate implementation plan
