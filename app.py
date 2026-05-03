from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path

from flask import Flask, g, got_request_exception, jsonify, redirect, render_template, request, session, url_for
from flask.cli import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_, text
from werkzeug.security import check_password_hash, generate_password_hash

from game_logic import (
    MAX_TURN_TOTAL,
    TEAM_A,
    TEAM_B,
    build_game_state_payload,
    build_new_game_start_state,
    decode_x01_turn_result,
    encode_noughts_marker,
    game_type_label,
    normalize_cricket_team,
    normalize_game_type,
    normalize_noughts_marker,
    normalize_requested_team_assignments,
    normalize_requested_team_names,
    normalize_team_mode,
    normalize_total_points,
    normalize_x01_starting_score,
    parse_cricket_state,
    parse_noughts_and_crosses_state,
    parse_team_assignments,
    parse_team_names,
    parse_x01_state,
    player_outcome_for_game,
    recompute_game_state as replay_game_state,
    serialize_turns_for_game as serialize_turn_rows_for_game,
    team_label,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "darts.db"

load_dotenv(BASE_DIR / ".env")


class SuppressPlayersAccessLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return should_log_werkzeug_message(record.getMessage())


def should_log_werkzeug_message(message: str) -> bool:
    return 'GET /api/players HTTP/1.1' not in message


def configure_logging(flask_app: Flask) -> None:
    log_level_name = os.getenv("APP_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    flask_app.logger.setLevel(log_level)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(log_level)
    if not any(isinstance(log_filter, SuppressPlayersAccessLogFilter) for log_filter in werkzeug_logger.filters):
        werkzeug_logger.addFilter(SuppressPlayersAccessLogFilter())


def log_unhandled_request_exception(sender: Flask, exception: Exception, **extra) -> None:
    current_user = getattr(g, "current_user", None)
    user_id = getattr(current_user, "id", None)
    forwarded_for = request.headers.get("X-Forwarded-For")
    remote_addr = forwarded_for or request.remote_addr or "-"
    sender.logger.exception(
        "Unhandled request exception: method=%s path=%s user_id=%s remote_addr=%s",
        request.method,
        request.path,
        user_id,
        remote_addr,
    )

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", "change-this-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{DB_PATH}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_SORT_KEYS"] = False

configure_logging(app)
got_request_exception.connect(log_unhandled_request_exception, app)

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
    owner_user_id = db.Column(db.Integer, db.ForeignKey("app_users.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")
    game_type = db.Column(db.String(30), nullable=False, default="55by5")
    team_mode = db.Column(db.String(10), nullable=False, default="solo")
    team_assignments = db.Column(db.Text, nullable=True)
    team_names = db.Column(db.Text, nullable=True)
    cricket_state = db.Column(db.Text, nullable=True)
    noughts_and_crosses_state = db.Column(db.Text, nullable=True)
    x01_state = db.Column(db.Text, nullable=True)
    winner_team = db.Column(db.String(20), nullable=True)
    current_turn_position = db.Column(db.Integer, nullable=False, default=0)
    winner_player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=True)
    history_hidden = db.Column(db.Boolean, nullable=False, default=False)
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


def visible_games_query(user: AppUser | None = None):
    scoped_user = user or get_current_user()
    if scoped_user:
        return Game.query.filter(
            or_(Game.owner_user_id == scoped_user.id, Game.owner_user_id.is_(None))
        )
    if app.config.get("TESTING"):
        return Game.query
    return Game.query.filter(Game.id.is_(None))


def active_games_query(user: AppUser | None = None):
    return visible_games_query(user).filter_by(status="active")


def active_player_ids() -> set[int]:
    return {
        player_id
        for (player_id,) in (
            db.session.query(GamePlayerOrder.player_id)
            .join(Game, Game.id == GamePlayerOrder.game_id)
            .filter(Game.status == "active")
            .distinct()
            .all()
        )
    }


def active_players_for_ids(player_ids: list[int]) -> list[Player]:
    if not player_ids:
        return []
    return (
        Player.query.join(GamePlayerOrder, GamePlayerOrder.player_id == Player.id)
        .join(Game, Game.id == GamePlayerOrder.game_id)
        .filter(Player.id.in_(player_ids), Game.status == "active")
        .order_by(Player.name.asc())
        .distinct()
        .all()
    )


def get_game_for_request(game_id: int) -> Game | None:
    user = get_current_user()
    if user:
        return Game.query.filter(
            Game.id == game_id,
            or_(Game.owner_user_id == user.id, Game.owner_user_id.is_(None)),
        ).first()
    if app.config.get("TESTING"):
        return db.session.get(Game, game_id)
    return None


def abandon_active_games(user: AppUser | None = None) -> int:
    games = active_games_query(user).all()
    return abandon_games(games)


def abandon_expired_games(timeout_seconds: int = SESSION_IDLE_TIMEOUT_SECONDS, user: AppUser | None = None, global_scope: bool = False) -> int:
    threshold = normalize_utc_datetime(datetime.now(timezone.utc)) - timedelta(seconds=timeout_seconds)
    stale_games: list[Game] = []

    games_query = Game.query.filter_by(status="active") if global_scope else active_games_query(user)
    for game in games_query.all():
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

    if request.endpoint != "static" and (g.current_user or app.config.get("TESTING")):
        abandon_expired_games(global_scope=True)

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
    if "owner_user_id" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN owner_user_id INTEGER")
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
    if "x01_state" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN x01_state TEXT")
    if "winner_team" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN winner_team VARCHAR(20)")
    if "history_hidden" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN history_hidden BOOLEAN NOT NULL DEFAULT 0")

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


def serialize_turns_for_game(game: Game) -> list[dict]:
    turn_rows = (
        db.session.query(Turn, Player)
        .join(Player, Player.id == Turn.player_id)
        .filter(Turn.game_id == game.id)
        .order_by(Turn.turn_number.asc())
        .all()
    )
    return serialize_turn_rows_for_game(turn_rows, game)


def serialize_game_state(game: Game) -> dict:
    ordered_players = game_ordered_players(game.id)
    scores = game_scores_map(game.id)
    turn_rows = (
        db.session.query(Turn, Player)
        .join(Player, Player.id == Turn.player_id)
        .filter(Turn.game_id == game.id)
        .order_by(Turn.turn_number.asc())
        .all()
    )
    return build_game_state_payload(
        game,
        ordered_players=ordered_players,
        scores=scores,
        turn_rows=turn_rows,
    )


def recompute_game_state(game: Game) -> None:
    ordered_players = game_ordered_players(game.id)
    score_rows = GameScore.query.filter_by(game_id=game.id).all()
    turns = Turn.query.filter_by(game_id=game.id).order_by(Turn.turn_number.asc()).all()
    replay_game_state(
        game,
        ordered_players=ordered_players,
        score_rows=score_rows,
        turns=turns,
    )


def build_player_stats(player: Player) -> dict:
    supported_game_types = ("x01", "55by5", "english_cricket", "noughts_and_crosses")
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
    current_user = get_current_user()
    if current_user:
        abandon_active_games(current_user)
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
                {"id": "x01", "name": "X01"},
                {"id": "55by5", "name": "55 by 5"},
                {"id": "english_cricket", "name": "English Cricket"},
                {"id": "noughts_and_crosses", "name": "Noughts and Crosses"},
            ],
        }
    )


@app.get("/api/players")
def list_players():
    busy_player_ids = active_player_ids()
    players = Player.query.order_by(Player.name.asc()).all()
    return jsonify(
        [
            {
                "id": player.id,
                "name": player.name,
                "created_at": now_iso(player.created_at),
                "is_busy": player.id in busy_player_ids,
            }
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
    user, error = require_admin_user()
    if error:
        return error

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
    game = active_games_query().order_by(Game.started_at.desc()).first()
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


@app.post("/api/games")
def create_game():
    if active_games_query().first():
        return jsonify({"error": "Finish the active game before starting a new one."}), 400

    payload = request.get_json(silent=True) or {}
    game_type = normalize_game_type(payload.get("game_type"))
    team_mode = normalize_team_mode(payload.get("team_mode"))
    x01_starting_score = normalize_x01_starting_score(payload.get("x01_starting_score"), 501)

    ordered_player_ids, error = validate_ordered_player_ids(payload.get("ordered_player_ids") or [])
    if error:
        return jsonify({"error": error}), 400

    busy_players = active_players_for_ids(ordered_player_ids)
    if busy_players:
        busy_player_names = ", ".join(player.name for player in busy_players)
        verb = "is" if len(busy_players) == 1 else "are"
        return jsonify({"error": f"{busy_player_names} {verb} already in an active game."}), 400

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

    initial_turn_position, cricket_state, noughts_and_crosses_state, x01_state = build_new_game_start_state(
        game_type,
        ordered_player_ids,
        normalized_assignments,
        team_mode,
        normalize_cricket_team(payload.get("starting_batting_team"), TEAM_A),
        x01_starting_score,
    )

    game = Game(
        owner_user_id=get_current_user().id if get_current_user() else None,
        status="active",
        game_type=game_type,
        team_mode=team_mode,
        team_assignments=json.dumps({str(k): v for k, v in normalized_assignments.items()}) if normalized_assignments else None,
        team_names=json.dumps(team_names) if team_mode == "teams" else None,
        cricket_state=cricket_state,
        noughts_and_crosses_state=noughts_and_crosses_state,
        x01_state=x01_state,
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
    game = get_game_for_request(game_id)
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
        dart_1=0 if game.game_type == "x01" else total_points,
        dart_2=(
            encode_noughts_marker(noughts_marker) if game.game_type == "noughts_and_crosses"
            else 0
        ),
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
                "x01_result": decode_x01_turn_result(turn.dart_3) if game.game_type == "x01" else None,
            },
            "game": serialize_game_state(game),
        }
    )


@app.delete("/api/games/<int:game_id>/turn")
def undo_last_turn(game_id: int):
    game = get_game_for_request(game_id)
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
    game = get_game_for_request(game_id)
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

    base_query = visible_games_query().filter_by(status="finished", history_hidden=False)
    total = base_query.count()

    games = (
        base_query
        .order_by(Game.finished_at.desc().nullslast(), Game.id.desc())
        .limit(limit)
        .all()
    )

    # Pre-fetch all winner names in one query to avoid an N+1 per game.
    winner_player_ids = {g.winner_player_id for g in games if g.winner_player_id}
    winner_names: dict[int, str] = {}
    if winner_player_ids:
        for player in Player.query.filter(Player.id.in_(winner_player_ids)).all():
            winner_names[player.id] = player.name

    result = []
    for index, game in enumerate(games):
        winner_name = winner_names.get(game.winner_player_id) if game.winner_player_id else None

        participants = game_ordered_players(game.id)
        turn_count = Turn.query.filter_by(game_id=game.id).count()

        result.append(
            {
                "id": game.id,
                "sequence_number": total - index,
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

    games = Game.query.filter_by(status="finished", history_hidden=False).all()
    if not games:
        return jsonify({"deleted_games": 0})

    for game in games:
        game.history_hidden = True
    db.session.commit()

    return jsonify({"deleted_games": len(games)})


@app.get("/api/games/<int:game_id>/state")
def game_state(game_id: int):
    game = get_game_for_request(game_id)
    if not game:
        return jsonify({"error": "Game not found."}), 404
    return jsonify({"game": serialize_game_state(game)})


@app.get("/api/games/<int:game_id>/history")
def game_history_detail(game_id: int):
    game = get_game_for_request(game_id)
    if not game:
        return jsonify({"error": "Game not found."}), 404

    data = serialize_game_state(game)
    return jsonify({"game": data})


with app.app_context():
    db.create_all()
    ensure_game_schema_columns()
    ensure_admin_user()


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", os.getenv("PORT", "5000")))
    app.run(debug=True, host=host, port=port)
