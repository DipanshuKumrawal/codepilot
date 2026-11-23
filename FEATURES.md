# CodePilot – Feature Overview

## Core AI capabilities
| Feature | Description |
|---|---|
| Intent routing | An LLM router classifies each question as code search, debugging, testing, documentation, architecture or general. |
| Semantic code search | FAISS + MiniLM embeddings retrieve the most relevant chunks; answers cite their source files. |
| Debugging agent | Explains errors from the code context and can propose a fix as a reviewable change. |
| Test generation | Writes pytest tests, runs them, and retries up to 2 times on failure. |
| Documentation agent | Generates docs/docstrings for the retrieved code. |
| Architecture agent | Summarises the whole project structure and component relationships. |
| Conversation memory | Chat history is passed to the agents for follow-up questions. |

## Repository handling
- Local folders or GitHub URLs (auto-cloned into `data/repositories`)
- Per-repository vector index (cached; **Re-index** and **Delete index** buttons)
- 25+ file types supported; ignores `.venv`, `node_modules`, `.git`, builds, caches and files > 500 KB
- Index statistics (files, chunks)

## Web UI (Streamlit)
- **💬 Chat** – example prompts, intent badges, collapsible source list, error handling, clear/export chat (Markdown)
- **🗂️ Explorer** – file-type chart, full-text search with line numbers, syntax-highlighted file viewer
- **🛠️ Code changes** – pick a file or create a new one, review a coloured diff (+/- counts), approve or reject, **undo** via `.bak`
- **🧪 Tests** – run the repository's pytest suite and view output
- Sidebar status, model name and missing-API-key warning; gradient header and themed styling

## Safety & quality
- Human-in-the-loop approval for every edit
- Path-traversal protection on read/write tools
- Automatic backups with undo
- Configurable model/temperature through environment variables
- Embeddings run locally; only retrieved snippets are sent to the LLM

## Changes made in this revision
- Fixed `streamlit_app.py` project-root bug and agent-proposed changes disappearing on rerun
- Loader no longer skips repos located under a folder named `build`/`dist`; added size limit and more file types
- Vector store path is now independent of the working directory
- Switched LLM provider to the free Groq API (`openai/gpt-oss-120b`); lower default temperature (1 → 0.2); clear error if the key is missing
- Debug prompt now asks for a `FILE:`/`FIXED CODE:` block so fixes become reviewable changes
- Added new-file creation, undo, re-index, search, explorer and test-runner features
- Added `README.md`, `FEATURES.md`, `.env.example`, `.gitignore`

## Ideas for the future
Streaming responses, multi-repo switching, git commit/branch from approved changes, auth for hosted deployment, automated unit tests for CodePilot itself.
