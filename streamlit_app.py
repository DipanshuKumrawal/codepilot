import os
import sys
from collections import Counter
from pathlib import Path

import streamlit as st

# Project root = folder containing this file
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config import api_key_configured, get_model_name
from app.graph.workflow import build_graph
from app.ingestion.pipeline import index_repository, delete_index
from app.ingestion.vectorstore import vectorstore_exists
from app.tools.code_tools import create_diff, apply_change, undo_change
from app.tools.file_tools import list_repository_files, search_text
from app.tools.test_tools import run_tests

st.set_page_config(page_title="CodePilot", page_icon="🤖", layout="wide")

# ------------------------------------------------------------------
# Styling
# ------------------------------------------------------------------
st.markdown(
    """
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
.hero {
  padding: 1.2rem 1.6rem; border-radius: 14px; margin-bottom: 1rem;
  background: linear-gradient(135deg,#4f46e5 0%,#7c3aed 55%,#06b6d4 100%);
  color: white;
}
.hero h1 {margin: 0; font-size: 2rem; color: white;}
.hero p {margin: .2rem 0 0; opacity: .9;}
.badge {
  display:inline-block; padding:2px 10px; border-radius:999px;
  font-size:.75rem; font-weight:600; background:#eef2ff; color:#4338ca;
  margin-right:6px;
}
.stButton>button {border-radius: 10px;}
[data-testid="stMetricValue"] {font-size: 1.5rem;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
  <h1>🤖 CodePilot</h1>
  <p>AI software-engineering agent: search, debug, test, document and
  safely edit your codebase.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------
defaults = {
    "repo_path": None,
    "indexed": False,
    "messages": [],       # {"role","content","intent","sources"}
    "pending_change": None,
    "last_stats": None,
    "queued_question": None,
    "test_output": None,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

EXAMPLES = [
    "Explain the architecture of this project.",
    "Where is authentication implemented?",
    "Generate unit tests for the main module.",
    "Write documentation for the core functions.",
]


def prepare_repo(repo_type, repo_input, force=False):
    if repo_type == "GitHub":
        from app.tools.git_tools import clone_repository
        repo_path = clone_repository(repo_input.strip())
    else:
        repo_path = os.path.abspath(os.path.expanduser(repo_input.strip()))

    if not os.path.isdir(repo_path):
        raise ValueError("Repository path does not exist or is not a folder.")

    stats = index_repository(repo_path, force=force)
    return repo_path, stats


def activate(repo_path, stats):
    st.session_state.repo_path = repo_path
    st.session_state.indexed = True
    st.session_state.messages = []
    st.session_state.pending_change = None
    st.session_state.test_output = None
    st.session_state.last_stats = stats


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.header("📂 Repository")

    repo_type = st.radio("Source", ["Local", "GitHub"], horizontal=True)
    repo_input = st.text_input(
        "Local path" if repo_type == "Local" else "GitHub URL",
        placeholder="/Users/me/projects/myapp"
        if repo_type == "Local"
        else "https://github.com/user/repo.git",
    )

    c1, c2 = st.columns(2)
    index_clicked = c1.button("🚀 Index", use_container_width=True)
    reindex_clicked = c2.button(
        "🔄 Re-index", use_container_width=True,
        help="Delete the existing index and rebuild it.",
    )

    if index_clicked or reindex_clicked:
        if not repo_input:
            st.error("Please enter a repository.")
        else:
            try:
                with st.spinner("Indexing repository..."):
                    path, stats = prepare_repo(
                        repo_type, repo_input, force=reindex_clicked
                    )
                activate(path, stats)
                st.success("Repository ready!")
            except Exception as e:
                st.error(f"Indexing failed: {e}")

    st.divider()
    if st.session_state.indexed:
        st.success("🟢 Repository ready")
        st.caption(st.session_state.repo_path)
        stats = st.session_state.last_stats or {}
        if stats.get("files"):
            m1, m2 = st.columns(2)
            m1.metric("Files", stats["files"])
            m2.metric("Chunks", stats["chunks"])
        elif stats:
            st.caption("Using existing index.")
        if st.button("🗑️ Delete index", use_container_width=True):
            delete_index(st.session_state.repo_path)
            st.session_state.indexed = False
            st.rerun()
    else:
        st.warning("🟡 No repository indexed")

    st.divider()
    st.subheader("⚙️ Session")
    st.caption(f"Model: `{get_model_name()}`")
    if not api_key_configured():
        st.error("GROQ_API_KEY missing in .env")
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.session_state.messages:
        transcript = "\n\n".join(
            f"**{m['role'].title()}**: {m['content']}"
            for m in st.session_state.messages
        )
        st.download_button(
            "⬇️ Export chat (.md)", transcript,
            file_name="codepilot_chat.md", use_container_width=True,
        )

# ------------------------------------------------------------------
# Helpers for tabs
# ------------------------------------------------------------------
repo = st.session_state.repo_path
ready = st.session_state.indexed and repo


def render_pending_change():
    change = st.session_state.pending_change
    if not change:
        return

    st.subheader("📋 Proposed code change")
    label = "new file" if change.get("is_new") else "modified"
    st.markdown(
        f"`{change['file']}` &nbsp; <span class='badge'>{label}</span>"
        f"<span class='badge'>+{change.get('added', 0)}</span>"
        f"<span class='badge'>-{change.get('removed', 0)}</span>",
        unsafe_allow_html=True,
    )
    if change["diff"]:
        st.code(change["diff"], language="diff")
    else:
        st.info("No differences from the current file.")

    a, b = st.columns(2)
    if a.button("✅ Approve & apply", key="approve", use_container_width=True):
        if apply_change(repo, change["file"], change["new_content"]):
            st.session_state.pending_change = None
            st.session_state.applied_file = change["file"]
            st.rerun()
        else:
            st.error("Failed to apply change.")
    if b.button("❌ Reject", key="reject", use_container_width=True):
        st.session_state.pending_change = None
        st.rerun()


def propose_from_agent(raw):
    """Turn an agent proposal into a reviewable change."""
    if not raw:
        return
    diff = create_diff(repo, raw["file"], raw["new_content"])
    if diff["success"]:
        st.session_state.pending_change = diff


def run_question(question):
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]
    try:
        result = build_graph().invoke({
            "question": question,
            "repo_path": repo,
            "intent": "",
            "retrieved_documents": [],
            "analysis": "",
            "final_answer": "",
            "messages": history,
            "attempts": 0,
            "test_code": "",
            "test_result": {},
            "test_feedback": "",
            "pending_change": {},
        })
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ Something went wrong: `{e}`",
            "intent": "error", "sources": [],
        })
        return

    sources = sorted({
        os.path.relpath(d["path"], repo) if d.get("path") and
        os.path.isabs(d["path"]) and d["path"].startswith(repo)
        else d.get("path")
        for d in result.get("retrieved_documents", []) if d.get("path")
    })
    st.session_state.messages.append({
        "role": "assistant",
        "content": result.get("final_answer", "No answer generated."),
        "intent": result.get("intent", ""),
        "sources": sources,
    })
    propose_from_agent(result.get("pending_change"))


# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab_chat, tab_explore, tab_change, tab_tests = st.tabs(
    ["💬 Chat", "🗂️ Explorer", "🛠️ Code changes", "🧪 Tests"]
)

# ---- Chat ---------------------------------------------------------
with tab_chat:
    if not st.session_state.messages:
        st.markdown("##### Try asking")
        cols = st.columns(2)
        for i, ex in enumerate(EXAMPLES):
            if cols[i % 2].button(ex, key=f"ex{i}", use_container_width=True):
                if ready:
                    st.session_state.queued_question = ex
                    st.rerun()
                else:
                    st.warning("Index a repository first.")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if m.get("intent") and m["role"] == "assistant":
                st.markdown(
                    f"<span class='badge'>{m['intent']}</span>",
                    unsafe_allow_html=True,
                )
            st.markdown(m["content"])
            if m.get("sources"):
                with st.expander(f"📎 Sources ({len(m['sources'])})"):
                    for s in m["sources"]:
                        st.markdown(f"- `{s}`")

    if st.session_state.pending_change:
        st.divider()
        render_pending_change()

question = st.chat_input("Ask something about your codebase...")
if st.session_state.queued_question:
    question = st.session_state.queued_question
    st.session_state.queued_question = None

if question:
    if not ready:
        st.error("Please index a repository first.")
    elif not vectorstore_exists(repo):
        st.error("Vector store is missing. Please re-index the repository.")
    elif not api_key_configured():
        st.error("GROQ_API_KEY is not set in .env.")
    else:
        with st.spinner("CodePilot is thinking..."):
            run_question(question)
        st.rerun()

# ---- Explorer -----------------------------------------------------
with tab_explore:
    if not ready:
        st.info("Index a repository to explore it.")
    else:
        files = list_repository_files(repo)
        exts = Counter(Path(f).suffix or "(none)" for f in files)
        m1, m2, m3 = st.columns(3)
        m1.metric("Files", len(files))
        m2.metric("Languages / types", len(exts))
        m3.metric("Top type", exts.most_common(1)[0][0] if exts else "-")
        if exts:
            st.bar_chart(dict(exts.most_common(10)))

        left, right = st.columns([1, 2])
        with left:
            st.markdown("**Search in files**")
            q = st.text_input("Text to find", key="search_q",
                              label_visibility="collapsed",
                              placeholder="Search text...")
            if q:
                hits = search_text(repo, q)
                st.caption(f"{len(hits)} match(es)")
                for f, no, line in hits:
                    st.markdown(f"`{f}:{no}`  \n{line}")
        with right:
            if files:
                choice = st.selectbox("Open file", files)
                text = (Path(repo) / choice).read_text(
                    encoding="utf-8", errors="ignore"
                )
                st.caption(f"{len(text.splitlines())} lines")
                st.code(text, language=Path(choice).suffix.lstrip(".") or None)

# ---- Code changes -------------------------------------------------
with tab_change:
    if not ready:
        st.info("Index a repository first.")
    else:
        if st.session_state.get("applied_file"):
            st.success(f"Applied change to `{st.session_state.applied_file}`.")
        st.markdown(
            "Propose an edit manually (or let the Debug agent propose one in "
            "chat). Every change is shown as a diff and needs your approval. "
            "A `.bak` backup is kept so you can undo."
        )
        files = list_repository_files(repo)
        target = st.selectbox(
            "File to modify (or type a new path below)", [""] + files
        )
        new_path = st.text_input("…or new file path", placeholder="utils/new.py")
        file_name = new_path.strip() or target
        current = ""
        if target and not new_path.strip():
            current = (Path(repo) / target).read_text(
                encoding="utf-8", errors="ignore"
            )
        new_code = st.text_area(
            "Proposed content", value=current, height=280,
            key=f"code_{file_name}",
        )
        if st.button("🔍 Review change"):
            if not file_name:
                st.warning("Select or enter a file path.")
            else:
                res = create_diff(repo, file_name, new_code)
                if res["success"]:
                    st.session_state.pending_change = res
                    st.session_state.applied_file = None
                else:
                    st.error(res["message"])

        if st.session_state.pending_change:
            st.divider()
            render_pending_change()

        st.divider()
        u_file = st.selectbox("Undo last change for", [""] + files, key="undo")
        if st.button("↩️ Undo (restore .bak)") and u_file:
            if undo_change(repo, u_file):
                st.success(f"Restored `{u_file}`.")
            else:
                st.warning("No backup found for that file.")

# ---- Tests --------------------------------------------------------
with tab_tests:
    if not ready:
        st.info("Index a repository first.")
    else:
        st.markdown("Run the repository's `pytest` suite.")
        if st.button("▶️ Run pytest"):
            with st.spinner("Running tests..."):
                st.session_state.test_output = run_tests(repo)
        out = st.session_state.test_output
        if out:
            if out["return_code"] == 0:
                st.success("All tests passed ✅")
            else:
                st.error(f"Tests failed (exit code {out['return_code']})")
            st.code(out["stdout"] or "(no output)")
            if out["stderr"]:
                st.code(out["stderr"])
