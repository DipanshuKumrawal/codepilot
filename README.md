# 🤖 CodePilot

CodePilot is an AI software-engineering assistant. Point it at a local folder
or a GitHub repository, then ask questions in plain English. It indexes the
code, routes each question to a specialised agent, and answers using only the
code it retrieved, citing the files it used. It can also propose code edits,
which you review as a diff before anything is written.

**Stack:** Streamlit · LangGraph · LangChain · FAISS · sentence-transformers
(`all-MiniLM-L6-v2`) · Groq (free LLM API) · GitPython · pytest

Feature list: [FEATURES.md](FEATURES.md)

---

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then put your Groq key in .env
streamlit run streamlit_app.py
```

1. Get a free key at <https://console.groq.com/keys>.
2. In the sidebar pick **Local** (folder path) or **GitHub** (repo URL) and click **🚀 Index**.
3. Ask questions in **💬 Chat**.

### Configuration (`.env`)

| Variable | Purpose | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key (required, free) | – |
| `CODEPILOT_MODEL` | Groq model id | `openai/gpt-oss-120b` |
| `CODEPILOT_TEMPERATURE` | Sampling temperature | `0.2` |

Available models differ per account. List yours with
`curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"`.
Restart Streamlit after editing `.env`.

---

## How it works (in detail)

CodePilot is a **RAG (retrieval-augmented generation)** system with an
**agent router**. There are two phases: *indexing* (once per repository) and
*question answering* (every message).

### Phase 1 – Indexing

Triggered by **Index** / **Re-index** in the sidebar
(`app/ingestion/pipeline.py`).

1. **Get the repo.** A local path is used as-is. A GitHub URL is cloned with
   GitPython into `data/repositories/<name>` (`app/tools/git_tools.py`).
2. **Load files** (`loader.py`). Walks the folder and keeps source/text files
   (`.py .js .ts .java .go .rs .md .html .css .json .yaml …`). It skips
   `.git`, `.venv`, `node_modules`, `build`, `dist`, caches, empty files and
   files over 500 KB.
3. **Chunk** (`chunker.py`). Each file is split into ~1200-character pieces
   with 200 characters of overlap, so a function that straddles a boundary
   still appears whole in at least one chunk. Each chunk remembers its path,
   language and chunk number.
4. **Embed.** Every chunk is turned into a vector by the local
   `all-MiniLM-L6-v2` model. This runs on your machine, needs no API key and
   is free. The first run downloads the model.
5. **Store** (`vectorstore.py`). Vectors go into a FAISS index saved under
   `data/vectorstores/<id>/`, where `<id>` is a hash of the repo's absolute
   path. Each repo has its own index, and re-indexing a known repo is skipped
   unless you click **Re-index**.

### Phase 2 – Answering a question

The chat message goes through a **LangGraph** state machine
(`app/graph/workflow.py`). A shared state dict carries the question, repo
path, intent, retrieved chunks, analysis, final answer, chat history, test
code/results and any pending code change (`app/graph/state.py`).

```
                    ┌─► code_search ─► analyze_code ─┐
                    ├─► debugging ───────────────────┤
 question ─► router ┼─► documentation ───────────────┼─► final answer ─► UI
                    ├─► architecture ────────────────┤
                    ├─► general ─────────────────────┘
                    └─► testing ─► run pytest ─┬─ pass/fail ─► final answer
                              ▲                └─ retry (max 2) ┘
                              └──────────────────────────────────
```

1. **Router** (`classify_question`): the LLM reads the question and returns one
   intent: `code_search`, `debugging`, `testing`, `documentation`,
   `architecture` or `general`. An unrecognised reply falls back to
   `code_search`.
2. **Specialist agent**, depending on the intent:
   - **Code search** – semantic search (top 8 chunks), then `analyze_code`
     asks the LLM to explain them using the chat history.
   - **Debugging** – retrieves 8 chunks and asks the LLM for root cause,
     file, explanation, fix and side effects. If it ends its answer with a
     `FILE:` / `FIXED CODE:` block, that is turned into a **proposed change**.
   - **Testing** – retrieves 8 chunks, the LLM writes pytest tests, they are
     saved as `generated_test.py` in the repo and run with pytest. The graph
     loops back to regenerate on failure (at most 2 attempts).
   - **Documentation** – retrieves 8 chunks and writes docs for them.
   - **Architecture** – does not use similarity search. It loads *all* repo
     files and asks the LLM to summarise structure and components.
   - **General** – non-code questions; no retrieval.
3. **Final answer** (`generate_final_answer`): a last LLM call combines the
   analysis, the list of source files and the chat history into the reply.
4. **UI** shows the answer with an intent badge and a collapsible **Sources**
   list. If a code change was proposed, it appears as a diff.

The prompts all tell the model to use only the supplied code and say so when
the context is insufficient, which reduces made-up answers.

### Safe code changes

Whether you type an edit in the **Code changes** tab or the Debugging agent
proposes one:

1. `create_diff` builds a unified diff (new files diff against empty).
2. You see the diff with +/- counts and choose **Approve** or **Reject**.
3. On approve, `apply_change` first saves the original as `<file>.bak`, then
   writes the new content. **Undo** restores the `.bak`.
4. All paths are resolved and must stay inside the repository folder.

### The interface

| Tab | What it does |
|---|---|
| 💬 Chat | Ask questions, example prompts, intent badge, sources, export chat |
| 🗂️ Explorer | File-type chart, text search with line numbers, file viewer |
| 🛠️ Code changes | Edit/create a file, review diff, approve/reject, undo |
| 🧪 Tests | Run the repo's `pytest` and show the output |

The sidebar handles indexing, repository status, model name, delete index and
clearing/exporting the chat.

---

## Project layout

```
streamlit_app.py        Web UI (tabs, session state, chat loop)
main.py                 CLI demo against sample_project/
app/config.py           LLM client (Groq via OpenAI-compatible API)
app/ingestion/          loader → chunker → vectorstore → pipeline
app/graph/              LangGraph state, nodes, workflow
app/agents/             debug, test, architecture, documentation agents
app/tools/              files/search, git clone, diff/apply/undo, pytest
app/prompts/            router, analysis, final-answer prompts
sample_project/         tiny demo codebase
data/                   cloned repos and FAISS indexes (git-ignored)
```

## Limitations

- Quality depends on the chosen free model; small models route and follow
  formats less reliably.
- Answers only see the retrieved chunks (top 8), so very broad questions may
  miss files. The Architecture agent sees everything but can hit the model's
  context limit on large repos.
- Test generation targets Python/pytest. The retry loop regenerates tests but
  does not yet feed the failure output back into the prompt.
- Groq's free tier has rate limits (a 429 means wait a minute).

## Security notes

- Keep `.env` private. It is in `.gitignore`. Rotate any key you pasted into
  chats or screenshots.
- Edits require explicit approval and cannot leave the repository folder.
- Indexing runs locally; only retrieved code snippets and your question are
  sent to the LLM provider.
