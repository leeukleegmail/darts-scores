import importlib
import sys
import tempfile

import pytest


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="darts-test-") as db_dir:
        db_path = f"{db_dir}/test.db"

        monkeypatch.setenv("FLASK_ENV", "testing")
        monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_path}")

        sys.modules.pop("app", None)
        app_module = importlib.import_module("app")
        app, db = app_module.app, app_module.db

        app.config.update(
            {
                "TESTING": True,
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            }
        )

        with app.app_context():
            db.drop_all()
            db.create_all()

        with app.test_client() as test_client:
            yield test_client


@pytest.fixture()
def auth_client(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="darts-auth-test-") as db_dir:
        db_path = f"{db_dir}/test.db"

        monkeypatch.setenv("FLASK_ENV", "development")
        monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_path}")
        monkeypatch.setenv("APP_ADMIN_USERNAME", "admin")
        monkeypatch.setenv("APP_ADMIN_PASSWORD", "admin")

        sys.modules.pop("app", None)
        app_module = importlib.import_module("app")
        app, db = app_module.app, app_module.db

        app.config.update(
            {
                "TESTING": False,
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            }
        )

        with app.app_context():
            db.drop_all()
            db.create_all()
            app_module.ensure_admin_user()

        with app.test_client() as test_client:
            yield test_client


@pytest.fixture()
def client_with_module(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="darts-module-test-") as db_dir:
        db_path = f"{db_dir}/test.db"

        monkeypatch.setenv("FLASK_ENV", "testing")
        monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_path}")

        sys.modules.pop("app", None)
        app_module = importlib.import_module("app")
        app, db = app_module.app, app_module.db

        app.config.update(
            {
                "TESTING": True,
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            }
        )

        with app.app_context():
            db.drop_all()
            db.create_all()

        with app.test_client() as test_client:
            yield test_client, app_module


def add_player(client, name):
    res = client.post("/api/players", json={"name": name})
    assert res.status_code == 201
    return res.get_json()["id"]


def test_turn_scoring_divisible_by_five(client):
    alice = add_player(client, "Alice")
    game = client.post("/api/games", json={"ordered_player_ids": [alice]}).get_json()["game"]

    res = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": alice, "total_points": 20},
    )
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["turn"]["counted"] is True
    assert payload["turn"]["fives_awarded"] == 4


def test_turn_scoring_not_divisible_by_five(client):
    alice = add_player(client, "Alice")
    game = client.post("/api/games", json={"ordered_player_ids": [alice]}).get_json()["game"]

    res = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": alice, "total_points": 3},
    )
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["turn"]["counted"] is False
    assert payload["turn"]["fives_awarded"] == 0


def test_first_to_55_fives_wins(client):
    alice = add_player(client, "Alice")
    bob = add_player(client, "Bob")
    game = client.post("/api/games", json={"ordered_player_ids": [alice, bob]}).get_json()["game"]

    # 13 rounds of 20 pts (4 fives each) -> 52 fives for Alice
    for _ in range(13):
        a_turn = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": alice, "total_points": 20},
        )
        assert a_turn.status_code == 200

        b_turn = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": bob, "total_points": 0},
        )
        assert b_turn.status_code == 200

    # 15 pts (3 fives) -> 52 + 3 = 55 exactly -> win
    final = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": alice, "total_points": 15},
    )
    assert final.status_code == 200
    final_payload = final.get_json()

    assert final_payload["game"]["status"] == "finished"
    assert final_payload["game"]["winner_player_id"] == alice


def test_bust_when_exceeding_55(client):
    alice = add_player(client, "Alice")
    game = client.post("/api/games", json={"ordered_player_ids": [alice]}).get_json()["game"]

    # 13 turns of 20 (52 fives) + 1 turn of 5 (1 five) = 53 fives
    for _ in range(13):
        client.post(f"/api/games/{game['id']}/turn", json={"player_id": alice, "total_points": 20})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": alice, "total_points": 5})

    # Score is now 53; scoring 25 (5 fives) would push to 58 -> bust
    bust = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": alice, "total_points": 25},
    )
    assert bust.status_code == 200
    payload = bust.get_json()
    assert payload["turn"]["counted"] is False
    assert payload["turn"]["fives_awarded"] == 0
    assert payload["game"]["status"] == "active"
    alice_score = next(p for p in payload["game"]["players"] if p["id"] == alice)
    assert alice_score["fives"] == 53


def test_game_history_persists(client):
    p1 = add_player(client, "P1")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]

    # 11 turns of 25 (5 fives each) = 55 fives exactly -> game finishes
    for _ in range(11):
        client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})

    history = client.get("/api/games/history?limit=10")
    assert history.status_code == 200
    games = history.get_json()
    assert len(games) == 1
    assert games[0]["winner_player_id"] == p1


def test_quit_active_game(client):
    p1 = add_player(client, "Quitter")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]

    quit_res = client.delete(f"/api/games/{game['id']}")
    assert quit_res.status_code == 200
    assert quit_res.get_json()["ok"] is True

    active = client.get("/api/games/active")
    assert active.status_code == 200
    assert active.get_json()["game"] is None

    # Starting another game should now be allowed.
    next_game = client.post("/api/games", json={"ordered_player_ids": [p1]})
    assert next_game.status_code == 201


def test_admin_can_delete_history(client):
    p1 = add_player(client, "Hist1")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]

    # 11 turns of 25 (5 fives each) = 55 fives exactly -> game finishes
    for _ in range(11):
        client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})

    before = client.get("/api/games/history?limit=10")
    assert before.status_code == 200
    assert len(before.get_json()) == 1

    deleted = client.delete("/api/games/history")
    assert deleted.status_code == 200
    assert deleted.get_json()["deleted_games"] == 1

    after = client.get("/api/games/history?limit=10")
    assert after.status_code == 200
    assert after.get_json() == []


def test_api_requires_auth_when_not_testing(auth_client):
    res = auth_client.get("/api/players")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Authentication required."


def test_admin_login_can_create_user(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    create_user = auth_client.post(
        "/api/auth/users",
        json={"username": "viewer", "password": "viewerpass", "is_admin": False},
    )
    assert create_user.status_code == 201
    assert create_user.get_json()["username"] == "viewer"


def test_non_admin_cannot_clear_history(auth_client):
    admin_login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert admin_login.status_code == 302

    created = auth_client.post(
        "/api/auth/users",
        json={"username": "player1", "password": "playerpass", "is_admin": False},
    )
    assert created.status_code == 201

    auth_client.post("/logout", follow_redirects=False)

    user_login = auth_client.post(
        "/login",
        data={"username": "player1", "password": "playerpass"},
        follow_redirects=False,
    )
    assert user_login.status_code == 302

    denied = auth_client.delete("/api/games/history")
    assert denied.status_code == 403
    assert denied.get_json()["error"] == "Admin access required."


def test_login_rejects_invalid_password(auth_client):
    bad = auth_client.post(
        "/login",
        data={"username": "admin", "password": "wrong-pass"},
        follow_redirects=False,
    )
    assert bad.status_code == 401
    assert b"Invalid username or password." in bad.data


def test_create_user_requires_valid_payload(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    missing_name = auth_client.post("/api/auth/users", json={"password": "longenough"})
    assert missing_name.status_code == 400
    assert missing_name.get_json()["error"] == "Username is required."

    short_password = auth_client.post("/api/auth/users", json={"username": "a", "password": "short"})
    assert short_password.status_code == 400
    assert short_password.get_json()["error"] == "Password must be at least 8 characters."

    created = auth_client.post(
        "/api/auth/users",
        json={"username": "dup", "password": "password1", "is_admin": False},
    )
    assert created.status_code == 201

    duplicate = auth_client.post(
        "/api/auth/users",
        json={"username": "dup", "password": "password2", "is_admin": False},
    )
    assert duplicate.status_code == 400
    assert duplicate.get_json()["error"] == "A user with this username already exists."


def test_player_validation_and_conflicts(client):
    empty = client.post("/api/players", json={"name": ""})
    assert empty.status_code == 400

    a = add_player(client, "Alpha")

    duplicate = client.post("/api/players", json={"name": "alpha"})
    assert duplicate.status_code == 400

    not_found = client.put("/api/players/9999", json={"name": "Renamed"})
    assert not_found.status_code == 404

    blank_rename = client.put(f"/api/players/{a}", json={"name": "   "})
    assert blank_rename.status_code == 400

    b = add_player(client, "Beta")
    conflict = client.put(f"/api/players/{b}", json={"name": "Alpha"})
    assert conflict.status_code == 400


def test_delete_player_not_found_and_active_game_block(client):
    missing = client.delete("/api/players/9999")
    assert missing.status_code == 404

    p1 = add_player(client, "Locked")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]
    assert game["status"] == "active"

    blocked = client.delete(f"/api/players/{p1}")
    assert blocked.status_code == 400
    assert blocked.get_json()["error"] == "Cannot delete a player who is in the active game."


def test_create_game_validation_paths(client):
    p1 = add_player(client, "G1")

    invalid_list = client.post("/api/games", json={"ordered_player_ids": []})
    assert invalid_list.status_code == 400

    duplicate_ids = client.post("/api/games", json={"ordered_player_ids": [p1, p1]})
    assert duplicate_ids.status_code == 400

    missing_player = client.post("/api/games", json={"ordered_player_ids": [9999]})
    assert missing_player.status_code == 400

    started = client.post("/api/games", json={"ordered_player_ids": [p1]})
    assert started.status_code == 201

    second = client.post("/api/games", json={"ordered_player_ids": [p1]})
    assert second.status_code == 400
    assert second.get_json()["error"] == "Finish the active game before starting a new one."


def test_turn_submission_validation_paths(client):
    p1 = add_player(client, "T1")
    p2 = add_player(client, "T2")
    game = client.post("/api/games", json={"ordered_player_ids": [p1, p2]}).get_json()["game"]

    out_of_turn = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p2, "total_points": 20},
    )
    assert out_of_turn.status_code == 400

    non_int_total = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": "20"},
    )
    assert non_int_total.status_code == 400

    out_of_range = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 181},
    )
    assert out_of_range.status_code == 400

    not_found_game = client.post(
        "/api/games/9999/turn",
        json={"player_id": p1, "total_points": 20},
    )
    assert not_found_game.status_code == 404


def test_undo_and_quit_invalid_states(client):
    p1 = add_player(client, "Undoer")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]

    no_turns = client.delete(f"/api/games/{game['id']}/turn")
    assert no_turns.status_code == 400
    assert no_turns.get_json()["error"] == "No turns to undo."

    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})
    quit_res = client.delete(f"/api/games/{game['id']}")
    assert quit_res.status_code == 200

    undo_finished = client.delete(f"/api/games/{game['id']}/turn")
    assert undo_finished.status_code == 400
    assert undo_finished.get_json()["error"] == "Cannot undo a finished game."

    quit_again = client.delete(f"/api/games/{game['id']}")
    assert quit_again.status_code == 400
    assert quit_again.get_json()["error"] == "Only active games can be quit."


def test_login_get_paths_and_auth_me(auth_client):
    login_page = auth_client.get("/login")
    assert login_page.status_code == 200

    unauth_me = auth_client.get("/api/auth/me")
    assert unauth_me.status_code == 401

    ok_login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert ok_login.status_code == 302

    me = auth_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["username"] == "admin"

    relogin_redirect = auth_client.get("/login", follow_redirects=False)
    assert relogin_redirect.status_code == 302

    home = auth_client.get("/")
    assert home.status_code == 200


def test_auth_required_for_admin_endpoints(auth_client):
    create_unauth = auth_client.post("/api/auth/users", json={"username": "x", "password": "password1"})
    assert create_unauth.status_code == 401

    clear_unauth = auth_client.delete("/api/games/history")
    assert clear_unauth.status_code == 401


def test_meta_and_players_list_and_mutations(client):
    meta = client.get("/api/meta")
    assert meta.status_code == 200
    assert meta.get_json()["winning_fives"] == 55

    created = add_player(client, "Gamma")
    listed = client.get("/api/players")
    assert listed.status_code == 200
    assert any(p["id"] == created for p in listed.get_json())

    renamed = client.put(f"/api/players/{created}", json={"name": "Gamma2"})
    assert renamed.status_code == 200
    assert renamed.get_json()["name"] == "Gamma2"

    deleted = client.delete(f"/api/players/{created}")
    assert deleted.status_code == 200
    assert deleted.get_json()["ok"] is True


def test_active_game_and_undo_success_paths(client):
    p1 = add_player(client, "UndoA")
    p2 = add_player(client, "UndoB")
    game = client.post("/api/games", json={"ordered_player_ids": [p1, p2]}).get_json()["game"]

    active = client.get("/api/games/active")
    assert active.status_code == 200
    assert active.get_json()["game"]["id"] == game["id"]

    t1 = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 20})
    assert t1.status_code == 200

    undo = client.delete(f"/api/games/{game['id']}/turn")
    assert undo.status_code == 200
    assert undo.get_json()["game"]["current_turn_position"] == 0


def test_not_found_and_finished_paths(client):
    undo_missing = client.delete("/api/games/9999/turn")
    assert undo_missing.status_code == 404

    quit_missing = client.delete("/api/games/9999")
    assert quit_missing.status_code == 404

    state_missing = client.get("/api/games/9999/state")
    assert state_missing.status_code == 404

    history_missing = client.get("/api/games/9999/history")
    assert history_missing.status_code == 404

    p1 = add_player(client, "FinishOne")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]
    client.delete(f"/api/games/{game['id']}")

    finished_turn = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 20},
    )
    assert finished_turn.status_code == 400


def test_delete_history_when_empty_returns_zero(client):
    empty_delete = client.delete("/api/games/history")
    assert empty_delete.status_code == 200
    assert empty_delete.get_json()["deleted_games"] == 0


def test_ensure_admin_user_existing_branch(client_with_module):
    _, app_module = client_with_module
    with app_module.app.app_context():
        app_module.ensure_admin_user()
        before = app_module.AppUser.query.count()
        app_module.ensure_admin_user()
        after = app_module.AppUser.query.count()
    assert before == after
