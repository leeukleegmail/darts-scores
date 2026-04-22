from datetime import datetime, timedelta, timezone
import importlib
import json
import sys
import tempfile
import time

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
def multi_auth_clients(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="darts-multi-auth-test-") as db_dir:
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

        admin_client = app.test_client()
        player_client = app.test_client()
        yield admin_client, player_client, app_module


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


def login_user(client, username, password="admin"):
    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 302
    return response


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


def test_team_games_preserve_custom_team_names(client):
    alpha = add_player(client, "Alpha Team")
    bravo = add_player(client, "Bravo Team")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [alpha, bravo],
            "team_mode": "teams",
            "team_assignments": {str(alpha): "team_a", str(bravo): "team_b"},
            "team_names": {"team_a": "Dragons", "team_b": "Sharks"},
        },
    )

    assert created.status_code == 201
    game = created.get_json()["game"]
    assert game["team_names"] == {"team_a": "Dragons", "team_b": "Sharks"}


def test_stale_active_game_is_abandoned_after_30_minutes(client_with_module):
    client, app_module = client_with_module
    p1 = add_player(client, "Stale Player")
    first_game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]

    with app_module.app.app_context():
        stored_game = app_module.db.session.get(app_module.Game, first_game["id"])
        stored_game.started_at = datetime.now(timezone.utc) - timedelta(minutes=31)
        app_module.db.session.commit()

    next_game = client.post("/api/games", json={"ordered_player_ids": [p1]})
    assert next_game.status_code == 201

    with app_module.app.app_context():
        stored_game = app_module.db.session.get(app_module.Game, first_game["id"])
        assert stored_game.status == "abandoned"
        assert stored_game.finished_at is not None


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


def test_login_page_is_available_for_get_and_head(auth_client):
    get_response = auth_client.get("/login")
    assert get_response.status_code == 200
    assert b"<form" in get_response.data

    head_response = auth_client.head("/login")
    assert head_response.status_code == 200


def test_logout_quits_active_game(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    player_id = add_player(auth_client, "Log Out Player")
    game = auth_client.post("/api/games", json={"ordered_player_ids": [player_id]}).get_json()["game"]

    logout = auth_client.post("/logout", follow_redirects=False)
    assert logout.status_code == 302

    active = auth_client.get("/api/games/active")
    assert active.status_code == 401

    app_module = sys.modules["app"]
    with app_module.app.app_context():
        stored_game = app_module.db.session.get(app_module.Game, game["id"])
        assert stored_game.status == "abandoned"
        assert stored_game.finished_at is not None


def test_inactivity_timeout_quits_active_game_and_logs_user_out(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    player_id = add_player(auth_client, "Idle Player")
    game = auth_client.post("/api/games", json={"ordered_player_ids": [player_id]}).get_json()["game"]

    with auth_client.session_transaction() as session_data:
        session_data["last_activity_at"] = int(time.time()) - (31 * 60)

    expired = auth_client.get("/api/auth/me")
    assert expired.status_code == 401
    assert expired.get_json()["error"] == "Session expired due to inactivity."

    app_module = sys.modules["app"]
    with app_module.app.app_context():
        stored_game = app_module.db.session.get(app_module.Game, game["id"])
        assert stored_game.status == "abandoned"
        assert stored_game.finished_at is not None


def test_different_users_can_run_active_games_at_the_same_time(multi_auth_clients):
    admin_client, player_client, _app_module = multi_auth_clients

    login_user(admin_client, "admin")
    admin_player_id = add_player(admin_client, "Admin Active Player")

    created_user = admin_client.post(
        "/api/auth/users",
        json={"username": "viewer", "password": "viewerpass", "is_admin": False},
    )
    assert created_user.status_code == 201

    admin_game = admin_client.post("/api/games", json={"ordered_player_ids": [admin_player_id]})
    assert admin_game.status_code == 201
    admin_game_id = admin_game.get_json()["game"]["id"]

    login_user(player_client, "viewer", "viewerpass")
    viewer_players = player_client.get("/api/players")
    assert viewer_players.status_code == 200
    viewer_player_id = next(
        player["id"]
        for player in viewer_players.get_json()
        if player["name"] == "viewer"
    )

    viewer_game = player_client.post("/api/games", json={"ordered_player_ids": [viewer_player_id]})
    assert viewer_game.status_code == 201
    viewer_game_id = viewer_game.get_json()["game"]["id"]

    admin_active = admin_client.get("/api/games/active")
    viewer_active = player_client.get("/api/games/active")
    assert admin_active.status_code == 200
    assert viewer_active.status_code == 200
    assert admin_active.get_json()["game"]["id"] == admin_game_id
    assert viewer_active.get_json()["game"]["id"] == viewer_game_id


def test_players_in_other_users_active_games_are_marked_busy_and_rejected(multi_auth_clients):
    admin_client, player_client, _app_module = multi_auth_clients

    login_user(admin_client, "admin")
    busy_player_id = add_player(admin_client, "Busy Admin Player")
    free_player_id = add_player(admin_client, "Free Shared Player")

    created_user = admin_client.post(
        "/api/auth/users",
        json={"username": "viewer", "password": "viewerpass", "is_admin": False},
    )
    assert created_user.status_code == 201

    started = admin_client.post("/api/games", json={"ordered_player_ids": [busy_player_id]})
    assert started.status_code == 201

    login_user(player_client, "viewer", "viewerpass")
    listed_players = player_client.get("/api/players")
    assert listed_players.status_code == 200

    players_by_name = {player["name"]: player for player in listed_players.get_json()}
    assert players_by_name["Busy Admin Player"]["is_busy"] is True
    assert players_by_name["Free Shared Player"]["is_busy"] is False

    blocked = player_client.post(
        "/api/games",
        json={"ordered_player_ids": [busy_player_id, free_player_id]},
    )
    assert blocked.status_code == 400
    assert blocked.get_json()["error"] == "Busy Admin Player is already in an active game."


def test_logging_out_one_user_does_not_abandon_another_users_active_game(multi_auth_clients):
    admin_client, player_client, app_module = multi_auth_clients

    login_user(admin_client, "admin")
    admin_player_id = add_player(admin_client, "Admin Session Player")
    created_user = admin_client.post(
        "/api/auth/users",
        json={"username": "viewer", "password": "viewerpass", "is_admin": False},
    )
    assert created_user.status_code == 201

    admin_game = admin_client.post("/api/games", json={"ordered_player_ids": [admin_player_id]}).get_json()["game"]

    login_user(player_client, "viewer", "viewerpass")
    viewer_player_id = next(
        player["id"]
        for player in player_client.get("/api/players").get_json()
        if player["name"] == "viewer"
    )
    viewer_game = player_client.post("/api/games", json={"ordered_player_ids": [viewer_player_id]}).get_json()["game"]

    logout = admin_client.post("/logout", follow_redirects=False)
    assert logout.status_code == 302

    viewer_active = player_client.get("/api/games/active")
    assert viewer_active.status_code == 200
    assert viewer_active.get_json()["game"]["id"] == viewer_game["id"]

    with app_module.app.app_context():
        stored_admin_game = app_module.db.session.get(app_module.Game, admin_game["id"])
        stored_viewer_game = app_module.db.session.get(app_module.Game, viewer_game["id"])
        assert stored_admin_game.status == "abandoned"
        assert stored_viewer_game.status == "active"


def test_users_only_see_their_own_games_and_history(multi_auth_clients):
    admin_client, player_client, _app_module = multi_auth_clients

    login_user(admin_client, "admin")
    admin_player_id = add_player(admin_client, "Admin History Player")
    created_user = admin_client.post(
        "/api/auth/users",
        json={"username": "viewer", "password": "viewerpass", "is_admin": False},
    )
    assert created_user.status_code == 201

    admin_game = admin_client.post("/api/games", json={"ordered_player_ids": [admin_player_id]}).get_json()["game"]
    for _ in range(11):
        turn = admin_client.post(
            f"/api/games/{admin_game['id']}/turn",
            json={"player_id": admin_player_id, "total_points": 25},
        )
        assert turn.status_code == 200

    login_user(player_client, "viewer", "viewerpass")
    hidden_state = player_client.get(f"/api/games/{admin_game['id']}/state")
    assert hidden_state.status_code == 404

    viewer_history = player_client.get("/api/games/history")
    assert viewer_history.status_code == 200
    assert viewer_history.get_json() == []


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

    players = auth_client.get("/api/players")
    assert players.status_code == 200
    assert any(player["name"] == "viewer" for player in players.get_json())


def test_deleting_player_does_not_delete_matching_user_account(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    created = auth_client.post(
        "/api/auth/users",
        json={"username": "paired-user", "password": "pairedpass", "is_admin": False},
    )
    assert created.status_code == 201

    players = auth_client.get("/api/players")
    assert players.status_code == 200
    player = next(item for item in players.get_json() if item["name"] == "paired-user")

    deleted = auth_client.delete(f"/api/players/{player['id']}")
    assert deleted.status_code == 200
    assert deleted.get_json()["ok"] is True

    users = auth_client.get("/api/auth/users")
    assert users.status_code == 200
    assert any(item["username"] == "paired-user" for item in users.get_json())


def test_create_user_reuses_existing_player_with_same_name(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    existing_player = auth_client.post("/api/players", json={"name": "Case Match"})
    assert existing_player.status_code == 201

    created = auth_client.post(
        "/api/auth/users",
        json={"username": "case match", "password": "playerpass", "is_admin": False},
    )
    assert created.status_code == 201

    players = auth_client.get("/api/players")
    assert players.status_code == 200
    matching_players = [player for player in players.get_json() if player["name"].lower() == "case match"]
    assert len(matching_players) == 1


def test_admin_can_list_users_and_update_password(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    created = auth_client.post(
        "/api/auth/users",
        json={"username": "manager", "password": "oldpassword", "is_admin": False},
    )
    assert created.status_code == 201
    created_user = created.get_json()

    listed = auth_client.get("/api/auth/users")
    assert listed.status_code == 200
    usernames = [user["username"] for user in listed.get_json()]
    assert "admin" in usernames
    assert "manager" in usernames

    updated = auth_client.put(
        f"/api/auth/users/{created_user['id']}/password",
        json={"password": "newpassword"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["username"] == "manager"

    auth_client.post("/logout", follow_redirects=False)

    old_login = auth_client.post(
        "/login",
        data={"username": "manager", "password": "oldpassword"},
        follow_redirects=False,
    )
    assert old_login.status_code == 401

    new_login = auth_client.post(
        "/login",
        data={"username": "manager", "password": "newpassword"},
        follow_redirects=False,
    )
    assert new_login.status_code == 302


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
    player = created.get_json()

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

    denied_list = auth_client.get("/api/auth/users")
    assert denied_list.status_code == 403
    assert denied_list.get_json()["error"] == "Admin access required."

    denied_update = auth_client.put(
        f"/api/auth/users/{player['id']}/password",
        json={"password": "anotherpass"},
    )
    assert denied_update.status_code == 403
    assert denied_update.get_json()["error"] == "Admin access required."


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


def test_player_stats_endpoint_summarizes_wins_losses_by_game_type(client_with_module):
    client, app_module = client_with_module
    alpha = add_player(client, "Alpha Stats")
    beta = add_player(client, "Beta Stats")

    with app_module.app.app_context():
        solo_win = app_module.Game(
            status="finished",
            game_type="55by5",
            team_mode="solo",
            winner_player_id=alpha,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        solo_loss = app_module.Game(
            status="finished",
            game_type="55by5",
            team_mode="solo",
            winner_player_id=beta,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        team_win = app_module.Game(
            status="finished",
            game_type="english_cricket",
            team_mode="teams",
            winner_team="team_a",
            team_assignments=json.dumps({str(alpha): "team_a", str(beta): "team_b"}),
            team_names=json.dumps({"team_a": "A Team", "team_b": "B Team"}),
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        app_module.db.session.add_all([solo_win, solo_loss, team_win])
        app_module.db.session.flush()

        for game in [solo_win, solo_loss, team_win]:
            app_module.db.session.add_all(
                [
                    app_module.GamePlayerOrder(game_id=game.id, player_id=alpha, position=0),
                    app_module.GamePlayerOrder(game_id=game.id, player_id=beta, position=1),
                ]
            )

        app_module.db.session.commit()

    response = client.get(f"/api/players/{alpha}/stats")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["player"]["name"] == "Alpha Stats"
    assert payload["stats"]["games_played"] == 3
    assert payload["stats"]["games_won"] == 2
    assert payload["stats"]["games_lost"] == 1
    assert [item["game_type"] for item in payload["stats"]["by_game_type"]] == [
        "x01",
        "55by5",
        "english_cricket",
        "noughts_and_crosses",
    ]

    by_type = {item["game_type"]: item for item in payload["stats"]["by_game_type"]}
    assert by_type["55by5"] == {"game_type": "55by5", "label": "55 by 5", "played": 2, "won": 1, "lost": 1}
    assert by_type["english_cricket"] == {
        "game_type": "english_cricket",
        "label": "English Cricket",
        "played": 1,
        "won": 1,
        "lost": 0,
    }
    assert by_type["noughts_and_crosses"] == {
        "game_type": "noughts_and_crosses",
        "label": "Noughts and Crosses",
        "played": 0,
        "won": 0,
        "lost": 0,
    }
    assert by_type["x01"] == {
        "game_type": "x01",
        "label": "X01",
        "played": 0,
        "won": 0,
        "lost": 0,
    }


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


def test_team_mode_undo_recomputes_scores_and_turn_order(client):
    p1 = add_player(client, "UndoTeamA")
    p2 = add_player(client, "UndoTeamB")
    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "55by5",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
        },
    ).get_json()["game"]

    first_turn = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})
    assert first_turn.status_code == 200
    second_turn = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 20})
    assert second_turn.status_code == 200

    undo = client.delete(f"/api/games/{game['id']}/turn")
    assert undo.status_code == 200

    state = undo.get_json()["game"]
    players = {player["id"]: player for player in state["players"]}
    assert players[p1]["fives"] == 5
    assert players[p2]["fives"] == 0
    assert state["active_player_id"] == p2
    assert len(state["turns"]) == 1


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


def test_ensure_admin_user_syncs_password_and_admin_flag(client_with_module, monkeypatch):
    _, app_module = client_with_module
    monkeypatch.setenv("APP_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("APP_ADMIN_PASSWORD", "first-pass")

    with app_module.app.app_context():
        app_module.ensure_admin_user()
        user = app_module.AppUser.query.filter_by(username="admin").first()
        assert user is not None
        assert app_module.check_password_hash(user.password_hash, "first-pass")

        user.is_admin = False
        app_module.db.session.commit()

        monkeypatch.setenv("APP_ADMIN_PASSWORD", "second-pass")
        app_module.ensure_admin_user()

        refreshed = app_module.AppUser.query.filter_by(username="admin").first()
        assert refreshed.is_admin is True
        assert app_module.check_password_hash(refreshed.password_hash, "second-pass")


def test_create_english_cricket_solo_mode(client):
    p1 = add_player(client, "Cricket A")
    p2 = add_player(client, "Cricket B")

    res = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "english_cricket",
            "team_mode": "solo",
        },
    )
    assert res.status_code == 201
    game = res.get_json()["game"]
    assert game["game_type"] == "english_cricket"
    assert game["team_mode"] == "solo"
    assert game["cricket_state"]["inning"] == 1
    assert game["cricket_state"]["batting_team"] == "team_a"
    assert game["cricket_state"]["bowling_team"] == "team_b"
    assert game["active_player_id"] == p2


def test_create_x01_game_with_config(client):
    p1 = add_player(client, "X01 A")
    p2 = add_player(client, "X01 B")

    res = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "x01",
            "team_mode": "solo",
            "x01_starting_score": 301,
        },
    )

    assert res.status_code == 201
    game = res.get_json()["game"]
    assert game["game_type"] == "x01"
    assert game["x01_state"]["starting_score"] == 301
    assert game["players"][0]["x01_remaining"] == 301
    assert game["active_player_id"] == p1


def test_create_noughts_and_crosses_solo_mode(client):
    p1 = add_player(client, "Noughts A")
    p2 = add_player(client, "Noughts B")

    res = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "noughts_and_crosses",
            "team_mode": "solo",
        },
    )
    assert res.status_code == 201
    game = res.get_json()["game"]
    assert game["game_type"] == "noughts_and_crosses"
    assert game["team_mode"] == "solo"
    assert game["active_player_id"] == p1
    assert len(game["noughts_and_crosses_state"]["cells"]) == 9
    assert game["noughts_and_crosses_state"]["cells"][4]["label"] == "Bullseye"
    assert game["noughts_and_crosses_state"]["cells"][0]["mark"] is None


def test_x01_counts_down_immediately(client):
    p1 = add_player(client, "Single Entry Player")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "x01",
            "x01_starting_score": 301,
        },
    ).get_json()["game"]

    first_turn = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 60},
    )
    assert first_turn.status_code == 200
    payload = first_turn.get_json()
    assert payload["turn"]["counted"] is True
    assert payload["turn"]["x01_result"] == "scored"
    assert payload["game"]["players"][0]["x01_remaining"] == 241


def test_create_noughts_and_crosses_team_mode(client):
    p1 = add_player(client, "Noughts Team A1")
    p2 = add_player(client, "Noughts Team B1")
    p3 = add_player(client, "Noughts Team A2")
    p4 = add_player(client, "Noughts Team B2")

    res = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2, p3, p4],
            "game_type": "noughts_and_crosses",
            "team_mode": "teams",
            "team_assignments": {
                str(p1): "team_a",
                str(p2): "team_b",
                str(p3): "team_a",
                str(p4): "team_b",
            },
        },
    )

    assert res.status_code == 201
    game = res.get_json()["game"]
    assert game["game_type"] == "noughts_and_crosses"
    assert game["team_mode"] == "teams"
    assert game["noughts_and_crosses_state"]["x_name"] == "Team A"
    assert game["noughts_and_crosses_state"]["o_name"] == "Team B"


def test_x01_bust_on_leave_one_and_zero_finishes_game(client):
    p1 = add_player(client, "Checkout Player")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "x01",
            "x01_starting_score": 101,
        },
    ).get_json()["game"]

    first = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    assert first.status_code == 200
    assert first.get_json()["game"]["players"][0]["x01_remaining"] == 41

    leave_one = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 40})
    assert leave_one.status_code == 200
    leave_one_payload = leave_one.get_json()
    assert leave_one_payload["turn"]["x01_result"] == "bust_leave_one"
    assert leave_one_payload["game"]["players"][0]["x01_remaining"] == 41

    finished = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 41})
    assert finished.status_code == 200
    finished_payload = finished.get_json()
    assert finished_payload["game"]["status"] == "finished"
    assert finished_payload["game"]["winner_player_id"] == p1
    assert finished_payload["game"]["players"][0]["x01_remaining"] == 0


def test_create_noughts_and_crosses_solo_mode_requires_exactly_two_players(client):
    p1 = add_player(client, "Solo Noughts A")
    p2 = add_player(client, "Solo Noughts B")
    p3 = add_player(client, "Solo Noughts C")

    res = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2, p3],
            "game_type": "noughts_and_crosses",
            "team_mode": "solo",
        },
    )

    assert res.status_code == 400
    assert res.get_json()["error"] == "Noughts and Crosses in solo mode requires exactly two players."


def test_x01_team_mode_uses_shared_team_remaining(client):
    p1 = add_player(client, "Team A Thrower")
    p2 = add_player(client, "Team B Thrower")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "x01",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
            "x01_starting_score": 101,
        },
    ).get_json()["game"]

    first = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    assert first.status_code == 200
    first_payload = first.get_json()
    team_a = next(player for player in first_payload["game"]["players"] if player["id"] == p1)
    team_b = next(player for player in first_payload["game"]["players"] if player["id"] == p2)
    assert team_a["x01_remaining"] == 41
    assert team_b["x01_remaining"] == 101

    second = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 20})
    assert second.status_code == 200

    finisher = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 41},
    )
    assert finisher.status_code == 200
    finisher_payload = finisher.get_json()
    assert finisher_payload["game"]["status"] == "finished"
    assert finisher_payload["game"]["winner_team"] == "team_a"


def test_create_english_cricket_can_choose_starting_batting_team(client):
    p1 = add_player(client, "Cricket C")
    p2 = add_player(client, "Cricket D")

    res = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "english_cricket",
            "team_mode": "solo",
            "starting_batting_team": "team_b",
        },
    )
    assert res.status_code == 201
    game = res.get_json()["game"]
    assert game["cricket_state"]["starting_batting_team"] == "team_b"
    assert game["cricket_state"]["batting_team"] == "team_b"
    assert game["cricket_state"]["bowling_team"] == "team_a"
    assert game["active_player_id"] == p1


def test_english_cricket_runs_and_wickets_finish_game(client):
    p1 = add_player(client, "Bat A")
    p2 = add_player(client, "Bowl B")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "english_cricket",
            "team_mode": "solo",
        },
    ).get_json()["game"]

    # Inning 1: Team B bowls first, Team A bats, then Team B closes the innings.
    opening_bowl = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})
    assert opening_bowl.status_code == 200
    bat = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 50})
    assert bat.status_code == 200
    bowl = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 10})
    assert bowl.status_code == 200

    # Progress inning 2 by always submitting for the active player.
    for _ in range(4):
        state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
        if state["status"] == "finished":
            break
        active_id = state["active_player_id"]
        active = next(p for p in state["players"] if p["id"] == active_id)
        batting_team = state["cricket_state"]["batting_team"]
        total = 150 if active["team"] == batting_team else 0
        turn = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": active_id, "total_points": total},
        )
        assert turn.status_code == 200

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["status"] == "finished"
    assert state["winner_team"] in {"team_a", "team_b", None}


def test_english_cricket_second_innings_chase_finishes_immediately(client):
    p1 = add_player(client, "Chase A")
    p2 = add_player(client, "Chase B")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "english_cricket",
            "team_mode": "solo",
        },
    ).get_json()["game"]

    inning_one_turns = [
        (p2, 0),
        (p1, 50),
        (p2, 10),
        (p1, 0),
    ]
    for player_id, total in inning_one_turns:
        turn = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": player_id, "total_points": total},
        )
        assert turn.status_code == 200

    winning_chase = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p2, "total_points": 51},
    )
    assert winning_chase.status_code == 200

    state = winning_chase.get_json()["game"]
    assert state["status"] == "finished"
    assert state["winner_team"] == "team_b"
    assert state["cricket_state"]["runs"]["team_b"] == 11


def test_noughts_and_crosses_marks_board_and_finishes_on_three_in_a_row(client):
    p1 = add_player(client, "Crosses")
    p2 = add_player(client, "Noughts")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "noughts_and_crosses",
            "team_mode": "solo",
        },
    ).get_json()["game"]

    moves = [
        (p1, 0, "X"),
        (p2, 3, "O"),
        (p1, 1, "X"),
        (p2, 4, "O"),
        (p1, 2, "X"),
    ]

    latest = None
    for player_id, cell_index, marker in moves:
        latest = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": player_id, "total_points": cell_index, "noughts_marker": marker},
        )
        assert latest.status_code == 200

    payload = latest.get_json()
    cells = payload["game"]["noughts_and_crosses_state"]["cells"]
    assert [cells[index]["mark"] for index in (0, 1, 2)] == ["X", "X", "X"]
    assert payload["game"]["status"] == "finished"
    assert payload["game"]["winner_player_id"] == p1
    assert payload["game"]["noughts_and_crosses_state"]["winning_line"] == [0, 1, 2]


def test_noughts_and_crosses_undo_preserves_board_labels(client):
    p1 = add_player(client, "Undo Crosses")
    p2 = add_player(client, "Undo Noughts")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "noughts_and_crosses",
            "team_mode": "solo",
        },
    ).get_json()["game"]

    initial_labels = [cell["label"] for cell in game["noughts_and_crosses_state"]["cells"]]

    first_move = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 0, "noughts_marker": "X"},
    )
    assert first_move.status_code == 200

    undone = client.delete(f"/api/games/{game['id']}/turn")
    assert undone.status_code == 200

    final_labels = [cell["label"] for cell in undone.get_json()["game"]["noughts_and_crosses_state"]["cells"]]
    assert final_labels == initial_labels


def test_55by5_team_mode_winner(client):
    p1 = add_player(client, "TeamA-1")
    p2 = add_player(client, "TeamB-1")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "55by5",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
        },
    ).get_json()["game"]

    # Team A reaches exactly 55 fives first: 11 x 25 points
    for _ in range(11):
        t1 = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})
        assert t1.status_code == 200
        if t1.get_json()["game"]["status"] == "finished":
            break
        t2 = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})
        assert t2.status_code == 200

    finished = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert finished["status"] == "finished"
    assert finished["winner_team"] == "team_a"
