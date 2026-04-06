# 55 by 5 Darts (Flask)

Local single-user Flask app for darts scoring and game management with:

- Persistent player roster
- Drag-and-drop turn order before game start
- Live turn entry and scoreboard
- Persisted completed-game history
- Support for **55 by 5** and **English Cricket**

This project is designed for local play on one machine (session-based login, no multiplayer networking).

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
- [Run tests](#run-tests)
- [Data persistence](#data-persistence)
- [Troubleshooting](#troubleshooting)

## Overview

The app supports any number of players in the roster. After login, you set up players and teams on the setup page, then choose a game mode from the separate **Select Game** panel:

- **55 by 5**
- **English Cricket**

For each new game, you select who is playing and drag players into the desired turn order. You can play in individual mode or in two teams with drag-and-drop team assignment.

For **55 by 5**, each turn is entered as one total score value. A turn only counts if the total score is divisible by 5. Counted turn score is tracked as "fives" where:

$$
\text{fives awarded} = \frac{\text{turn total}}{5}
$$

The winner is the first player to reach exactly 55 on a counted turn.

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

http://127.0.0.1:5000

## Run with Docker Compose

From the project root:

```bash
docker compose up --build
```

Then open:

http://127.0.0.1:5010

Log in with the default admin credentials (`admin` / `admin`) and change the password via the User Administration panel.

### Configuration via environment variables

The easiest way to override defaults is to create or edit `.env` in the project root **before** running Compose (it is git-ignored and never committed):

```dotenv
APP_SECRET_KEY=replace-with-a-long-random-string
APP_ADMIN_USERNAME=myadmin
APP_ADMIN_PASSWORD=my-strong-password
```

Docker Compose picks up `.env` automatically. The three variables are:

| Variable | Default | Purpose |
|---|---|---|
| `APP_SECRET_KEY` | `change-me-before-going-live` | Flask session signing key — **must be changed** for any non-local deployment |
| `APP_ADMIN_USERNAME` | `admin` | Bootstrap admin username (used only when no admin account exists yet) |
| `APP_ADMIN_PASSWORD` | `admin` | Bootstrap admin password |

You can also pass them inline:

```bash
APP_SECRET_KEY=abc123 APP_ADMIN_PASSWORD=hunter2 docker compose up --build
```

If you update `APP_ADMIN_PASSWORD` and it appears unchanged:

1. Recreate the container so new env vars are applied:

   ```bash
   docker compose down
   docker compose up -d --build --force-recreate
   ```

2. Log out of the app and log back in (existing browser sessions remain valid until logout).

3. Verify the container sees the new value:

   ```bash
   docker compose exec web env | grep APP_ADMIN
   ```

4. Confirm you are using the username from `APP_ADMIN_USERNAME`.

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

To stop the app, press `Ctrl+C` in the terminal.

## Authentication

The app requires login before accessing the game UI.

### Default admin account

On first start (or whenever no admin account exists in the database) a bootstrap admin user is created automatically:

| Setting | Default | Override env var |
|---|---|---|
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

## How to play in the UI

1. Add players in the Players panel.
2. Check the players who will play in **Select Players**.
3. Drag players in Selected Players to set the sequence.
4. Choose `Individual` or `Teams` mode.
5. If using `Teams`, drag players between Team A and Team B.
6. In the separate **Select Game** panel, choose `55 by 5` or `English Cricket`.
7. For English Cricket, a popup lets Team A choose whether to `Bat` or `Bowl`, then click `Start Game`.
8. For `55 by 5`, click `55 by 5` once to begin the match.
9. In Live Game, enter the turn value for the active player.
10. Click Submit Score.
11. Review completed games in Recent Games.

Notes:

- Only one active game is allowed at a time.
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

### English Cricket

- Supports individual mode (2 players) or 2-team mode.
- Game has two innings with role swap.
- Batting turn: only points above 40 count as runs (`runs = total_points - 40` when over 40).
- Bowling turn: enter bull marks for the turn; 10 marks closes the opponent's innings.
- In inning 2, batting side wins immediately if it passes the other side's runs.
- If innings completes without an immediate chase win, higher run total wins.

Completed games are saved in history.
Examples:

- Turn total: `20` -> counted -> `4` fives.
- Turn total: `3` -> not divisible by `5` -> `0` fives.
- Turn total: `75` -> counted -> `15` fives.

Accepted total range per turn:

- `0` to `180`

## Project layout

```text
55by5/
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
- `POST /api/auth/users` -> create app user (admin only)
- `GET /api/meta` -> config metadata (valid turn total range, targets, winning fives)
- `GET /api/players` -> list players
- `POST /api/players` -> create player
- `PUT /api/players/<player_id>` -> rename player
- `DELETE /api/players/<player_id>` -> delete player (if not in active game)
- `GET /api/games/active` -> active game state
- `POST /api/games` -> create game from ordered player ids (supports `game_type`, `team_mode`, `team_assignments`)
- `POST /api/games/<game_id>/turn` -> submit one turn total value
- `DELETE /api/games/<game_id>/turn` -> undo the most recent turn
- `GET /api/games/<game_id>/state` -> full game state
- `GET /api/games/history` -> list finished games
- `DELETE /api/games/history` -> delete all finished game history (admin only)
- `GET /api/games/<game_id>/history` -> details of a finished/current game

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

- Counted vs non-counted turns
- Fives calculation
- Win condition at exact 55
- Bust behavior when a turn would exceed 55
- Game history persistence and admin history deletion

## Data persistence

- Database file: `darts.db` in project root
- Player roster persists across restarts
- Completed game history persists across restarts
- App user accounts persist across restarts

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

Then open http://127.0.0.1:5001

### Drag and drop not updating order

- Ensure players are selected first.
- Drag from one order row onto another row.
- If needed, refresh the page and reselect players.

### Cannot start a new game

The app permits only one active game at a time. Finish the active game first.

## License

This repository currently has no license file. Add one if you plan to distribute it.
