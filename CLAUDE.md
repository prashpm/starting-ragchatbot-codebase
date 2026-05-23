/# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Install dependencies (first time only)
uv sync

# Start the server
./run.sh
# or manually:
cd backend && uv run uvicorn app:app --reload --port 8000
```

Requires a `.env` file in the project root with `ANTHROPIC_API_KEY=...` (see `.env.example`).

The app serves on `http://localhost:8000`. The backend auto-loads all `.txt`, `.pdf`, and `.docx` files from `docs/` on startup.

## Architecture

This is a RAG chatbot: a FastAPI backend with a vanilla JS frontend, served as static files from the same server.

**Request flow for a user query:**
1. `frontend/script.js` — `sendMessage()` POSTs `{ query, session_id }` to `/api/query`
2. `backend/app.py` — `query_documents()` creates/resolves session, delegates to `RAGSystem.query()`
3. `backend/rag_system.py` — `RAGSystem` is the central orchestrator: loads conversation history, calls `AIGenerator`, collects sources, saves the exchange back to session
4. `backend/ai_generator.py` — makes the first Claude API call with the `search_course_content` tool available; if Claude decides to search, `_handle_tool_execution()` runs the tool and makes a second Claude API call to synthesize the final answer
5. `backend/search_tools.py` — `CourseSearchTool.execute()` calls `VectorStore.search()`, tracks sources for the UI
6. `backend/vector_store.py` — `VectorStore` wraps two ChromaDB collections: `course_catalog` (course titles/metadata) and `course_content` (chunked lesson text). Semantic course name resolution happens via vector search on `course_catalog` before filtering `course_content`

**Key design decisions:**
- Claude drives retrieval via tool use (`tool_choice: auto`) rather than a fixed retrieve-then-generate pipeline. One search per query maximum.
- `SessionManager` stores conversation history in memory (not persisted across restarts). History is passed in the system prompt, not as message history.
- Course title is used as the unique ID in ChromaDB — duplicate titles are skipped on ingestion.

## Document Format

Course documents in `docs/` must follow this text format for `DocumentProcessor` to parse them correctly:

```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 1: <lesson title>
Lesson Link: <url>
<lesson content...>

Lesson 2: <lesson title>
...
```

## Key Configuration (`backend/config.py`)

| Setting | Default | Purpose |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Claude model used for generation |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model for ChromaDB |
| `CHUNK_SIZE` | 800 | Max characters per content chunk |
| `CHUNK_OVERLAP` | 100 | Overlap between adjacent chunks |
| `MAX_RESULTS` | 5 | Max chunks returned per vector search |
| `MAX_HISTORY` | 2 | Conversation exchanges kept in session |
| `CHROMA_PATH` | `./chroma_db` | ChromaDB persistence directory (relative to `backend/`) |
