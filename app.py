from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import random
from pathlib import Path

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "darts.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", "change-this-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{DB_PATH}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_SORT_KEYS"] = False

SESSION_IDLE_TIMEOUT_SECONDS = 30 * 60


db = SQLAlchemy(app)


class AppUser(db.Model):
    __tablename__ = "app_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default="active")
    game_type = db.Column(db.String(30), nullable=False, default="55by5")
    team_mode = db.Column(db.String(10), nullable=False, default="solo")
    team_assignments = db.Column(db.Text, nullable=True)
    team_names = db.Column(db.Text, nullable=True)
    cricket_state = db.Column(db.Text, nullable=True)
    noughts_and_crosses_state = db.Column(db.Text, nullable=True)
    winner_team = db.Column(db.String(20), nullable=True)
    current_turn_position = db.Column(db.Integer, nullable=False, default=0)
    winner_player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=True)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)


class GamePlayerOrder(db.Model):
    __tablename__ = "game_player_order"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False)


class GameScore(db.Model):
    __tablename__ = "game_scores"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    fives = db.Column(db.Integer, nullable=False, default=0)


class Turn(db.Model):
    __tablename__ = "turns"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    turn_number = db.Column(db.Integer, nullable=False)
    dart_1 = db.Column(db.Integer, nullable=False)
    dart_2 = db.Column(db.Integer, nullable=False)
    dart_3 = db.Column(db.Integer, nullable=False)
    total_points = db.Column(db.Integer, nullable=False)
    counted = db.Column(db.Boolean, nullable=False, default=False)
    fives_awarded = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


def now_iso(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.isoformat()


def get_current_user() -> AppUser | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(AppUser, user_id)


def current_user_or_testing_admin() -> AppUser | None:
    user = get_current_user()
    if user:
        return user
    if app.config.get("TESTING"):
        return AppUser(id=0, username="test-admin", password_hash="", is_admin=True)
    return None


def require_admin_user() -> tuple[AppUser | None, tuple[object, int] | None]:
    user = current_user_or_testing_admin()
    if not user:
        return None, (jsonify({"error": "Authentication required."}), 401)
    if not user.is_admin:
        return None, (jsonify({"error": "Admin access required."}), 403)
    return user, None


def current_session_timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def find_player_by_name(name: str) -> Player | None:
    return Player.query.filter(func.lower(Player.name) == name.lower()).first()


def normalize_utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def abandon_games(games: list[Game]) -> int:
    active_games = [game for game in games if game.status == "active"]
    if not active_games:
        return 0

    finished_at = datetime.now(timezone.utc)
    for game in active_games:
        game.status = "abandoned"
        game.finished_at = finished_at

    db.session.commit()
    return len(active_games)


def abandon_active_games() -> int:
    games = Game.query.filter_by(status="active").all()
    return abandon_games(games)


def abandon_expired_games(timeout_seconds: int = SESSION_IDLE_TIMEOUT_SECONDS) -> int:
    threshold = normalize_utc_datetime(datetime.now(timezone.utc)) - timedelta(seconds=timeout_seconds)
    stale_games: list[Game] = []

    for game in Game.query.filter_by(status="active").all():
        latest_turn = (
            Turn.query.with_entities(Turn.created_at)
            .filter_by(game_id=game.id)
            .order_by(Turn.created_at.desc())
            .first()
        )
        last_activity_at = latest_turn[0] if latest_turn else game.started_at
        normalized_activity = normalize_utc_datetime(last_activity_at)
        if normalized_activity and normalized_activity <= threshold:
            stale_games.append(game)

    return abandon_games(stale_games)


def ensure_admin_user() -> None:
    username = os.getenv("APP_ADMIN_USERNAME", "admin").strip() or "admin"
    password = os.getenv("APP_ADMIN_PASSWORD", "admin")
    existing = AppUser.query.filter(func.lower(AppUser.username) == username.lower()).first()
    if existing:
        updated = False
        if not check_password_hash(existing.password_hash, password):
            existing.password_hash = generate_password_hash(password, method="pbkdf2:sha256")
            updated = True
        if not existing.is_admin:
            existing.is_admin = True
            updated = True
        if updated:
            db.session.commit()
        return
    admin = AppUser(
        username=username,
        password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
        is_admin=True,
    )
    db.session.add(admin)
    db.session.commit()


@app.before_request
def require_login():
    g.current_user = get_current_user()

    if request.endpoint != "static":
        abandon_expired_games()

    if app.config.get("TESTING"):
        return None

    if request.endpoint == "static":
        return None

    if request.path in {"/login", "/logout"}:
        return None

    if g.current_user:
        raw_last_activity = session.get("last_activity_at")
        try:
            last_activity_at = int(raw_last_activity) if raw_last_activity is not None else None
        except (TypeError, ValueError):
            last_activity_at = None

        now_ts = current_session_timestamp()
        if last_activity_at is not None and now_ts - last_activity_at >= SESSION_IDLE_TIMEOUT_SECONDS:
            abandon_active_games()
            session.clear()
            g.current_user = None
            if request.path.startswith("/api/"):
                return jsonify({"error": "Session expired due to inactivity."}), 401
            return redirect(url_for("login"))

        session["last_activity_at"] = now_ts
        return None

    if request.path.startswith("/api/"):
        return jsonify({"error": "Authentication required."}), 401

    return redirect(url_for("login"))


MAX_TURN_TOTAL = 180
CRICKET_WICKET_TARGET = 10
TEAM_A = "team_a"
TEAM_B = "team_b"
NOUGHTS_AND_CROSSES_MARK_X = "X"
NOUGHTS_AND_CROSSES_MARK_O = "O"
NOUGHTS_AND_CROSSES_DARTBOARD_NUMBERS = list(range(1, 21))
NOUGHTS_AND_CROSSES_SEGMENTS = ["Big", "Small", "Double", "Treble"]
NOUGHTS_AND_CROSSES_WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def generate_random_noughts_targets() -> list[str]:
    """Generate random dartboard targets for Noughts and Crosses board.
    Center cell (index 4) is always Bullseye.
    Other 8 cells are random combinations of numbers (1-20) and segments.
    """
    targets = []
    for i in range(9):
        if i == 4:
            targets.append("Bullseye")
        else:
            number = random.choice(NOUGHTS_AND_CROSSES_DARTBOARD_NUMBERS)
            segment = random.choice(NOUGHTS_AND_CROSSES_SEGMENTS)
            targets.append(f"{segment} {number}")
    return targets


def default_team_names() -> dict[str, str]:
    return {TEAM_A: "Team A", TEAM_B: "Team B"}


def normalize_team_name_value(raw_value: object, fallback: str) -> str:
    if not isinstance(raw_value, str):
        return fallback
    cleaned = raw_value.strip()
    return cleaned[:40] if cleaned else fallback


def normalize_game_type(raw_type: str | None) -> str:
    game_type = (raw_type or "55by5").strip().lower()
    if game_type == "english_cricket":
        return "english_cricket"
    if game_type in {"noughts_and_crosses", "noughts-and-crosses", "noughts", "tic_tac_toe", "tic-tac-toe", "tic tac toe"}:
        return "noughts_and_crosses"
    return "55by5"


def normalize_team_mode(raw_mode: str | None) -> str:
    team_mode = (raw_mode or "solo").strip().lower()
    return "teams" if team_mode == "teams" else "solo"


def normalize_cricket_team(raw_team: str | None, default: str = TEAM_A) -> str:
    team = (raw_team or default).strip().lower() if isinstance(raw_team, str) else default
    return TEAM_B if team == TEAM_B else TEAM_A


def build_initial_cricket_state(starting_batting_team: str | None = TEAM_A) -> dict:
    batting_team = normalize_cricket_team(starting_batting_team, TEAM_A)
    bowling_team = TEAM_B if batting_team == TEAM_A else TEAM_A
    return {
        "inning": 1,
        "starting_batting_team": batting_team,
        "starting_bowling_team": bowling_team,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "runs": {TEAM_A: 0, TEAM_B: 0},
        "wickets": {TEAM_A: 0, TEAM_B: 0},
    }


def build_initial_noughts_and_crosses_state() -> dict:
    targets = generate_random_noughts_targets()
    return {
        "cells": [{"label": label, "mark": None} for label in targets],
        "winner_marker": None,
        "winning_line": [],
    }


def starting_turn_position(ordered_players: list[dict], assignments: dict[int, str], bowling_team: str | None) -> int:
    if not ordered_players:
        return 0
    preferred_team = normalize_cricket_team(bowling_team, TEAM_B)
    for index, player in enumerate(ordered_players):
        if assignments.get(player["id"], TEAM_A) == preferred_team:
            return index
    return 0


def normalize_total_points(raw_total: int) -> tuple[int | None, str | None]:
    if not isinstance(raw_total, int):
        return None, "total_points must be an integer."
    if raw_total < 0 or raw_total > MAX_TURN_TOTAL:
        return None, f"total_points must be between 0 and {MAX_TURN_TOTAL}."
    return raw_total, None


def turn_result(total: int) -> tuple[int, bool, int]:
    counted = total % 5 == 0
    fives = total // 5 if counted else 0
    return total, counted, fives


def parse_team_assignments(raw_value: str | None) -> dict[int, str]:
    if not raw_value:
        return {}
    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError):
        return {}
    if not isinstance(decoded, dict):
        return {}

    result: dict[int, str] = {}
    for key, value in decoded.items():
        try:
            player_id = int(key)
        except (TypeError, ValueError):
            continue
        if value in {TEAM_A, TEAM_B}:
            result[player_id] = value
    return result


def parse_team_names(raw_value: str | None) -> dict[str, str]:
    names = default_team_names()
    if not raw_value:
        return names

    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError):
        return names
    if not isinstance(decoded, dict):
        return names

    for team_key, fallback in names.items():
        names[team_key] = normalize_team_name_value(decoded.get(team_key), fallback)
    return names


def parse_cricket_state(raw_value: str | None) -> dict:
    """Deserialize stored cricket state and fill any missing fields with safe defaults."""
    default_state = build_initial_cricket_state(TEAM_A)
    if not raw_value:
        return default_state

    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError):
        return default_state
    if not isinstance(decoded, dict):
        return default_state

    inning = decoded.get("inning", 1)
    if inning not in (1, 2):
        inning = 1

    batting_team = normalize_cricket_team(decoded.get("batting_team"), TEAM_A)
    bowling_team = normalize_cricket_team(decoded.get("bowling_team"), TEAM_B)
    if batting_team == bowling_team:
        bowling_team = TEAM_B if batting_team == TEAM_A else TEAM_A

    starting_batting_team = normalize_cricket_team(decoded.get("starting_batting_team"), batting_team)
    starting_bowling_team = normalize_cricket_team(
        decoded.get("starting_bowling_team"),
        TEAM_B if starting_batting_team == TEAM_A else TEAM_A,
    )
    if starting_batting_team == starting_bowling_team:
        starting_bowling_team = TEAM_B if starting_batting_team == TEAM_A else TEAM_A

    runs = decoded.get("runs", {}) or {}
    wickets = decoded.get("wickets", {}) or {}
    return {
        "inning": inning,
        "starting_batting_team": starting_batting_team,
        "starting_bowling_team": starting_bowling_team,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "runs": {
            TEAM_A: int(runs.get(TEAM_A, 0)),
            TEAM_B: int(runs.get(TEAM_B, 0)),
        },
        "wickets": {
            TEAM_A: max(0, min(CRICKET_WICKET_TARGET, int(wickets.get(TEAM_A, 0)))),
            TEAM_B: max(0, min(CRICKET_WICKET_TARGET, int(wickets.get(TEAM_B, 0)))),
        },
    }


def normalize_noughts_marker(raw_marker: object, default: str | None = NOUGHTS_AND_CROSSES_MARK_X) -> str | None:
    if isinstance(raw_marker, str):
        marker = raw_marker.strip().upper()
        if marker in {NOUGHTS_AND_CROSSES_MARK_X, NOUGHTS_AND_CROSSES_MARK_O, "0"}:
            return NOUGHTS_AND_CROSSES_MARK_O if marker == "0" else marker
    return default


def encode_noughts_marker(marker: str | None) -> int:
    if marker == NOUGHTS_AND_CROSSES_MARK_X:
        return 1
    if marker == NOUGHTS_AND_CROSSES_MARK_O:
        return 2
    return 0


def decode_noughts_marker(encoded_marker: int | None) -> str | None:
    if encoded_marker == 1:
        return NOUGHTS_AND_CROSSES_MARK_X
    if encoded_marker == 2:
        return NOUGHTS_AND_CROSSES_MARK_O
    return None


def parse_noughts_and_crosses_state(raw_value: str | None) -> dict:
    if not raw_value:
        return build_initial_noughts_and_crosses_state()

    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError):
        return build_initial_noughts_and_crosses_state()
    if not isinstance(decoded, dict):
        return build_initial_noughts_and_crosses_state()

    raw_cells = decoded.get("cells") if isinstance(decoded.get("cells"), list) else []
    cells = []
    for index in range(9):
        raw_cell = raw_cells[index] if index < len(raw_cells) and isinstance(raw_cells[index], dict) else {}
        fallback_label = "Bullseye" if index == 4 else f"Square {index + 1}"
        cells.append(
            {
                "label": str(raw_cell.get("label") or fallback_label),
                "mark": normalize_noughts_marker(raw_cell.get("mark"), None),
            }
        )

    raw_winning_line = decoded.get("winning_line") if isinstance(decoded.get("winning_line"), list) else []
    winning_line = [
        index for index in raw_winning_line
        if isinstance(index, int) and 0 <= index < 9
    ][:3]

    return {
        "cells": cells,
        "winner_marker": normalize_noughts_marker(decoded.get("winner_marker"), None),
        "winning_line": winning_line,
    }


def marker_for_team(team_key: str | None) -> str:
    return NOUGHTS_AND_CROSSES_MARK_O if team_key == TEAM_B else NOUGHTS_AND_CROSSES_MARK_X


def check_noughts_and_crosses_winner(cells: list[dict]) -> tuple[str | None, list[int]]:
    for line in NOUGHTS_AND_CROSSES_WIN_LINES:
        marks = [cells[index].get("mark") for index in line]
        if marks[0] and marks.count(marks[0]) == 3:
            return marks[0], list(line)
    return None, []


def finish_noughts_and_crosses_game(
    game: Game,
    ordered_players: list[dict],
    assignments: dict[int, str],
    marker: str,
) -> None:
    winning_team = TEAM_A if marker == NOUGHTS_AND_CROSSES_MARK_X else TEAM_B
    if game.team_mode == "teams":
        finish_game(game, winner_team=winning_team)
        return

    winner_player_id = next(
        (
            player["id"]
            for player in ordered_players
            if assignments.get(player["id"], TEAM_A) == winning_team
        ),
        None,
    )
    finish_game(game, winner_player_id=winner_player_id)


def team_label(team_key: str | None, team_names: dict[str, str] | None = None) -> str | None:
    names = team_names or default_team_names()
    if team_key == TEAM_A:
        return names.get(TEAM_A, "Team A")
    if team_key == TEAM_B:
        return names.get(TEAM_B, "Team B")
    return None


def reset_game_scores(score_rows: list[GameScore]) -> dict[int, GameScore]:
    """Reset persisted score rows before replaying turns from scratch."""
    score_by_player = {row.player_id: row for row in score_rows}
    for row in score_rows:
        row.fives = 0
    return score_by_player


def reset_game_progress(game: Game) -> None:
    """Return the game to an in-progress baseline ready for deterministic replay."""
    game.status = "active"
    game.current_turn_position = 0
    game.winner_player_id = None
    game.winner_team = None
    game.finished_at = None


def finish_game(game: Game, *, winner_player_id: int | None = None, winner_team: str | None = None) -> None:
    """Mark a replayed game as finished and record the winner."""
    game.status = "finished"
    game.winner_player_id = winner_player_id
    game.winner_team = winner_team
    game.finished_at = datetime.now(timezone.utc)


def apply_standard_turn(
    game: Game,
    turn: Turn,
    score_row: GameScore,
    assignments: dict[int, str],
    team_totals: dict[str, int],
) -> None:
    """Apply one 55 by 5 turn during replay."""
    _, counted, awarded = turn_result(turn.total_points)

    if game.team_mode == "teams":
        team = assignments.get(turn.player_id, TEAM_A)
        projected = team_totals[team] + awarded
        if counted and projected > 55:
            counted = False
            awarded = 0
        if counted:
            team_totals[team] = projected
            if projected == 55:
                finish_game(game, winner_team=team)
    else:
        projected = score_row.fives + awarded
        if counted and projected > 55:
            counted = False
            awarded = 0
        if counted and projected == 55:
            finish_game(game, winner_player_id=turn.player_id)

    turn.counted = counted
    turn.fives_awarded = awarded
    score_row.fives += awarded


def apply_cricket_turn(
    game: Game,
    turn: Turn,
    score_row: GameScore,
    assignments: dict[int, str],
    cricket_state: dict,
) -> None:
    """Apply one English Cricket turn during replay."""
    team = assignments.get(turn.player_id, TEAM_A)
    batting_team = cricket_state["batting_team"]
    bowling_team = cricket_state["bowling_team"]

    if team == batting_team:
        runs = max(turn.total_points - 40, 0)
        turn.counted = runs > 0
        turn.fives_awarded = runs
        score_row.fives += runs
        cricket_state["runs"][batting_team] += runs

        if cricket_state["inning"] == 2:
            chase_target = cricket_state["runs"][bowling_team]
            if cricket_state["runs"][batting_team] > chase_target:
                finish_game(game, winner_team=batting_team)
        return

    marks = max(0, turn.total_points)
    current_marks = cricket_state["wickets"][bowling_team]
    gained = min(marks, CRICKET_WICKET_TARGET - current_marks)
    turn.counted = gained > 0
    turn.fives_awarded = gained
    score_row.fives += gained
    cricket_state["wickets"][bowling_team] += gained

    if cricket_state["wickets"][bowling_team] < CRICKET_WICKET_TARGET:
        return

    if cricket_state["inning"] == 1:
        cricket_state["inning"] = 2
        cricket_state["batting_team"], cricket_state["bowling_team"] = (
            cricket_state["bowling_team"],
            cricket_state["batting_team"],
        )
        return

    team_a_runs = cricket_state["runs"][TEAM_A]
    team_b_runs = cricket_state["runs"][TEAM_B]
    if team_a_runs > team_b_runs:
        finish_game(game, winner_team=TEAM_A)
    elif team_b_runs > team_a_runs:
        finish_game(game, winner_team=TEAM_B)
    else:
        finish_game(game)


def apply_noughts_and_crosses_turn(
    game: Game,
    turn: Turn,
    ordered_players: list[dict],
    assignments: dict[int, str],
    noughts_state: dict,
) -> None:
    """Apply one Noughts and Crosses move during replay."""
    cells = noughts_state["cells"]
    cell_index = turn.total_points
    if not 0 <= cell_index < len(cells):
        return
    if cells[cell_index].get("mark"):
        return

    player_team = assignments.get(turn.player_id, TEAM_A)
    default_marker = marker_for_team(player_team)
    chosen_marker = normalize_noughts_marker(decode_noughts_marker(turn.dart_2), default_marker)

    cells[cell_index]["mark"] = chosen_marker
    turn.counted = True
    turn.fives_awarded = 0

    winner_marker, winning_line = check_noughts_and_crosses_winner(cells)
    if winner_marker:
        noughts_state["winner_marker"] = winner_marker
        noughts_state["winning_line"] = winning_line
        finish_noughts_and_crosses_game(game, ordered_players, assignments, winner_marker)
        return

    noughts_state["winner_marker"] = None
    noughts_state["winning_line"] = []
    if all(cell.get("mark") for cell in cells):
        finish_game(game)


def recompute_game_state(game: Game) -> None:
    """Replay every stored turn to rebuild scores, turn order, and winners."""
    ordered = game_ordered_players(game.id)
    if not ordered:
        return

    assignments = parse_team_assignments(game.team_assignments)
    score_rows = GameScore.query.filter_by(game_id=game.id).all()
    score_by_player = reset_game_scores(score_rows)

    reset_game_progress(game)

    stored_cricket_state = parse_cricket_state(game.cricket_state)
    stored_noughts_state = parse_noughts_and_crosses_state(game.noughts_and_crosses_state)
    if game.game_type == "english_cricket":
        cricket_state = build_initial_cricket_state(stored_cricket_state["starting_batting_team"])
        game.current_turn_position = starting_turn_position(ordered, assignments, cricket_state["bowling_team"])
    else:
        cricket_state = stored_cricket_state

    if game.game_type == "noughts_and_crosses":
        # Preserve generated board labels when replaying turns (e.g., undo) and only reset marks/outcome.
        noughts_state = stored_noughts_state
        for cell in noughts_state["cells"]:
            cell["mark"] = None
        noughts_state["winner_marker"] = None
        noughts_state["winning_line"] = []
    else:
        noughts_state = stored_noughts_state

    team_totals = {TEAM_A: 0, TEAM_B: 0}
    turns = Turn.query.filter_by(game_id=game.id).order_by(Turn.turn_number.asc()).all()

    for idx, turn in enumerate(turns, start=1):
        turn.turn_number = idx
        turn.counted = False
        turn.fives_awarded = 0

        if game.status != "active":
            continue

        expected_player_id = ordered[game.current_turn_position]["id"]
        if turn.player_id != expected_player_id:
            continue

        score_row = score_by_player.get(turn.player_id)
        if not score_row:
            continue

        if game.game_type == "english_cricket":
            apply_cricket_turn(game, turn, score_row, assignments, cricket_state)
        elif game.game_type == "noughts_and_crosses":
            apply_noughts_and_crosses_turn(game, turn, ordered, assignments, noughts_state)
        else:
            apply_standard_turn(game, turn, score_row, assignments, team_totals)

        if game.status == "active":
            game.current_turn_position = (game.current_turn_position + 1) % len(ordered)

    if game.game_type == "english_cricket":
        game.cricket_state = json.dumps(cricket_state)
    if game.game_type == "noughts_and_crosses":
        game.noughts_and_crosses_state = json.dumps(noughts_state)


def ensure_game_schema_columns() -> None:
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        return

    existing_columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(games)"))
    }
    statements: list[str] = []
    if "game_type" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN game_type VARCHAR(30) NOT NULL DEFAULT '55by5'")
    if "team_mode" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN team_mode VARCHAR(10) NOT NULL DEFAULT 'solo'")
    if "team_assignments" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN team_assignments TEXT")
    if "team_names" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN team_names TEXT")
    if "cricket_state" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN cricket_state TEXT")
    if "noughts_and_crosses_state" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN noughts_and_crosses_state TEXT")
    if "winner_team" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN winner_team VARCHAR(20)")

    for statement in statements:
        db.session.execute(text(statement))
    if statements:
        db.session.commit()


def game_ordered_players(game_id: int) -> list[dict]:
    rows = (
        db.session.query(GamePlayerOrder, Player)
        .join(Player, Player.id == GamePlayerOrder.player_id)
        .filter(GamePlayerOrder.game_id == game_id)
        .order_by(GamePlayerOrder.position.asc())
        .all()
    )
    return [{"id": p.id, "name": p.name, "position": o.position} for o, p in rows]


def game_scores_map(game_id: int) -> dict[int, int]:
    rows = GameScore.query.filter_by(game_id=game_id).all()
    return {row.player_id: row.fives for row in rows}


def active_player_id_for_game(game: Game, ordered_players: list[dict]) -> int | None:
    if game.status != "active" or not ordered_players:
        return None
    if not 0 <= game.current_turn_position < len(ordered_players):
        return None
    return ordered_players[game.current_turn_position]["id"]


def serialize_players_for_game(
    ordered_players: list[dict],
    scores: dict[int, int],
    assignments: dict[int, str],
) -> list[dict]:
    return [
        {
            "id": item["id"],
            "name": item["name"],
            "position": item["position"],
            "fives": scores.get(item["id"], 0),
            "team": assignments.get(item["id"]),
        }
        for item in ordered_players
    ]


def serialize_turns_for_game(game: Game) -> list[dict]:
    turns = (
        db.session.query(Turn, Player)
        .join(Player, Player.id == Turn.player_id)
        .filter(Turn.game_id == game.id)
        .order_by(Turn.turn_number.asc())
        .all()
    )
    noughts_state = parse_noughts_and_crosses_state(game.noughts_and_crosses_state) if game.game_type == "noughts_and_crosses" else {}
    return [
        {
            "turn_number": turn.turn_number,
            "player_id": turn.player_id,
            "player_name": player.name,
            "total_points": turn.total_points,
            "counted": turn.counted,
            "fives_awarded": turn.fives_awarded,
            "noughts_marker": decode_noughts_marker(turn.dart_2) if game.game_type == "noughts_and_crosses" else None,
            "board_index": turn.total_points if game.game_type == "noughts_and_crosses" else None,
            "board_label": noughts_state.get("cells", [])[turn.total_points].get("label") if game.game_type == "noughts_and_crosses" and 0 <= turn.total_points < 9 else None,
            "created_at": now_iso(turn.created_at),
        }
        for turn, player in turns
    ]


def noughts_side_name(
    ordered_players: list[dict],
    assignments: dict[int, str],
    team_names: dict[str, str],
    team_key: str,
    team_mode: str,
) -> str:
    if team_mode == "teams":
        return team_label(team_key, team_names) or ("Team X" if team_key == TEAM_A else "Team O")
    player = next((item for item in ordered_players if assignments.get(item["id"], TEAM_A) == team_key), None)
    return player["name"] if player else ("X" if team_key == TEAM_A else "O")


def serialize_game_state(game: Game) -> dict:
    """Return the full JSON game payload consumed by the UI and tests."""
    ordered_players = game_ordered_players(game.id)
    scores = game_scores_map(game.id)
    assignments = parse_team_assignments(game.team_assignments)
    team_names = parse_team_names(game.team_names)
    noughts_state = parse_noughts_and_crosses_state(game.noughts_and_crosses_state)
    if game.game_type == "noughts_and_crosses":
        noughts_state["x_name"] = noughts_side_name(ordered_players, assignments, team_names, TEAM_A, game.team_mode)
        noughts_state["o_name"] = noughts_side_name(ordered_players, assignments, team_names, TEAM_B, game.team_mode)

    return {
        "id": game.id,
        "status": game.status,
        "game_type": game.game_type,
        "team_mode": game.team_mode,
        "winner_team": game.winner_team,
        "winner_team_name": team_label(game.winner_team, team_names),
        "team_names": team_names,
        "current_turn_position": game.current_turn_position,
        "active_player_id": active_player_id_for_game(game, ordered_players),
        "winner_player_id": game.winner_player_id,
        "started_at": now_iso(game.started_at),
        "finished_at": now_iso(game.finished_at),
        "team_assignments": {str(k): v for k, v in assignments.items()},
        "cricket_state": parse_cricket_state(game.cricket_state) if game.game_type == "english_cricket" else None,
        "noughts_and_crosses_state": noughts_state if game.game_type == "noughts_and_crosses" else None,
        "players": serialize_players_for_game(ordered_players, scores, assignments),
        "turns": serialize_turns_for_game(game),
    }


def game_type_label(game_type: str | None) -> str:
    normalized = normalize_game_type(game_type)
    if normalized == "english_cricket":
        return "English Cricket"
    if normalized == "noughts_and_crosses":
        return "Noughts and Crosses"
    return "55 by 5"


def player_outcome_for_game(game: Game, player_id: int) -> str | None:
    if game.status != "finished":
        return None

    if game.team_mode == "teams":
        assignments = parse_team_assignments(game.team_assignments)
        player_team = assignments.get(player_id)
        if not player_team or not game.winner_team:
            return None
        return "won" if player_team == game.winner_team else "lost"

    if game.winner_player_id is None:
        return None
    return "won" if game.winner_player_id == player_id else "lost"


def build_player_stats(player: Player) -> dict:
    supported_game_types = ("55by5", "english_cricket", "noughts_and_crosses")
    by_game_type = {
        game_type: {
            "game_type": game_type,
            "label": game_type_label(game_type),
            "played": 0,
            "won": 0,
            "lost": 0,
        }
        for game_type in supported_game_types
    }

    games = (
        db.session.query(Game)
        .join(GamePlayerOrder, Game.id == GamePlayerOrder.game_id)
        .filter(GamePlayerOrder.player_id == player.id, Game.status == "finished")
        .order_by(Game.finished_at.desc().nullslast(), Game.id.desc())
        .all()
    )

    games_played = 0
    games_won = 0
    games_lost = 0

    for game in games:
        normalized_game_type = normalize_game_type(game.game_type)
        summary = by_game_type.setdefault(
            normalized_game_type,
            {
                "game_type": normalized_game_type,
                "label": game_type_label(normalized_game_type),
                "played": 0,
                "won": 0,
                "lost": 0,
            },
        )
        summary["played"] += 1
        games_played += 1

        outcome = player_outcome_for_game(game, player.id)
        if outcome == "won":
            summary["won"] += 1
            games_won += 1
        elif outcome == "lost":
            summary["lost"] += 1
            games_lost += 1

    win_rate = round((games_won / games_played) * 100, 1) if games_played else 0.0
    return {
        "games_played": games_played,
        "games_won": games_won,
        "games_lost": games_lost,
        "win_rate": win_rate,
        "by_game_type": [by_game_type[game_type] for game_type in supported_game_types],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method != "POST":
        if get_current_user() and not app.config.get("TESTING"):
            return redirect(url_for("index"))
        return render_template("login.html", error=None)

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    user = AppUser.query.filter(func.lower(AppUser.username) == username.lower()).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render_template("login.html", error="Invalid username or password."), 401

    session["user_id"] = user.id
    session["last_activity_at"] = current_session_timestamp()
    return redirect(url_for("index"))


@app.post("/logout")
def logout():
    if get_current_user():
        abandon_active_games()
    session.clear()
    return redirect(url_for("login"))


@app.get("/api/auth/me")
def auth_me():
    user = current_user_or_testing_admin()
    if not user:
        return jsonify({"error": "Authentication required."}), 401

    return jsonify({"id": user.id, "username": user.username, "is_admin": user.is_admin})


@app.get("/api/auth/users")
def list_app_users():
    user, error = require_admin_user()
    if error:
        return error

    users = AppUser.query.order_by(func.lower(AppUser.username).asc()).all()
    return jsonify(
        [
            {
                "id": item.id,
                "username": item.username,
                "is_admin": item.is_admin,
                "created_at": now_iso(item.created_at),
            }
            for item in users
        ]
    )


@app.post("/api/auth/users")
def create_app_user():
    user, error = require_admin_user()
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    is_admin = bool(payload.get("is_admin", False))

    if not username:
        return jsonify({"error": "Username is required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    existing = AppUser.query.filter(func.lower(AppUser.username) == username.lower()).first()
    if existing:
        return jsonify({"error": "A user with this username already exists."}), 400

    new_user = AppUser(
        username=username,
        password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
        is_admin=is_admin,
    )
    db.session.add(new_user)

    if not find_player_by_name(username):
        db.session.add(Player(name=username))

    db.session.commit()

    return jsonify({"id": new_user.id, "username": new_user.username, "is_admin": new_user.is_admin}), 201


@app.put("/api/auth/users/<int:user_id>/password")
def update_app_user_password(user_id: int):
    user, error = require_admin_user()
    if error:
        return error

    target_user = db.session.get(AppUser, user_id)
    if not target_user:
        return jsonify({"error": "User not found."}), 404

    payload = request.get_json(silent=True) or {}
    password = payload.get("password") or ""
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    target_user.password_hash = generate_password_hash(password, method="pbkdf2:sha256")
    db.session.commit()

    return jsonify(
        {
            "id": target_user.id,
            "username": target_user.username,
            "is_admin": target_user.is_admin,
        }
    )


@app.get("/api/meta")
def api_meta():
    return jsonify(
        {
            "valid_turn_total": {"min": 0, "max": MAX_TURN_TOTAL},
            "common_targets": [20, 15, 10, 5],
            "winning_fives": 55,
            "game_types": [
                {"id": "55by5", "name": "55 by 5"},
                {"id": "english_cricket", "name": "English Cricket"},
                {"id": "noughts_and_crosses", "name": "Noughts and Crosses"},
            ],
        }
    )


@app.get("/api/players")
def list_players():
    players = Player.query.order_by(Player.name.asc()).all()
    return jsonify(
        [
            {"id": player.id, "name": player.name, "created_at": now_iso(player.created_at)}
            for player in players
        ]
    )


@app.get("/api/players/<int:player_id>/stats")
def get_player_stats(player_id: int):
    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Player not found."}), 404

    return jsonify(
        {
            "player": {
                "id": player.id,
                "name": player.name,
                "created_at": now_iso(player.created_at),
            },
            "stats": build_player_stats(player),
        }
    )


@app.post("/api/players")
def create_player():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Player name is required."}), 400

    existing = find_player_by_name(name)
    if existing:
        return jsonify({"error": "A player with this name already exists."}), 400

    player = Player(name=name)
    db.session.add(player)
    db.session.commit()
    return jsonify({"id": player.id, "name": player.name}), 201


@app.put("/api/players/<int:player_id>")
def rename_player(player_id: int):
    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Player not found."}), 404

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Player name is required."}), 400

    existing = Player.query.filter(func.lower(Player.name) == name.lower(), Player.id != player_id).first()
    if existing:
        return jsonify({"error": "A player with this name already exists."}), 400

    player.name = name
    db.session.commit()
    return jsonify({"id": player.id, "name": player.name})


@app.delete("/api/players/<int:player_id>")
def delete_player(player_id: int):
    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Player not found."}), 404

    in_active_game = (
        db.session.query(GamePlayerOrder)
        .join(Game, Game.id == GamePlayerOrder.game_id)
        .filter(GamePlayerOrder.player_id == player_id, Game.status == "active")
        .first()
    )
    if in_active_game:
        return jsonify({"error": "Cannot delete a player who is in the active game."}), 400

    db.session.delete(player)
    db.session.commit()
    return jsonify({"ok": True})


@app.get("/api/games/active")
def get_active_game():
    game = Game.query.filter_by(status="active").order_by(Game.started_at.desc()).first()
    if not game:
        return jsonify({"game": None})
    return jsonify({"game": serialize_game_state(game)})


def validate_ordered_player_ids(raw_player_ids: object) -> tuple[list[int] | None, str | None]:
    """Validate the ordered player ids supplied for a new game."""
    if not isinstance(raw_player_ids, list) or not raw_player_ids:
        return None, "ordered_player_ids must be a non-empty list."
    if len(raw_player_ids) != len(set(raw_player_ids)):
        return None, "ordered_player_ids contains duplicate players."
    if any(not isinstance(player_id, int) for player_id in raw_player_ids):
        return None, "ordered_player_ids must contain integers."

    players = Player.query.filter(Player.id.in_(raw_player_ids)).all()
    if len(players) != len(raw_player_ids):
        return None, "One or more players were not found."
    return raw_player_ids, None


def normalize_requested_team_names(raw_team_names: object) -> tuple[dict[str, str] | None, str | None]:
    if raw_team_names and not isinstance(raw_team_names, dict):
        return None, "team_names must be an object when team mode is teams."

    team_names = default_team_names()
    if isinstance(raw_team_names, dict):
        for team_key, fallback in team_names.items():
            team_names[team_key] = normalize_team_name_value(raw_team_names.get(team_key), fallback)
    return team_names, None


def normalize_requested_team_assignments(
    game_type: str,
    team_mode: str,
    ordered_player_ids: list[int],
    raw_assignments: object,
) -> tuple[dict[int, str] | None, str | None]:
    normalized_assignments: dict[int, str] = {}

    if team_mode == "teams":
        if not isinstance(raw_assignments, dict):
            return None, "team_assignments must be an object when team mode is teams."

        for raw_player_id, team in raw_assignments.items():
            try:
                pid = int(raw_player_id)
            except (TypeError, ValueError):
                return None, "team_assignments contains invalid player id."
            if pid not in ordered_player_ids:
                return None, "team_assignments contains unknown player id."
            if team not in {TEAM_A, TEAM_B}:
                return None, "team_assignments must use team_a or team_b."
            normalized_assignments[pid] = team

        if len(normalized_assignments) != len(ordered_player_ids):
            return None, "Every selected player must be assigned to a team."
        if set(normalized_assignments.values()) != {TEAM_A, TEAM_B}:
            return None, "Both Team A and Team B must have at least one player."
        return normalized_assignments, None

    if game_type in {"english_cricket", "noughts_and_crosses"}:
        if len(ordered_player_ids) != 2:
            game_label = "English Cricket" if game_type == "english_cricket" else "Noughts and Crosses"
            return None, f"{game_label} in solo mode requires exactly two players."
        normalized_assignments[ordered_player_ids[0]] = TEAM_A
        normalized_assignments[ordered_player_ids[1]] = TEAM_B

    return normalized_assignments, None


def build_new_game_start_state(
    game_type: str,
    ordered_player_ids: list[int],
    normalized_assignments: dict[int, str],
    starting_batting_team: str | None,
) -> tuple[int, str | None, str | None]:
    if game_type == "english_cricket":
        opening_state = build_initial_cricket_state(starting_batting_team)
        ordered_for_start = [{"id": player_id} for player_id in ordered_player_ids]
        initial_turn_position = starting_turn_position(
            ordered_for_start,
            normalized_assignments,
            opening_state["bowling_team"],
        )
        return initial_turn_position, json.dumps(opening_state), None

    if game_type == "noughts_and_crosses":
        return 0, None, json.dumps(build_initial_noughts_and_crosses_state())

    return 0, None, None


@app.post("/api/games")
def create_game():
    if Game.query.filter_by(status="active").first():
        return jsonify({"error": "Finish the active game before starting a new one."}), 400

    payload = request.get_json(silent=True) or {}
    game_type = normalize_game_type(payload.get("game_type"))
    team_mode = normalize_team_mode(payload.get("team_mode"))

    ordered_player_ids, error = validate_ordered_player_ids(payload.get("ordered_player_ids") or [])
    if error:
        return jsonify({"error": error}), 400

    team_names, error = normalize_requested_team_names(payload.get("team_names") or {})
    if error:
        return jsonify({"error": error}), 400

    normalized_assignments, error = normalize_requested_team_assignments(
        game_type,
        team_mode,
        ordered_player_ids,
        payload.get("team_assignments") or {},
    )
    if error:
        return jsonify({"error": error}), 400

    initial_turn_position, cricket_state, noughts_and_crosses_state = build_new_game_start_state(
        game_type,
        ordered_player_ids,
        normalized_assignments,
        normalize_cricket_team(payload.get("starting_batting_team"), TEAM_A),
    )

    game = Game(
        status="active",
        game_type=game_type,
        team_mode=team_mode,
        team_assignments=json.dumps({str(k): v for k, v in normalized_assignments.items()}) if normalized_assignments else None,
        team_names=json.dumps(team_names) if team_mode == "teams" else None,
        cricket_state=cricket_state,
        noughts_and_crosses_state=noughts_and_crosses_state,
        current_turn_position=initial_turn_position,
    )
    db.session.add(game)
    db.session.flush()

    for index, player_id in enumerate(ordered_player_ids):
        db.session.add(GamePlayerOrder(game_id=game.id, player_id=player_id, position=index))
        db.session.add(GameScore(game_id=game.id, player_id=player_id, fives=0))

    db.session.commit()
    return jsonify({"game": serialize_game_state(game)}), 201


@app.post("/api/games/<int:game_id>/turn")
def submit_turn(game_id: int):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found."}), 404
    if game.status != "active":
        return jsonify({"error": "This game is already finished."}), 400

    ordered = game_ordered_players(game.id)
    if not ordered:
        return jsonify({"error": "Game has no players."}), 400

    expected_player_id = ordered[game.current_turn_position]["id"]

    payload = request.get_json(silent=True) or {}
    player_id = payload.get("player_id")
    raw_total = payload.get("total_points")

    if player_id != expected_player_id:
        return jsonify({"error": "It is not this player's turn."}), 400
    total_points, err = normalize_total_points(raw_total)
    if err:
        return jsonify({"error": err}), 400

    noughts_marker = None
    if game.game_type == "noughts_and_crosses":
        if not 0 <= total_points < 9:
            return jsonify({"error": "Select a valid board square."}), 400
        noughts_marker = normalize_noughts_marker(payload.get("noughts_marker"), None)

    turn_count = Turn.query.filter_by(game_id=game.id).count()
    turn = Turn(
        game_id=game.id,
        player_id=player_id,
        turn_number=turn_count + 1,
        dart_1=total_points,
        dart_2=encode_noughts_marker(noughts_marker) if game.game_type == "noughts_and_crosses" else 0,
        dart_3=0,
        total_points=total_points,
        counted=False,
        fives_awarded=0,
    )
    db.session.add(turn)

    recompute_game_state(game)

    db.session.commit()

    return jsonify(
        {
            "turn": {
                "turn_number": turn.turn_number,
                "player_id": player_id,
                "total_points": turn.total_points,
                "counted": turn.counted,
                "fives_awarded": turn.fives_awarded,
            },
            "game": serialize_game_state(game),
        }
    )


@app.delete("/api/games/<int:game_id>/turn")
def undo_last_turn(game_id: int):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found."}), 404
    if game.status not in ("active",):
        return jsonify({"error": "Cannot undo a finished game."}), 400

    last_turn = Turn.query.filter_by(game_id=game_id).order_by(Turn.turn_number.desc()).first()
    if not last_turn:
        return jsonify({"error": "No turns to undo."}), 400

    db.session.delete(last_turn)
    db.session.flush()
    recompute_game_state(game)
    db.session.commit()

    return jsonify({"game": serialize_game_state(game)})


@app.delete("/api/games/<int:game_id>")
def quit_game(game_id: int):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found."}), 404
    if game.status != "active":
        return jsonify({"error": "Only active games can be quit."}), 400

    game.status = "abandoned"
    game.finished_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"ok": True})


@app.get("/api/games/history")
def games_history():
    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(100, limit))

    games = (
        Game.query.filter_by(status="finished")
        .order_by(Game.finished_at.desc().nullslast(), Game.id.desc())
        .limit(limit)
        .all()
    )

    result = []
    for game in games:
        winner_name = None
        if game.winner_player_id:
            winner = db.session.get(Player, game.winner_player_id)
            winner_name = winner.name if winner else None

        participants = game_ordered_players(game.id)
        turn_count = Turn.query.filter_by(game_id=game.id).count()

        result.append(
            {
                "id": game.id,
                "game_type": game.game_type,
                "team_mode": game.team_mode,
                "winner_team": game.winner_team,
                "winner_team_name": team_label(game.winner_team, parse_team_names(game.team_names)),
                "winner_player_id": game.winner_player_id,
                "winner_name": winner_name,
                "started_at": now_iso(game.started_at),
                "finished_at": now_iso(game.finished_at),
                "turn_count": turn_count,
                "participants": participants,
            }
        )

    return jsonify(result)


@app.delete("/api/games/history")
def delete_games_history():
    user, error = require_admin_user()
    if error:
        return error

    game_ids = [row.id for row in Game.query.filter_by(status="finished").all()]
    if not game_ids:
        return jsonify({"deleted_games": 0})

    Turn.query.filter(Turn.game_id.in_(game_ids)).delete(synchronize_session=False)
    GameScore.query.filter(GameScore.game_id.in_(game_ids)).delete(synchronize_session=False)
    GamePlayerOrder.query.filter(GamePlayerOrder.game_id.in_(game_ids)).delete(synchronize_session=False)
    Game.query.filter(Game.id.in_(game_ids)).delete(synchronize_session=False)
    db.session.commit()

    return jsonify({"deleted_games": len(game_ids)})


@app.get("/api/games/<int:game_id>/state")
def game_state(game_id: int):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found."}), 404
    return jsonify({"game": serialize_game_state(game)})


@app.get("/api/games/<int:game_id>/history")
def game_history_detail(game_id: int):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found."}), 404

    data = serialize_game_state(game)
    return jsonify({"game": data})


with app.app_context():
    db.create_all()
    ensure_game_schema_columns()
    ensure_admin_user()


if __name__ == "__main__":
    app.run(debug=True)
