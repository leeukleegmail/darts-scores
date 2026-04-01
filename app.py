from __future__ import annotations

from datetime import datetime, timezone
import json
import os
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
    cricket_state = db.Column(db.Text, nullable=True)
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

    if app.config.get("TESTING"):
        return None

    if request.endpoint == "static":
        return None

    if request.path in {"/login", "/logout"}:
        return None

    if g.current_user:
        return None

    if request.path.startswith("/api/"):
        return jsonify({"error": "Authentication required."}), 401

    return redirect(url_for("login"))


MAX_TURN_TOTAL = 180
CRICKET_WICKET_TARGET = 10
TEAM_A = "team_a"
TEAM_B = "team_b"


def normalize_game_type(raw_type: str | None) -> str:
    game_type = (raw_type or "55by5").strip().lower()
    return "english_cricket" if game_type == "english_cricket" else "55by5"


def normalize_team_mode(raw_mode: str | None) -> str:
    team_mode = (raw_mode or "solo").strip().lower()
    return "teams" if team_mode == "teams" else "solo"


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


def parse_cricket_state(raw_value: str | None) -> dict:
    default_state = {
        "inning": 1,
        "batting_team": TEAM_A,
        "bowling_team": TEAM_B,
        "runs": {TEAM_A: 0, TEAM_B: 0},
        "wickets": {TEAM_A: 0, TEAM_B: 0},
    }
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
    batting_team = decoded.get("batting_team", TEAM_A)
    bowling_team = decoded.get("bowling_team", TEAM_B)
    if batting_team not in {TEAM_A, TEAM_B}:
        batting_team = TEAM_A
    if bowling_team not in {TEAM_A, TEAM_B}:
        bowling_team = TEAM_B

    runs = decoded.get("runs", {}) or {}
    wickets = decoded.get("wickets", {}) or {}
    return {
        "inning": inning,
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


def team_label(team_key: str | None) -> str | None:
    if team_key == TEAM_A:
        return "Team A"
    if team_key == TEAM_B:
        return "Team B"
    return None


def recompute_game_state(game: Game) -> None:
    ordered = game_ordered_players(game.id)
    if not ordered:
        return

    assignments = parse_team_assignments(game.team_assignments)
    score_rows = GameScore.query.filter_by(game_id=game.id).all()
    score_by_player = {row.player_id: row for row in score_rows}
    for row in score_rows:
        row.fives = 0

    game.status = "active"
    game.current_turn_position = 0
    game.winner_player_id = None
    game.winner_team = None
    game.finished_at = None

    cricket_state = parse_cricket_state(game.cricket_state)
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
                        game.status = "finished"
                        game.winner_team = batting_team
                        game.finished_at = datetime.now(timezone.utc)
            else:
                marks = max(0, turn.total_points)
                current_marks = cricket_state["wickets"][bowling_team]
                gained = min(marks, CRICKET_WICKET_TARGET - current_marks)
                turn.counted = gained > 0
                turn.fives_awarded = gained
                score_row.fives += gained
                cricket_state["wickets"][bowling_team] += gained

                if cricket_state["wickets"][bowling_team] >= CRICKET_WICKET_TARGET:
                    if cricket_state["inning"] == 1:
                        cricket_state["inning"] = 2
                        cricket_state["batting_team"], cricket_state["bowling_team"] = (
                            cricket_state["bowling_team"],
                            cricket_state["batting_team"],
                        )
                    else:
                        game.status = "finished"
                        team_a_runs = cricket_state["runs"][TEAM_A]
                        team_b_runs = cricket_state["runs"][TEAM_B]
                        if team_a_runs > team_b_runs:
                            game.winner_team = TEAM_A
                        elif team_b_runs > team_a_runs:
                            game.winner_team = TEAM_B
                        game.finished_at = datetime.now(timezone.utc)
        else:
            counted = turn.total_points % 5 == 0
            awarded = turn.total_points // 5 if counted else 0

            if game.team_mode == "teams":
                team = assignments.get(turn.player_id, TEAM_A)
                projected = team_totals[team] + awarded
                if counted and projected > 55:
                    counted = False
                    awarded = 0
                if counted:
                    team_totals[team] = projected
                    if projected == 55:
                        game.status = "finished"
                        game.winner_team = team
                        game.finished_at = datetime.now(timezone.utc)
            else:
                projected = score_row.fives + awarded
                if counted and projected > 55:
                    counted = False
                    awarded = 0
                if counted and projected == 55:
                    game.status = "finished"
                    game.winner_player_id = turn.player_id
                    game.finished_at = datetime.now(timezone.utc)

            turn.counted = counted
            turn.fives_awarded = awarded
            score_row.fives += awarded

        if game.status == "active":
            game.current_turn_position = (game.current_turn_position + 1) % len(ordered)

    if game.game_type == "english_cricket":
        game.cricket_state = json.dumps(cricket_state)


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
    if "cricket_state" not in existing_columns:
        statements.append("ALTER TABLE games ADD COLUMN cricket_state TEXT")
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


def serialize_game_state(game: Game) -> dict:
    ordered_players = game_ordered_players(game.id)
    scores = game_scores_map(game.id)
    assignments = parse_team_assignments(game.team_assignments)
    cricket_state = parse_cricket_state(game.cricket_state)
    active_player_id = None
    if game.status == "active" and ordered_players:
        active_player_id = ordered_players[game.current_turn_position]["id"]

    turns = (
        db.session.query(Turn, Player)
        .join(Player, Player.id == Turn.player_id)
        .filter(Turn.game_id == game.id)
        .order_by(Turn.turn_number.asc())
        .all()
    )

    return {
        "id": game.id,
        "status": game.status,
        "game_type": game.game_type,
        "team_mode": game.team_mode,
        "winner_team": game.winner_team,
        "winner_team_name": team_label(game.winner_team),
        "current_turn_position": game.current_turn_position,
        "active_player_id": active_player_id,
        "winner_player_id": game.winner_player_id,
        "started_at": now_iso(game.started_at),
        "finished_at": now_iso(game.finished_at),
        "team_assignments": {str(k): v for k, v in assignments.items()},
        "cricket_state": cricket_state if game.game_type == "english_cricket" else None,
        "players": [
            {
                "id": item["id"],
                "name": item["name"],
                "position": item["position"],
                "fives": scores.get(item["id"], 0),
                "team": assignments.get(item["id"]),
            }
            for item in ordered_players
        ],
        "turns": [
            {
                "turn_number": turn.turn_number,
                "player_id": turn.player_id,
                "player_name": player.name,
                "total_points": turn.total_points,
                "counted": turn.counted,
                "fives_awarded": turn.fives_awarded,
                "created_at": now_iso(turn.created_at),
            }
            for turn, player in turns
        ],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if get_current_user() and not app.config.get("TESTING"):
            return redirect(url_for("index"))
        return render_template("login.html", error=None)

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    user = AppUser.query.filter(func.lower(AppUser.username) == username.lower()).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render_template("login.html", error="Invalid username or password."), 401

    session["user_id"] = user.id
    return redirect(url_for("index"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/api/auth/me")
def auth_me():
    user = current_user_or_testing_admin()
    if not user:
        return jsonify({"error": "Authentication required."}), 401

    return jsonify({"id": user.id, "username": user.username, "is_admin": user.is_admin})


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
    db.session.commit()

    return jsonify({"id": new_user.id, "username": new_user.username, "is_admin": new_user.is_admin}), 201


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


@app.post("/api/players")
def create_player():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Player name is required."}), 400

    existing = Player.query.filter(func.lower(Player.name) == name.lower()).first()
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


@app.post("/api/games")
def create_game():
    if Game.query.filter_by(status="active").first():
        return jsonify({"error": "Finish the active game before starting a new one."}), 400

    payload = request.get_json(silent=True) or {}
    game_type = normalize_game_type(payload.get("game_type"))
    team_mode = normalize_team_mode(payload.get("team_mode"))
    ordered_player_ids = payload.get("ordered_player_ids") or []
    if not isinstance(ordered_player_ids, list) or not ordered_player_ids:
        return jsonify({"error": "ordered_player_ids must be a non-empty list."}), 400

    if len(ordered_player_ids) != len(set(ordered_player_ids)):
        return jsonify({"error": "ordered_player_ids contains duplicate players."}), 400

    players = Player.query.filter(Player.id.in_(ordered_player_ids)).all()
    if len(players) != len(ordered_player_ids):
        return jsonify({"error": "One or more players were not found."}), 400

    raw_assignments = payload.get("team_assignments") or {}
    normalized_assignments: dict[int, str] = {}
    if team_mode == "teams":
        if not isinstance(raw_assignments, dict):
            return jsonify({"error": "team_assignments must be an object when team mode is teams."}), 400
        for raw_player_id, team in raw_assignments.items():
            try:
                pid = int(raw_player_id)
            except (TypeError, ValueError):
                return jsonify({"error": "team_assignments contains invalid player id."}), 400
            if pid not in ordered_player_ids:
                return jsonify({"error": "team_assignments contains unknown player id."}), 400
            if team not in {TEAM_A, TEAM_B}:
                return jsonify({"error": "team_assignments must use team_a or team_b."}), 400
            normalized_assignments[pid] = team

        if len(normalized_assignments) != len(ordered_player_ids):
            return jsonify({"error": "Every selected player must be assigned to a team."}), 400
        if set(normalized_assignments.values()) != {TEAM_A, TEAM_B}:
            return jsonify({"error": "Both Team A and Team B must have at least one player."}), 400
    elif game_type == "english_cricket":
        if len(ordered_player_ids) != 2:
            return jsonify({"error": "English Cricket in solo mode requires exactly two players."}), 400
        normalized_assignments[ordered_player_ids[0]] = TEAM_A
        normalized_assignments[ordered_player_ids[1]] = TEAM_B

    cricket_state = None
    if game_type == "english_cricket":
        cricket_state = json.dumps(
            {
                "inning": 1,
                "batting_team": TEAM_A,
                "bowling_team": TEAM_B,
                "runs": {TEAM_A: 0, TEAM_B: 0},
                "wickets": {TEAM_A: 0, TEAM_B: 0},
            }
        )

    game = Game(
        status="active",
        game_type=game_type,
        team_mode=team_mode,
        team_assignments=json.dumps({str(k): v for k, v in normalized_assignments.items()}) if normalized_assignments else None,
        cricket_state=cricket_state,
        current_turn_position=0,
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

    turn_count = Turn.query.filter_by(game_id=game.id).count()
    turn = Turn(
        game_id=game.id,
        player_id=player_id,
        turn_number=turn_count + 1,
        dart_1=total_points,
        dart_2=0,
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
                "winner_team_name": team_label(game.winner_team),
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
