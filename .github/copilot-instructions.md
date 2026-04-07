# Project Guidelines

## Architecture
- This is a single-app Flask project centered in app.py.
- Keep backend behavior in app.py API routes/models, UI structure in templates/index.html and templates/login.html, client logic in static/js/script.js, and styling in static/css/style.css.
- Maintain the current server-rendered + vanilla JS architecture. Do not introduce frontend frameworks unless explicitly requested.
- For scoring changes or new game types, extend the small replay helpers in `app.py` (for example `recompute_game_state()` and the per-game apply helpers) rather than scattering rule changes across routes.

## Build and Test
- Local setup and run:
  - python -m venv .venv
  - source .venv/bin/activate
  - pip install -r requirements.txt
  - python app.py
- Primary backend tests:
  - python -m pytest tests/test_app.py -q
- Full test suite (includes Selenium):
  - python -m pytest -q
- Container run:
  - docker compose up --build
  - app is exposed on host port 5010

## Conventions
- Scoring rule: only totals divisible by 5 are counted; fives awarded are total/5 when counted.
- Win condition: exactly 55 fives; above 55 is a bust and awards zero fives for that turn.
- Keep the live-scoring UI keypad-first for touch use; do not reintroduce spinner-heavy number entry for `55 by 5`.
- English Cricket team labels are persisted via `team_names`, and inning/runs/wickets state is persisted via `cricket_state`.
- Keep API error responses JSON-shaped as {"error": "..."} with appropriate HTTP status codes.
- Use UTC timestamps and ISO serialization patterns consistent with app.py.
- Preserve session-based auth behavior and admin-gated actions:
  - admin-only endpoints must verify current_user_or_testing_admin().is_admin
  - UI admin actions should be hidden for non-admin users and enforced server-side

## Data and Environment Gotchas
- SQLite path matters in Docker. Use a writable mounted directory and a file URI (see docker-compose.yml SQLALCHEMY_DATABASE_URI).
- Keep local and container port assumptions aligned:
  - local python app.py uses 5000 by default
  - Docker maps host 5010 to container 5000
- macOS urllib3/OpenSSL warning is handled via urllib3<2 in requirements.txt; do not upgrade this casually without validating local compatibility.

## Documentation Links
- See README.md for full setup, auth configuration, API endpoint list, and troubleshooting.
