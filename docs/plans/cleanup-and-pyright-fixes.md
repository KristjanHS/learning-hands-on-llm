# Cleanup & Pyright Zero-Error Plan

**Created**: 2026-04-11
**Status**: Draft
**Goal**: Fix all 63 pyright errors (25 own-code + 38 third-party exclusion), resolve open follow-ups, add missing deps.

---

## Phase 1: Exclude Third-Party Code from Pyright (38 errors eliminated)

### Task 1.1: Add pyrightconfig.json

**Why**: 38 of 63 pyright errors came from third-party course material we never modify (since removed from the repo). Keeping pyright on own code only removes noise without hiding real issues.

**Steps**:
1. Create `pyrightconfig.json` at project root:
   ```json
   {
     "pythonVersion": "3.12",
     "venvPath": ".",
     "venv": ".venv"
   }
   ```

**Files to create**: `pyrightconfig.json`

---

## Phase 2: Add Missing Dependencies (17 errors → 0)

### Task 2.1: Add missing packages to pyproject.toml extras

**Why**: 17 own-code pyright errors are `reportMissingImports` for packages that are used in code but not listed in pyproject.toml extras, or listed but not installed because `uv sync` was run without the right extras.

**Missing from extras entirely** (need to add):
- `requests` → phase1 (used by benchm_ollama_*.py, ollama_api_tags.py)
- `httpx` → phase2 (used by qa_loop.py)

**Already in extras but not installed** (just need `uv sync --extra phase2 --extra dev`):
- `langchain-ollama`, `langchain-core`, `ollama` (phase1)
- `weaviate-client`, `langchain`, `langchain-community`, `langchain-nomic`, `langdetect` (phase2)
- `matplotlib`, `pandas` (phase1)

**Steps**:
1. Add `"requests"` to phase1 extras in `pyproject.toml`
2. Add `"httpx"` to phase2 extras in `pyproject.toml`
3. Run `uv lock` to regenerate lockfile
4. Run `uv sync --extra phase2 --extra dev` to install all deps
5. Verify pyright `reportMissingImports` errors are resolved

**Files to modify**: `pyproject.toml`

---

## Phase 3: Fix Code Bugs (4 errors)

### Task 3.1: Fix `any` → `Any` type annotation

**Why**: `phase1/python_code/benchm_ollama_ChatOllama.py:72` uses lowercase `any` (the builtin) as a type annotation instead of `typing.Any`. Pyright correctly flags this.

**Steps**:
1. Change line 72: `def _get_token_counts(response: any)` → `def _get_token_counts(response: Any)`
2. Add `from typing import Any` to imports (or use `object` if `Any` isn't warranted)

**Files to modify**: `phase1/python_code/benchm_ollama_ChatOllama.py`

### Task 3.2: Fix possibly-unbound `response` variable

**Why**: `phase1/python_code/LLava_image-use_colab_ollama.py:37` — if the `try` block at line 32 raises, `response` is never assigned, but line 37 uses it unconditionally.

**Steps**:
1. Read the full context around lines 30-38
2. Add `sys.exit(1)` or `raise` in the except block, or initialize `response` before the try

**Files to modify**: `phase1/python_code/LLava_image-use_colab_ollama.py`

### Task 3.3: Suppress `torch.version.cuda` pyright false positive

**Why**: `phase0/python_scripts/torch_cuda_info.py:10` — `torch.version` is a submodule at runtime but pyright stubs don't expose it. This is a known pyright limitation, not a code bug.

**Steps**:
1. Add `# type: ignore[attr-defined]` to line 10, with a comment explaining why

**Files to modify**: `phase0/python_scripts/torch_cuda_info.py`

### Task 3.4: Fix `plt.xlabel()` type narrowing

**Why**: `phase1/python_code/Pandas_csv_mathplotlib.py` — `df.columns[0]` returns `Hashable`, not `str`. Pyright may flag this depending on pandas stubs.

**Steps**:
1. Check if pyright still flags this after deps are installed (Task 2.1)
2. If so, cast: `plt.xlabel(str(df.columns[0]))`

**Files to modify**: `phase1/python_code/Pandas_csv_mathplotlib.py` (conditional)

---

## Phase 4: Fix Bare Imports in phase2/RAG_app (4 files)

### Task 4.1: Convert bare `from config import` to relative imports

**Why**: After adding `__init__.py` (Task 3.2 of modernization plan), `phase2/RAG_app/` is now a proper package. The bare `from config import` still works when scripts are run directly from that directory, but fails when imported as `phase2.RAG_app.*` (as the smoke test does). Relative imports work in both contexts.

**Steps**:
1. In each file, change `from config import ...` → `from .config import ...`
2. In `qa_loop.py`, also check for `from windows_ip_in_wsl import` → `from .windows_ip_in_wsl import`
3. In `qa_loop.py`, check for `from retriever import` → `from .retriever import`
4. Verify the smoke test still passes
5. Verify scripts still run directly (they'll need `python -m phase2.RAG_app.qa_loop` instead of `python qa_loop.py` — document this)

**Files to modify**:
- `phase2/RAG_app/delete_collection.py`
- `phase2/RAG_app/ingest_pdf.py`
- `phase2/RAG_app/qa_loop.py`
- `phase2/RAG_app/retriever.py`

---

## Phase 5: Cosmetic Fixes (2 tasks, independent)

### Task 5.1: Fix broken shebang in continue_tutorial.py

**Why**: `phase1/python_code/continue_tutorial.py` line 1 is `""  #!/usr/bin/env python3` — a string literal followed by a comment. The shebang is inert.

**Steps**:
1. Change line 1 to `#!/usr/bin/env python3`
2. Move the `from __future__ import annotations` to line 2 (after shebang)
3. Keep the ASCII art docstring that follows

**Files to modify**: `phase1/python_code/continue_tutorial.py`

### Task 5.2: Update ruff pre-commit hook ID from legacy alias

**Why**: `ruff` hook ID in ruff-pre-commit v0.15.10 shows as "(legacy alias)". The current non-legacy ID is `ruff-check`.

**Steps**:
1. In `.pre-commit-config.yaml`, change `- id: ruff` → `- id: ruff-check`
2. Keep `args: [--fix]` unchanged
3. Verify with `pre-commit run --all-files`

**Files to modify**: `.pre-commit-config.yaml`

---

## Phase 6: Verify & Close

### Task 6.1: Full pyright verification

**Steps**:
1. Run `uv run --python 3.12 pyright` — expect 0 errors, 0 warnings for own code
2. Run `uv run --python 3.12 pytest -q` — expect same pass/fail as before
3. Run `uv run --python 3.12 ruff check .` — expect 0 errors

---

## Dependency Summary

| Phase | Tasks | Parallel? |
|-------|-------|-----------|
| 1 (pyrightconfig) | 1.1 | Independent |
| 2 (deps) | 2.1 | Independent of Phase 1, but do first — resolves most errors |
| 3 (code bugs) | 3.1, 3.2, 3.3, 3.4 | All independent; 3.4 conditional on Phase 2 |
| 4 (bare imports) | 4.1 | Independent |
| 5 (cosmetic) | 5.1, 5.2 | Both independent |
| 6 (verify) | 6.1 | After all others |

**Recommended execution order**: 1.1 + 2.1 parallel → 3.1–3.4 + 4.1 + 5.1 + 5.2 parallel → 6.1

## Out of Scope

- **Secret rotation** (Gemini, Nomic, Weaviate) — manual external action, not automatable
- **Trailing whitespace in non-.py files** (markdown, yaml, html) — pre-existing in third-party and docs files; run `pre-commit run --all-files` separately if desired
