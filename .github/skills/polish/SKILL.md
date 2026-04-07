---
name: polish
description: 'Analyze this darts-scores codebase and apply a final production polish pass. Use for codebase audit, maintainability refactors, cleanup, UX/release checks, deployment/config review, README/test updates, and release-readiness verification.'
argument-hint: 'Describe the polish goal, area to focus on, or release concern to address'
user-invocable: true
---

# Production Polish Workflow

Use this skill when the goal is to give the repository a **final cleanup and release-ready polish pass** without changing the overall Flask + vanilla JS architecture.

## Best Fit

Trigger this skill for requests like:

- “perform a final polish before production”
- “analyze the codebase and refactor where needed”
- “clean this up for future game types”
- “review docs/tests and make it production ready”
- “do a maintainability pass”
- “do a release-readiness sweep”
- “double-check deployment and config safety”

## Repo Context

This repository is a single-app Flask project:

- Backend and game rules live in `app.py`
- UI templates live in `templates/`
- Client logic lives in `static/js/script.js`
- Styling lives in `static/css/style.css`
- Regression coverage lives in `tests/test_app.py` and `tests/test_gui_selenium.py`

Important conventions to preserve:

- Keep the current **server-rendered + vanilla JS** approach
- Keep API errors shaped like `{"error": "..."}`
- Use UTC timestamps and current serialization patterns
- For new rule changes, extend the small replay helpers in `app.py` rather than scattering logic across routes
- Keep the live scoring flow **keypad-first** for touch use

## Procedure

1. **Audit the current structure**
   - Read `app.py`, `static/js/script.js`, `README.md`, and the relevant tests
   - Identify duplication, oversized functions, stale comments, and game-type branching that can be simplified safely
   - Check the changed files for editor/diagnostic issues before and after refactoring

2. **Choose safe refactors**
   - Prefer extracting helper functions over changing public behavior
   - Improve naming, docstrings, and single-responsibility boundaries
   - Avoid introducing frameworks or large architectural rewrites unless explicitly requested

3. **Polish the backend**
   - Simplify replay/scoring logic in `app.py`
   - Centralize validation, creation, and serialization helpers
   - Keep `55 by 5` and `English Cricket` rules unchanged unless the user requested behavior changes
   - Preserve auth, admin gating, and SQLite persistence behavior

4. **Polish the frontend and UX**
   - Reduce duplicated state-sync or drag-and-drop logic in `static/js/script.js`
   - Keep the existing keypad-based UX intact
   - Review confirmation dialogs, empty states, admin-only UI visibility, and touch-friendly controls
   - Preserve current user-visible behavior unless the user asked for UI changes

5. **Review deployment and configuration safety**
   - Check `docker-compose.yml`, `Dockerfile`, env-var usage, and data-persistence assumptions when relevant
   - Make sure docs still reflect port mappings, DB persistence, and bootstrap admin/security expectations
   - Call out risky defaults or stale deployment notes if found

6. **Strengthen coverage and diagnostics**
   - Add or update tests when a refactor touches game flow, undo, win detection, session/logout behavior, or admin actions
   - Prefer backend regression tests first, then GUI coverage when the UI changed
   - Run editor diagnostics on changed files and fix any new issues

7. **Refresh docs and instructions**
   - Update `README.md` if UI behavior, setup notes, API payloads, or extension guidance are now stale
   - Keep `.github/copilot-instructions.md` and any user-facing guidance aligned with the current conventions

8. **Verify before finishing**
   Run the relevant checks and cite the fresh output:

   ```bash
   /Users/lee/vscode_projects/darts-scores/.venv/bin/python -m pytest tests/test_app.py -q
   /Users/lee/vscode_projects/darts-scores/.venv/bin/python -m pytest tests/test_gui_selenium.py -q
   ```

   Also check changed-file diagnostics with the editor error tools when code or docs were updated.

   If the change is broad, also run:

   ```bash
   /Users/lee/vscode_projects/darts-scores/.venv/bin/python -m pytest -q
   ```

## Optional Release Checklist

Use this as a final pass when the request is explicitly about production readiness:

- remove dead code, stale comments, and obvious cleanup leftovers
- confirm no secrets, tokens, or environment-specific data were accidentally added
- verify Docker/local setup instructions still match the real app behavior
- smoke-check critical flows: login, logout confirmation, start game, undo, finish game, quit game, history, and admin-only actions
- note any follow-up work that should be deferred instead of rushed into the polish pass

## Output Expectations

When using this skill, finish with:

- a short summary of what was refactored
- the files changed
- any new tests or documentation updates
- the exact verification evidence from the latest test run

## Guardrails

- Do **not** claim success without running the verification commands
- Do **not** change behavior speculatively; keep fixes root-cause based
- Do **not** add test-only production code
- Do **not** weaken the current auth, admin gating, or persistence behavior
