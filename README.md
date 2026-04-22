# Darts Scores (Flask)

Local Flask app for darts scoring with:

- Persistent player roster
- Drag-and-drop turn order before game start
- Live turn entry and scoreboard
- Persisted completed-game history

This project is designed for local play on one machine with session-based login. Multiple signed-in users can use the app at the same time, each with their own active game and game history view.

## Table of contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Run with Docker Compose](#run-with-docker-compose)
- [Run the app](#run-the-app)
- [Authentication](#authentication)
- [How to play in the UI](#how-to-play-in-the-ui)
- [Scoring rules](#scoring-rules)
- [Project layout](#project-layout)
- [API endpoints](#api-endpoints)
- [Extending the app](#extending-the-app)
- [Run tests](#run-tests)
- [Data persistence](#data-persistence)
- [Troubleshooting](#troubleshooting)

## Overview

The app supports any number of players in the roster. After login, you set up players and teams on the setup page, then choose a game mode from the separate **Select Game** panel:

- **X01**
- **55 by 5**
- **English Cricket**
- **Noughts and Crosses**

For each new game, you select who is playing and drag players into the desired turn order. You can play in singles mode or in two teams with drag-and-drop team assignment.

For **55 by 5**, each turn is entered as one total score value using the on-screen keypad. A turn only counts if the total score is divisible by 5, and counted turns award `turn total / 5` fives. The winner is the first player or team to reach exactly 55 fives.

For **X01**, the start popup lets you choose `1001`, `501`, `301`, or `101`, then players or teams count down to exactly zero. Overshooting zero or leaving `1` is a bust and scores nothing for that turn.

For **Noughts and Crosses**, each game generates a fresh board of dart targets and players claim squares as `X` or `O` until one side completes three in a row.

## Requirements

- macOS, Linux, or Windows
- Python 3.9+
- pip

Optional but recommended:

- Virtual environment (`venv`)

## Quick start

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open:

<http://127.0.0.1:5000>

To expose the app to other devices on your local network when running directly on your machine:

```bash
APP_HOST=0.0.0.0 APP_PORT=5000 python app.py
```

Then open `http://<your-machine-ip>:5000` from another device on the same network.

## Run with Docker Compose

From the project root:

```bash
docker compose up --build
```

Then open:

<http://127.0.0.1:5010>

Docker Compose already publishes the app on all network interfaces through host port `5010`, so other devices can use:

`http://<your-machine-ip>:5010`

Log in with the default admin credentials (`admin` / `admin`) and change the password via the User Administration panel.

### Configuration via environment variables

The app can load settings from a project-root `.env` file for both `python app.py` and Docker Compose. Use `.env.example` as the template, then create or edit your local `.env` (it is git-ignored and never committed):

```dotenv
APP_SECRET_KEY=replace-with-a-long-random-string
APP_ADMIN_USERNAME=myadmin
APP_ADMIN_PASSWORD=my-strong-password
APP_HOST=127.0.0.1
APP_PORT=5000
```

`python app.py` reads this file via `python-dotenv`, and Docker Compose picks it up automatically.

The supported variables are:

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_SECRET_KEY` | `change-me-before-going-live` | Flask session signing key — **must be changed** for any non-local deployment |
| `APP_ADMIN_USERNAME` | `admin` | Bootstrap admin username (used only when no admin account exists yet) |
| `APP_ADMIN_PASSWORD` | `admin` | Bootstrap admin password |
| `APP_HOST` | `127.0.0.1` | Host interface used by `python app.py`; set to `0.0.0.0` to expose the app on your LAN |
| `APP_PORT` | `5000` | Port used by `python app.py` |

Notes:

- The SQLite database is persisted in a named Docker volume.
- Stop the app with `Ctrl+C`.
- Start detached with `docker compose up -d`.
- Stop and remove containers with `docker compose down`.
- Reset DB data (including all users) by removing the volume: `docker compose down -v`.

## Run the app

1. Create and activate a virtual environment.
2. Install dependencies.
3. Start Flask via `python app.py`.
4. Keep the terminal open while playing.
5. Optional: set `APP_HOST` and `APP_PORT` in `.env` if you want to change the bind address or port without typing them each time.

To stop the app, press `Ctrl+C` in the terminal.

## Authentication

The app requires login before accessing the game UI.

### Default admin account

On first start (or whenever no admin account exists in the database) a bootstrap admin user is created automatically:

| Setting | Default | Override env var |
| --- | --- | --- |
| Username | `admin` | `APP_ADMIN_USERNAME` |
| Password | `admin` | `APP_ADMIN_PASSWORD` |

Change the default password immediately after first login by creating a new admin account and deleting the default one, or by restarting the app with `APP_ADMIN_PASSWORD` set to a strong value (bootstrap only runs when **no admin exists**).

If the configured admin username already exists, startup will synchronize that user's password and admin flag from `APP_ADMIN_PASSWORD` / `APP_ADMIN_USERNAME`.

### Secret key

Flask signs session cookies with `APP_SECRET_KEY`. The built-in default is intentionally weak. For any deployment beyond a single local machine, set a long random value:

```bash
# generate a suitable key
python -c "import secrets; print(secrets.token_hex(32))"
```

Set it in `.env` (see [Run with Docker Compose](#run-with-docker-compose)) or export it in your shell before running `python app.py`.

### Creating additional users

After logging in as admin, the **User Administration** panel is visible in the top-right corner of the game screen. Enter a username and password there to create additional non-admin (or admin) accounts.

Admins can also clear finished game history from the **Recent Games** panel.

Sessions expire after 30 minutes of inactivity. Logging out during an active game shows a confirmation prompt and abandons that user's active game if confirmed.

## How to play in the UI

1. Use the `+` button in **Select Players** to open the player manager and add players.
2. Check the players who will play in **Select Players**.
3. Drag players in Selected Players to set the sequence.
4. Choose `Singles` or `Teams` mode.
5. If using `Teams`, drag players between Team A and Team B.
6. In the separate **Select Game** panel, choose `X01`, `55 by 5`, `English Cricket`, or `Noughts and Crosses`.
7. For X01, choose the starting score in the popup, then click `Start Game`.
8. For English Cricket, a popup lets Team A choose whether to `Bat` or `Bowl`, then click `Start Game`.
9. For `55 by 5` and `Noughts and Crosses`, click the game button once to begin the match.
10. In Live Game, use the on-screen keypad to enter the active player's score, or click board squares in Noughts and Crosses.
11. Use `Submit Score`, `No Score`, or `Undo` as needed.
12. Review completed games in Recent Games.

Notes:

- Each signed-in user can have one active game at a time.
- Different users can run games concurrently in separate sessions.
- Player deletion is blocked if that player is in the active game.

## Scoring rules

### 55 by 5

- Any number of players can be created and stored persistently.
- Players are selected per game and ordered via drag-and-drop.
- Each turn is entered as one total points value.
- Turn total must be divisible by 5 to count.
- Fives gained from a turn = total points / 5.
- Winner is first player (or team in 2-team mode) to reach exactly 55 on a counted turn.
- If a counted turn would push above 55, it is a bust and does not count.

### X01

- Supports singles mode or 2-team mode.
- Start each game at `1001`, `501`, `301`, or `101`.
- Each turn is entered as one total points value.
- Winner is the first player or team to reach exactly `0`.
- If a turn would push below `0`, it is a bust and does not count.
- If a turn leaves exactly `1`, it is also a bust and does not count.
- The live view shows the active remaining total and checkout suggestions where available.

### English Cricket

- Supports singles mode (2 players) or 2-team mode.
- Game has two innings with role swap.
- Batting turn: only points above 40 count as runs (`runs = total_points - 40` when over 40).
- Bowling turn: enter bull marks for the turn; 10 marks closes the opponent's innings.
- In inning 2, batting side wins immediately if it passes the other side's runs.
- If innings completes without an immediate chase win, higher run total wins.

### Noughts and Crosses

- Supports singles mode (exactly 2 players) or 2-team mode.
- Each game generates a board of dart targets; the center square is always `Bullseye`.
- Clicking an open square lets the player assign it to `X` or `O`.
- First side to make three in a row wins.
- If all squares are claimed without a winning line, the game ends in a tie.

Completed games are saved in history.
Examples:

- Turn total: `20` -> counted -> `4` fives.
- Turn total: `3` -> not divisible by `5` -> `0` fives.
- Turn total: `75` -> counted -> `15` fives.

Accepted total range per turn:

- `0` to `180`

## Project layout

```text
darts-scores/
 app.py
 requirements.txt
 README.md
 templates/
  index.html
 static/
  css/
   style.css
  js/
   script.js
 tests/
  test_app.py
 darts.db               # auto-created on first run
```

## API endpoints

Main routes exposed by the Flask app:

- `GET /` -> main UI (requires login)
- `GET/POST /login` -> login page and login submit
- `POST /logout` -> logout current session
- `GET /api/auth/me` -> current authenticated user
- `GET /api/auth/users` -> list app users (admin only)
- `POST /api/auth/users` -> create app user (admin only)
- `PUT /api/auth/users/<user_id>/password` -> update a user's password (admin only)
- `GET /api/meta` -> config metadata (valid turn total range, targets, winning fives)
- `GET /api/players` -> list players
- `GET /api/players/<player_id>/stats` -> player summary stats by game type
- `POST /api/players` -> create player
- `PUT /api/players/<player_id>` -> rename player
- `DELETE /api/players/<player_id>` -> delete player (if not in active game)
- `GET /api/games/active` -> current user's active game state
- `POST /api/games` -> create game from ordered player ids (supports `game_type`, `team_mode`, `team_assignments`, `team_names`, `starting_batting_team`, `x01_starting_score`)
- `POST /api/games/<game_id>/turn` -> submit one turn total value
- `DELETE /api/games/<game_id>/turn` -> undo the most recent turn
- `GET /api/games/<game_id>/state` -> full game state
- `GET /api/games/history` -> list finished games visible to the current user
- `DELETE /api/games/history` -> delete all finished game history (admin only)
- `GET /api/games/<game_id>/history` -> details of a finished/current game

## Extending the app

To add another game type cleanly:

1. Add the new `game_type` value in `app.py` metadata and creation validation.
2. Keep backend scoring/replay rules in the small helper functions used by `recompute_game_state()`.
3. Add a dedicated renderer or UI branch in `static/js/script.js` rather than mixing new rules into existing keypad handlers.
4. Cover the new flow with both API tests in `tests/test_app.py` and, if it affects the UI, Selenium tests in `tests/test_gui_selenium.py`.

## Run tests

With virtual environment active:

```bash
python -m pytest -q
```

Backend coverage report:

```bash
python -m pytest tests/test_app.py --cov=app --cov-report=term-missing -q
```

Run Selenium GUI tests (requires Chrome or Firefox installed):

```bash
python -m pytest tests/test_gui_selenium.py -q
```

Notes for GUI tests:

- Tests run headless.
- Selenium will try Chrome first, then Firefox.
- If no compatible browser/WebDriver is available, the GUI tests are skipped.

With Docker Compose (containerized test run):

```bash
docker compose --profile test run --rm test
```

Optional: run tests as a Compose one-off without the profile flag:

```bash
docker compose run --rm test
```

The current test suite verifies:

- X01 setup, busts, shared team remaining, and end-to-end finish flows
- Counted vs non-counted turns
- Fives calculation
- Win condition at exact 55
- Bust behavior when a turn would exceed 55
- English Cricket inning flow and start-role selection
- Noughts and Crosses board flow and winning states
- Player stats, admin account management, and history deletion
- Game history persistence and admin history deletion

## Data persistence

- Database file: `darts.db` in project root
- Player roster persists across restarts
- Completed game history persists across restarts
- App user accounts persist across restarts
- Game ownership persists across restarts, so each user's active/finished games remain scoped to that account

To reset all local data (including user accounts):

1. Stop the app.
2. Delete `darts.db`.
3. Restart the app (the bootstrap admin account is re-created automatically).

When running with Docker Compose, remove the named volume instead:

```bash
docker compose down -v
```

## Troubleshooting

### `ModuleNotFoundError` or missing Flask packages

Make sure your virtual environment is active and dependencies are installed:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### `urllib3` / OpenSSL warning on macOS

If you see a warning similar to:

`urllib3 v2 only supports OpenSSL 1.1.1+ ... LibreSSL`

- This project pins `urllib3<2` in `requirements.txt` to avoid the warning on older system Python builds.
- Long-term fix: recreate your virtual environment with a modern Python linked against OpenSSL (for example Python 3.11+ from Homebrew), then reinstall requirements.

### Port already in use

If port 5000 is busy, run with a different port:

```bash
python -m flask --app app run --port 5001
```

Then open <http://127.0.0.1:5001>

### Expose the app on your local network

Run the app with a public bind address:

```bash
APP_HOST=0.0.0.0 APP_PORT=5000 python app.py
```

Then find your machine's LAN IP, for example on macOS:

```bash
ipconfig getifaddr en0
```

or, if you are on Ethernet:

```bash
ipconfig getifaddr en1
```

Other devices on the same network can then connect to:

`http://<your-machine-ip>:5000`

If macOS firewall prompts you, allow incoming connections for Python.

### Drag and drop not updating order

- Ensure players are selected first.
- Drag from one order row onto another row.
- If needed, refresh the page and reselect players.

### Cannot start a new game

Each signed-in user can have only one active game at a time. Finish or quit your current game first.

## License

This repository currently has no license file. Add one if you plan to distribute it.
