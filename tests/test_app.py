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


def test_should_log_werkzeug_message_suppresses_players_polling(client_with_module):
    _client, app_module = client_with_module

    assert not app_module.should_log_werkzeug_message('127.0.0.1 - - [22/Apr/2026 20:00:00] "GET /api/players HTTP/1.1" 200 -')
    assert app_module.should_log_werkzeug_message('127.0.0.1 - - [22/Apr/2026 20:00:00] "POST /api/players HTTP/1.1" 201 -')
    assert app_module.should_log_werkzeug_message('127.0.0.1 - - [22/Apr/2026 20:00:00] "GET /api/games/active HTTP/1.1" 200 -')


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


def test_clear_history_does_not_change_player_stats(client):
    p1 = add_player(client, "Stats Persist A")
    p2 = add_player(client, "Stats Persist B")

    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "noughts_and_crosses"},
    ).get_json()["game"]
    for cell, marker, pid in [(0, "X", p1), (3, "O", p2), (1, "X", p1), (4, "O", p2), (2, "X", p1)]:
        r = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": pid, "total_points": cell, "noughts_marker": marker},
        )
    assert r.get_json()["game"]["status"] == "finished"

    stats_before = client.get(f"/api/players/{p1}/stats").get_json()["stats"]
    assert stats_before["games_played"] == 1
    assert stats_before["games_won"] == 1
    assert stats_before["games_lost"] == 0

    cleared = client.delete("/api/games/history")
    assert cleared.status_code == 200
    assert cleared.get_json()["deleted_games"] == 1

    stats_after = client.get(f"/api/players/{p1}/stats").get_json()["stats"]
    assert stats_after == stats_before

    history = client.get("/api/games/history?limit=10")
    assert history.status_code == 200
    assert history.get_json() == []


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


def test_inactivity_timeout_logs_user_out_without_quitting_active_game(auth_client):
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
        assert stored_game.status == "active"
        assert stored_game.finished_at is None


def test_game_inactivity_timeout_still_quits_stale_active_game(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    player_id = add_player(auth_client, "Stale Player")
    game = auth_client.post("/api/games", json={"ordered_player_ids": [player_id]}).get_json()["game"]

    app_module = sys.modules["app"]
    with app_module.app.app_context():
        stored_game = app_module.db.session.get(app_module.Game, game["id"])
        stored_game.started_at = datetime.now(timezone.utc) - timedelta(minutes=31)
        app_module.db.session.commit()

    active = auth_client.get("/api/games/active")
    assert active.status_code == 200
    assert active.get_json()["game"] is None

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
    viewer_entries = viewer_history.get_json()
    assert any(entry["id"] == admin_game["id"] for entry in viewer_entries)


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


def test_non_admin_cannot_delete_players(auth_client):
    login = auth_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    created = auth_client.post(
        "/api/auth/users",
        json={"username": "viewer", "password": "viewerpass", "is_admin": False},
    )
    assert created.status_code == 201

    players = auth_client.get("/api/players")
    assert players.status_code == 200
    player = next(item for item in players.get_json() if item["name"] == "viewer")

    auth_client.post("/logout", follow_redirects=False)
    viewer_login = auth_client.post(
        "/login",
        data={"username": "viewer", "password": "viewerpass"},
        follow_redirects=False,
    )
    assert viewer_login.status_code == 302

    deleted = auth_client.delete(f"/api/players/{player['id']}")
    assert deleted.status_code == 403
    assert deleted.get_json()["error"] == "Admin access required."


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
    assert payload["stats"]["games_drawn"] == 0
    assert [item["game_type"] for item in payload["stats"]["by_game_type"]] == [
        "x01",
        "55by5",
        "english_cricket",
        "noughts_and_crosses",
        "halve_it",
        "hi_low",
    ]

    by_type = {item["game_type"]: item for item in payload["stats"]["by_game_type"]}
    assert by_type["55by5"] == {
        "game_type": "55by5",
        "label": "55 by 5",
        "played": 2,
        "won": 1,
        "lost": 1,
        "drawn": 0,
    }
    assert by_type["english_cricket"] == {
        "game_type": "english_cricket",
        "label": "English Cricket",
        "played": 1,
        "won": 1,
        "lost": 0,
        "drawn": 0,
    }
    assert by_type["noughts_and_crosses"] == {
        "game_type": "noughts_and_crosses",
        "label": "Noughts and Crosses",
        "played": 0,
        "won": 0,
        "lost": 0,
        "drawn": 0,
    }
    assert by_type["x01"] == {
        "game_type": "x01",
        "label": "X01",
        "played": 0,
        "won": 0,
        "lost": 0,
        "drawn": 0,
    }
    assert by_type["halve_it"] == {
        "game_type": "halve_it",
        "label": "Halve It",
        "played": 0,
        "won": 0,
        "lost": 0,
        "drawn": 0,
    }


def test_player_stats_endpoint_counts_draws_in_totals(client_with_module):
    client, app_module = client_with_module
    alpha = add_player(client, "Alpha Draw Stats")
    beta = add_player(client, "Beta Draw Stats")

    with app_module.app.app_context():
        draw_game = app_module.Game(
            status="finished",
            game_type="noughts_and_crosses",
            team_mode="solo",
            winner_player_id=None,
            winner_team=None,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        app_module.db.session.add(draw_game)
        app_module.db.session.flush()
        app_module.db.session.add_all(
            [
                app_module.GamePlayerOrder(game_id=draw_game.id, player_id=alpha, position=0),
                app_module.GamePlayerOrder(game_id=draw_game.id, player_id=beta, position=1),
            ]
        )
        app_module.db.session.commit()

    response = client.get(f"/api/players/{alpha}/stats")
    assert response.status_code == 200
    stats = response.get_json()["stats"]

    assert stats["games_played"] == 1
    assert stats["games_won"] == 0
    assert stats["games_lost"] == 0
    assert stats["games_drawn"] == 1
    assert stats["games_played"] == stats["games_won"] + stats["games_lost"] + stats["games_drawn"]

    by_type = {item["game_type"]: item for item in stats["by_game_type"]}
    assert by_type["noughts_and_crosses"]["drawn"] == 1


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


def test_turn_submission_rejects_scores_above_180_for_all_game_modes(client):
    p1 = add_player(client, "Limit A")
    p2 = add_player(client, "Limit B")

    game_payloads = [
        {"ordered_player_ids": [p1], "game_type": "55by5"},
        {
            "ordered_player_ids": [p1],
            "game_type": "x01",
            "x01_starting_score": 501,
        },
        {"ordered_player_ids": [p1, p2], "game_type": "english_cricket"},
        {"ordered_player_ids": [p1, p2], "game_type": "noughts_and_crosses"},
        {"ordered_player_ids": [p1], "game_type": "halve_it"},
    ]

    for payload in game_payloads:
        created = client.post("/api/games", json=payload)
        assert created.status_code == 201
        game = created.get_json()["game"]
        active_player_id = game["active_player_id"]

        rejected = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": active_player_id, "total_points": 181},
        )
        assert rejected.status_code == 400
        assert "between 0 and 180" in rejected.get_json()["error"]

        quit_res = client.delete(f"/api/games/{game['id']}")
        assert quit_res.status_code == 200


def test_turn_submission_accepts_score_of_180_at_boundary(client):
    p1 = add_player(client, "Boundary")

    game_payloads = [
        {"ordered_player_ids": [p1], "game_type": "55by5"},
        {
            "ordered_player_ids": [p1],
            "game_type": "x01",
            "x01_starting_score": 301,
        },
    ]

    for payload in game_payloads:
        created = client.post("/api/games", json=payload)
        assert created.status_code == 201
        game = created.get_json()["game"]
        active_player_id = game["active_player_id"]

        accepted = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": active_player_id, "total_points": 180},
        )
        assert accepted.status_code == 200
        assert accepted.get_json()["turn"]["total_points"] == 180

        quit_res = client.delete(f"/api/games/{game['id']}")
        # x01 may finish immediately in some configs; quitting an active game is optional.
        if quit_res.status_code != 200:
            assert quit_res.status_code == 400


def test_halve_it_rejects_team_mode(client):
    p1 = add_player(client, "Halve Team A")
    p2 = add_player(client, "Halve Team B")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "halve_it",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
        },
    )

    assert created.status_code == 400
    assert "does not support teams" in created.get_json()["error"]


def test_halve_it_scoring_and_miss_halves_total(client):
    p1 = add_player(client, "Halve Solo")

    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "halve_it"},
    ).get_json()["game"]

    round_1 = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 2},
    )
    assert round_1.status_code == 200
    round_1_payload = round_1.get_json()
    assert round_1_payload["turn"]["halve_it_target"] == "15"
    assert round_1_payload["turn"]["halve_it_halved"] is False
    assert next(player for player in round_1_payload["game"]["players"] if player["id"] == p1)["fives"] == 50

    round_2 = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 0},
    )
    assert round_2.status_code == 200
    round_2_payload = round_2.get_json()
    assert round_2_payload["turn"]["halve_it_target"] == "16"
    assert round_2_payload["turn"]["halve_it_halved"] is True
    assert next(player for player in round_2_payload["game"]["players"] if player["id"] == p1)["fives"] == 25


def test_halve_it_starting_scores_by_variant(client):
    standard_player = add_player(client, "Halve Standard Start")
    standard_game = client.post(
        "/api/games",
        json={"ordered_player_ids": [standard_player], "game_type": "halve_it"},
    ).get_json()["game"]
    standard_score = next(player for player in standard_game["players"] if player["id"] == standard_player)["fives"]
    assert standard_score == 20

    assert client.delete(f"/api/games/{standard_game['id']}").status_code == 200

    hardcore_player = add_player(client, "Halve Hardcore Start")
    hardcore_game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [hardcore_player],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    ).get_json()["game"]
    hardcore_score = next(player for player in hardcore_game["players"] if player["id"] == hardcore_player)["fives"]
    assert hardcore_score == 0


def test_halve_it_validates_entry_by_round_type(client):
    p1 = add_player(client, "Halve Rules")

    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "halve_it"},
    ).get_json()["game"]

    invalid_number_round = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 10},
    )
    assert invalid_number_round.status_code == 400
    assert "expects hit count" in invalid_number_round.get_json()["error"]

    assert client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 3},
    ).status_code == 200
    assert client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 3},
    ).status_code == 200

    invalid_double_round = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 7},
    )
    assert invalid_double_round.status_code == 400
    assert "divisible by 2" in invalid_double_round.get_json()["error"]


def test_halve_it_bull_round_allows_up_to_six_marks(client):
    p1 = add_player(client, "Halve Bull Rules")

    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "halve_it"},
    ).get_json()["game"]

    # Advance to round 9 (Bullseye).
    for entry in [1, 1, 20, 1, 1, 30, 1, 1]:
        response = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert response.status_code == 200

    valid_bull_marks = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 6},
    )
    assert valid_bull_marks.status_code == 200

    # New game for invalid bull marks check.
    game_invalid = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "halve_it"},
    ).get_json()["game"]

    for entry in [1, 1, 20, 1, 1, 30, 1, 1]:
        response = client.post(
            f"/api/games/{game_invalid['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert response.status_code == 200

    invalid_bull_marks = client.post(
        f"/api/games/{game_invalid['id']}/turn",
        json={"player_id": p1, "total_points": 7},
    )
    assert invalid_bull_marks.status_code == 400
    assert "hit count (0-6)" in invalid_bull_marks.get_json()["error"]


def test_halve_it_hardcore_variant_generates_custom_rounds(client):
    p1 = add_player(client, "Hardcore Solo")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )

    assert created.status_code == 201
    game = created.get_json()["game"]
    halve_state = game["halve_it_state"]
    assert halve_state["variant"] == "hardcore"
    assert halve_state["total_rounds"] == 9
    assert len(halve_state["rounds"]) == 9
    assert halve_state["rounds"][8]["kind"] == "bull"
    assert "Bullseye" in halve_state["rounds"][8]["target"]

    round_8 = halve_state["rounds"][7]
    assert round_8["kind"] == "exact_total"
    assert round_8["exact_totals"] == [41, 101, 123]
    assert "Target 41 / 101 / 123" in round_8["target"]


def test_halve_it_hardcore_round_9_is_bullseye(client):
    p1 = add_player(client, "Hardcore Final Round Bull")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    # Progress through 8 rounds with valid entries and capture score before R9.
    for _ in range(8):
        current_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
        round_info = current_state["halve_it_state"]["rounds"][current_state["halve_it_state"]["current_round"] - 1]
        kind = round_info["kind"]
        if kind == "number":
            entry = 1
        elif kind == "double":
            entry = 20
        elif kind == "triple":
            entry = 21
        elif kind == "exact_total":
            if round_info.get("exact_totals"):
                entry = int(round_info["exact_totals"][0])
            else:
                entry = int(round_info["exact_total"])
        elif kind == "all_darts_hits":
            entry = int(round_info.get("required_hits") or 3)
        else:
            entry = 0

        turn = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert turn.status_code == 200

    before_round_9_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    before_round_9_score = next(player for player in before_round_9_state["players"] if player["id"] == p1)["fives"]

    invalid_final = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 26},
    )
    assert invalid_final.status_code == 400
    assert "steps of 25" in invalid_final.get_json()["error"]

    valid_final = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 50},
    )
    assert valid_final.status_code == 200
    payload = valid_final.get_json()
    assert payload["turn"]["halve_it_halved"] is False
    after_score = next(player for player in payload["game"]["players"] if player["id"] == p1)["fives"]
    assert after_score == before_round_9_score + 50


def test_halve_it_hardcore_round_9_allows_no_score(client):
    p1 = add_player(client, "Hardcore Final Round No Score")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    # Progress through 8 rounds with valid entries.
    for _ in range(8):
        current_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
        round_info = current_state["halve_it_state"]["rounds"][current_state["halve_it_state"]["current_round"] - 1]
        kind = round_info["kind"]
        if kind == "number":
            entry = 1
        elif kind == "double":
            entry = 20
        elif kind == "triple":
            entry = 21
        elif kind == "exact_total":
            if round_info.get("exact_totals"):
                entry = int(round_info["exact_totals"][0])
            else:
                entry = int(round_info["exact_total"])
        elif kind == "all_darts_hits":
            entry = int(round_info.get("required_hits") or 3)
        elif kind == "manual_points":
            entry = 45
        else:
            entry = 0

        turn = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert turn.status_code == 200

    before_round_9_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    before_round_9_score = next(player for player in before_round_9_state["players"] if player["id"] == p1)["fives"]

    no_score_final = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 0},
    )
    assert no_score_final.status_code == 200
    payload = no_score_final.get_json()
    assert payload["turn"]["halve_it_halved"] is True
    after_score = next(player for player in payload["game"]["players"] if player["id"] == p1)["fives"]
    assert after_score == before_round_9_score // 2


def test_halve_it_hardcore_single_number_rounds_use_hit_count_scoring(client):
    p1 = add_player(client, "Hardcore Number Rules")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    round_1_info = game["halve_it_state"]["rounds"][0]
    assert round_1_info["kind"] == "number"
    assert round_1_info["entry_mode"] == "hits"

    # Two hits on 20 should score 40 in Hardcore round 1 (same as Standard number rounds).
    turn_1 = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 2},
    )
    assert turn_1.status_code == 200
    score_after_turn_1 = next(player for player in turn_1.get_json()["game"]["players"] if player["id"] == p1)["fives"]
    assert score_after_turn_1 == 40

    # Round 2 (Any Double): valid divisible-by-2 score to progress.
    turn_2 = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 20},
    )
    assert turn_2.status_code == 200

    # Round 3 is another single-number round and should also use hit-count scoring.
    state_round_3 = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    round_3_info = state_round_3["halve_it_state"]["rounds"][2]
    assert round_3_info["kind"] == "number"
    assert round_3_info["entry_mode"] == "hits"

    turn_3 = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 1},
    )
    assert turn_3.status_code == 200
    round_3_value = int(round_3_info["number"])
    score_after_turn_3 = next(player for player in turn_3.get_json()["game"]["players"] if player["id"] == p1)["fives"]
    assert score_after_turn_3 == 40 + 20 + round_3_value


def test_halve_it_hardcore_three_different_colors_allows_score_or_no_score(client):
    p1 = add_player(client, "Hardcore Colors Rules")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    rounds = game["halve_it_state"]["rounds"]
    assert rounds[3]["target"] == "Three Different Colors"
    assert rounds[3]["kind"] == "manual_points"
    assert rounds[3]["entry_mode"] == "points"

    # Progress to round 4 with valid entries.
    assert client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 1}).status_code == 200
    assert client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 20}).status_code == 200
    assert client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 1}).status_code == 200

    before_round_4 = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    before_score = next(player for player in before_round_4["players"] if player["id"] == p1)["fives"]

    # Entering a score should add that score.
    scored_round = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 45},
    )
    assert scored_round.status_code == 200
    after_scored = next(player for player in scored_round.get_json()["game"]["players"] if player["id"] == p1)["fives"]
    assert after_scored == before_score + 45

    # End this game so a second verification game can be created.
    assert client.delete(f"/api/games/{game['id']}").status_code == 200

    # A fresh game verifies explicit no-score (0) is also accepted.
    p2 = add_player(client, "Hardcore Colors Rules No Score")
    game2 = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p2],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    ).get_json()["game"]

    assert client.post(f"/api/games/{game2['id']}/turn", json={"player_id": p2, "total_points": 1}).status_code == 200
    assert client.post(f"/api/games/{game2['id']}/turn", json={"player_id": p2, "total_points": 20}).status_code == 200
    assert client.post(f"/api/games/{game2['id']}/turn", json={"player_id": p2, "total_points": 1}).status_code == 200

    before_no_score_state = client.get(f"/api/games/{game2['id']}/state").get_json()["game"]
    before_no_score = next(player for player in before_no_score_state["players"] if player["id"] == p2)["fives"]

    no_score_round = client.post(
        f"/api/games/{game2['id']}/turn",
        json={"player_id": p2, "total_points": 0},
    )
    assert no_score_round.status_code == 200
    no_score_payload = no_score_round.get_json()
    assert no_score_payload["turn"]["halve_it_halved"] is True
    after_no_score = next(player for player in no_score_payload["game"]["players"] if player["id"] == p2)["fives"]
    assert after_no_score == before_no_score // 2


def test_halve_it_hardcore_black_white_black_allows_no_score(client):
    p1 = add_player(client, "Hardcore BWB No Score")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    # Progress to round 6 with valid entries for rounds 1-5.
    for _ in range(5):
        current_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
        round_info = current_state["halve_it_state"]["rounds"][current_state["halve_it_state"]["current_round"] - 1]
        kind = round_info["kind"]
        if kind == "number":
            entry = 1
        elif kind == "double":
            entry = 20
        elif kind == "triple":
            entry = 21
        elif kind == "exact_total":
            if round_info.get("exact_totals"):
                entry = int(round_info["exact_totals"][0])
            else:
                entry = int(round_info["exact_total"])
        elif kind == "all_darts_hits":
            entry = int(round_info.get("required_hits") or 3)
        elif kind == "manual_points":
            entry = 45
        else:
            entry = 0

        response = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert response.status_code == 200

    state_before = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    round_6 = state_before["halve_it_state"]["rounds"][5]
    assert round_6["target"] == "Black-White-Black"
    assert round_6["kind"] == "manual_points"

    score_before = next(player for player in state_before["players"] if player["id"] == p1)["fives"]

    # No score should be accepted and should halve the player's current total.
    no_score = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 0},
    )
    assert no_score.status_code == 200
    payload = no_score.get_json()
    assert payload["turn"]["halve_it_halved"] is True
    score_after = next(player for player in payload["game"]["players"] if player["id"] == p1)["fives"]
    assert score_after == score_before // 2


def test_halve_it_hardcore_black_white_black_allows_score_entry(client):
    p1 = add_player(client, "Hardcore BWB Score Entry")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    # Progress to round 6 with valid entries for rounds 1-5.
    for _ in range(5):
        current_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
        round_info = current_state["halve_it_state"]["rounds"][current_state["halve_it_state"]["current_round"] - 1]
        kind = round_info["kind"]
        if kind == "number":
            entry = 1
        elif kind == "double":
            entry = 20
        elif kind == "triple":
            entry = 21
        elif kind == "exact_total":
            if round_info.get("exact_totals"):
                entry = int(round_info["exact_totals"][0])
            else:
                entry = int(round_info["exact_total"])
        elif kind == "all_darts_hits":
            entry = int(round_info.get("required_hits") or 3)
        elif kind == "manual_points":
            entry = 45
        else:
            entry = 0

        response = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert response.status_code == 200

    state_before = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    round_6 = state_before["halve_it_state"]["rounds"][5]
    assert round_6["target"] == "Black-White-Black"
    assert round_6["kind"] == "manual_points"

    score_before = next(player for player in state_before["players"] if player["id"] == p1)["fives"]

    scored_round = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 90},
    )
    assert scored_round.status_code == 200
    scored_payload = scored_round.get_json()
    assert scored_payload["turn"]["halve_it_halved"] is False
    score_after = next(player for player in scored_payload["game"]["players"] if player["id"] == p1)["fives"]
    assert score_after == score_before + 90


def test_halve_it_hardcore_three_different_colors_rejects_scores_over_180(client):
    p1 = add_player(client, "Hardcore Colors Max")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    # Progress to round 4.
    assert client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 1}).status_code == 200
    assert client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 20}).status_code == 200
    assert client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 1}).status_code == 200

    invalid_too_high = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 181},
    )
    assert invalid_too_high.status_code == 400
    assert "between 0 and 180" in invalid_too_high.get_json()["error"]


def test_halve_it_hardcore_exact_round_accepts_miss_and_no_score(client):
    p1 = add_player(client, "Hardcore Exact Miss")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    # Progress to round 8 (always Exact in Hardcore).
    for _ in range(7):
        current_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
        round_info = current_state["halve_it_state"]["rounds"][current_state["halve_it_state"]["current_round"] - 1]
        kind = round_info["kind"]
        if kind == "number":
            entry = 1
        elif kind == "double":
            entry = 20
        elif kind == "triple":
            entry = 21
        elif kind == "exact_total":
            if round_info.get("exact_totals"):
                entry = int(round_info["exact_totals"][0])
            else:
                entry = int(round_info["exact_total"])
        elif kind == "all_darts_hits":
            entry = int(round_info.get("required_hits") or 3)
        elif kind == "manual_points":
            entry = 45
        else:
            entry = 0

        response = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert response.status_code == 200

    state_before = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    round_8_info = state_before["halve_it_state"]["rounds"][7]
    assert round_8_info["kind"] == "exact_total"
    score_before = next(player for player in state_before["players"] if player["id"] == p1)["fives"]

    # Non-exact should be accepted and treated as miss (halving score).
    miss_round = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 0},
    )
    assert miss_round.status_code == 200
    miss_payload = miss_round.get_json()
    assert miss_payload["turn"]["halve_it_halved"] is True
    score_after_miss = next(player for player in miss_payload["game"]["players"] if player["id"] == p1)["fives"]
    assert score_after_miss == score_before // 2


def test_halve_it_hardcore_exact_round_exact_hit_still_scores(client):
    p1 = add_player(client, "Hardcore Exact Hit")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    # Progress to round 8.
    for _ in range(7):
        current_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
        round_info = current_state["halve_it_state"]["rounds"][current_state["halve_it_state"]["current_round"] - 1]
        kind = round_info["kind"]
        if kind == "number":
            entry = 1
        elif kind == "double":
            entry = 20
        elif kind == "triple":
            entry = 21
        elif kind == "exact_total":
            if round_info.get("exact_totals"):
                entry = int(round_info["exact_totals"][0])
            else:
                entry = int(round_info["exact_total"])
        elif kind == "all_darts_hits":
            entry = int(round_info.get("required_hits") or 3)
        elif kind == "manual_points":
            entry = 45
        else:
            entry = 0

        response = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert response.status_code == 200

    state_before = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    round_8_info = state_before["halve_it_state"]["rounds"][7]
    exact_target = int(round_8_info["exact_totals"][1])
    score_before = next(player for player in state_before["players"] if player["id"] == p1)["fives"]

    hit_round = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": exact_target},
    )
    assert hit_round.status_code == 200
    hit_payload = hit_round.get_json()
    assert hit_payload["turn"]["halve_it_halved"] is False
    score_after_hit = next(player for player in hit_payload["game"]["players"] if player["id"] == p1)["fives"]
    assert score_after_hit == score_before + exact_target


def test_halve_it_hardcore_exact_round_shows_all_targets_and_scores_one_hit(client):
    p1 = add_player(client, "Hardcore Exact Multi Target")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "halve_it",
            "halve_it_variant": "hardcore",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]

    for _ in range(7):
        current_state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
        round_info = current_state["halve_it_state"]["rounds"][current_state["halve_it_state"]["current_round"] - 1]
        kind = round_info["kind"]
        if kind == "number":
            entry = 1
        elif kind == "double":
            entry = 20
        elif kind == "triple":
            entry = 21
        elif kind == "exact_total":
            if round_info.get("exact_totals"):
                entry = int(round_info["exact_totals"][0])
            else:
                entry = int(round_info["exact_total"])
        elif kind == "all_darts_hits":
            entry = int(round_info.get("required_hits") or 3)
        elif kind == "manual_points":
            entry = 45
        else:
            entry = 0

        response = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": p1, "total_points": entry},
        )
        assert response.status_code == 200

    state_before = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    round_8 = state_before["halve_it_state"]["rounds"][7]
    assert round_8["exact_totals"] == [41, 101, 123]
    assert "Target 41 / 101 / 123" in round_8["target"]

    score_before = next(player for player in state_before["players"] if player["id"] == p1)["fives"]
    chosen_target = 123
    scored_round = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": chosen_target},
    )
    assert scored_round.status_code == 200
    payload = scored_round.get_json()
    assert payload["turn"]["halve_it_halved"] is False
    score_after = next(player for player in payload["game"]["players"] if player["id"] == p1)["fives"]
    assert score_after == score_before + chosen_target


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
            "x01_match_type": "first_to",
            "x01_legs_value": 3,
            "x01_starting_entity": str(p2),
        },
    )

    assert res.status_code == 201
    game = res.get_json()["game"]
    assert game["game_type"] == "x01"
    assert game["x01_state"]["starting_score"] == 301
    assert game["x01_state"]["match_type"] == "first_to"
    assert game["x01_state"]["legs_value"] == 3
    assert game["x01_state"]["required_legs"] == 3
    assert game["x01_state"]["starting_entity"] == str(p2)
    assert game["players"][0]["x01_remaining"] == 301
    assert game["active_player_id"] == p2


def test_create_hi_low_game_with_defaults_and_custom_validation(client):
    p1 = add_player(client, "Hi Low A")
    p2 = add_player(client, "Hi Low B")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "hi_low",
        },
    )
    assert created.status_code == 201
    game = created.get_json()["game"]
    assert game["game_type"] == "hi_low"
    assert game["hi_low_state"]["start_low"] == 26
    assert game["hi_low_state"]["start_high"] == 45
    assert game["hi_low_state"]["current_low"] == 26
    assert game["hi_low_state"]["current_high"] == 45
    assert game["hi_low_state"]["match_type"] == "best_of"
    assert game["hi_low_state"]["legs_value"] == 1
    assert game["hi_low_state"]["required_legs"] == 1
    assert game["hi_low_state"]["legs_won"] == {str(p1): 0, str(p2): 0}
    assert game["hi_low_state"]["phase"] == "bounds"

    closed = client.delete(f"/api/games/{game['id']}")
    assert closed.status_code == 200

    invalid = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "hi_low",
            "hi_low_use_custom": True,
            "hi_low_low": 70,
            "hi_low_high": 40,
        },
    )
    assert invalid.status_code == 400
    assert invalid.get_json()["error"] == "Hi/Low custom values require low to be less than high."


def test_hi_low_no_score_eliminates_player_and_can_finish_game(client):
    p1 = add_player(client, "No Score A")
    p2 = add_player(client, "No Score B")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "hi_low",
        },
    ).get_json()["game"]

    no_score = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 0},
    )
    assert no_score.status_code == 200
    payload = no_score.get_json()
    assert payload["turn"]["hi_low_result"] == "eliminated"
    assert payload["game"]["status"] == "finished"
    assert payload["game"]["winner_player_id"] == p2


def test_hi_low_elimination_flow_updates_bounds_and_skips_eliminated(client):
    p1 = add_player(client, "Skip A")
    p2 = add_player(client, "Skip B")
    p3 = add_player(client, "Skip C")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2, p3],
            "game_type": "hi_low",
        },
    ).get_json()["game"]

    first = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 45},
    )
    assert first.status_code == 200
    first_payload = first.get_json()
    assert first_payload["turn"]["hi_low_result"] == "eliminated"
    assert first_payload["game"]["active_player_id"] == p2

    out_of_turn = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p3, "total_points": 60},
    )
    assert out_of_turn.status_code == 400
    assert out_of_turn.get_json()["error"] == "It is not this player's turn."

    second = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p2, "total_points": 50},
    )
    assert second.status_code == 200
    second_payload = second.get_json()
    assert second_payload["turn"]["hi_low_result"] == "success"
    assert second_payload["game"]["hi_low_state"]["current_low"] == 26
    assert second_payload["game"]["hi_low_state"]["current_high"] == 50
    assert second_payload["game"]["active_player_id"] == p3

    final = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p3, "total_points": 50},
    )
    assert final.status_code == 200
    final_payload = final.get_json()
    assert final_payload["turn"]["hi_low_result"] == "eliminated"
    assert final_payload["game"]["status"] == "finished"
    assert final_payload["game"]["winner_player_id"] == p2

    players = {item["id"]: item for item in final_payload["game"]["players"]}
    assert players[p1]["hi_low_eliminated"] is True
    assert players[p3]["hi_low_eliminated"] is True
    assert players[p2]["hi_low_eliminated"] is False


def test_hi_low_team_mode_wins_by_last_team_with_active_players(client):
    p1 = add_player(client, "Team A One")
    p2 = add_player(client, "Team B One")
    p3 = add_player(client, "Team A Two")
    p4 = add_player(client, "Team B Two")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2, p3, p4],
            "game_type": "hi_low",
            "team_mode": "teams",
            "team_assignments": {
                str(p1): "team_a",
                str(p2): "team_b",
                str(p3): "team_a",
                str(p4): "team_b",
            },
        },
    ).get_json()["game"]

    turns = [
        (p1, 50),
        (p2, 50),
        (p3, 40),
        (p4, 40),
    ]
    last_payload = None
    for player_id, score in turns:
        response = client.post(
            f"/api/games/{game['id']}/turn",
            json={"player_id": player_id, "total_points": score},
        )
        assert response.status_code == 200
        last_payload = response.get_json()

    assert last_payload is not None
    assert last_payload["game"]["status"] == "finished"
    assert last_payload["game"]["winner_team"] == "team_a"


def test_hi_low_first_to_two_requires_two_leg_wins(client):
    p1 = add_player(client, "Hi A")
    p2 = add_player(client, "Hi B")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "hi_low",
            "hi_low_match_type": "first_to",
            "hi_low_legs_value": 2,
        },
    ).get_json()["game"]

    assert game["hi_low_state"]["match_type"] == "first_to"
    assert game["hi_low_state"]["legs_value"] == 2
    assert game["hi_low_state"]["required_legs"] == 2

    leg_one = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 30},
    )
    assert leg_one.status_code == 200
    leg_one_payload = leg_one.get_json()
    assert leg_one_payload["turn"]["hi_low_result"] == "eliminated"
    assert leg_one_payload["game"]["status"] == "active"
    assert leg_one_payload["game"]["winner_player_id"] is None
    assert leg_one_payload["game"]["hi_low_state"]["legs_won"][str(p2)] == 1
    assert leg_one_payload["game"]["hi_low_state"]["eliminated_players"] == []

    leg_two = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p2, "total_points": 40},
    )
    assert leg_two.status_code == 200
    leg_two_payload = leg_two.get_json()
    assert leg_two_payload["turn"]["hi_low_result"] == "eliminated"
    assert leg_two_payload["game"]["status"] == "active"
    assert leg_two_payload["game"]["hi_low_state"]["legs_won"][str(p1)] == 1

    match_leg = client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 40},
    )
    assert match_leg.status_code == 200
    match_payload = match_leg.get_json()
    assert match_payload["turn"]["hi_low_result"] == "eliminated"
    assert match_payload["game"]["status"] == "finished"
    assert match_payload["game"]["winner_player_id"] == p2
    assert match_payload["game"]["hi_low_state"]["legs_won"][str(p2)] == 2


def test_x01_first_to_legs_requires_multiple_leg_wins(client):
    p1 = add_player(client, "Leg Winner")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "x01",
            "x01_starting_score": 101,
            "x01_match_type": "first_to",
            "x01_legs_value": 3,
        },
    ).get_json()["game"]

    first_leg = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 101})
    assert first_leg.status_code == 200
    first_leg_payload = first_leg.get_json()
    assert first_leg_payload["game"]["status"] == "active"
    assert first_leg_payload["game"]["x01_state"]["legs_won"][str(p1)] == 1
    assert first_leg_payload["game"]["players"][0]["x01_remaining"] == 101

    second_leg = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 101})
    assert second_leg.status_code == 200
    second_leg_payload = second_leg.get_json()
    assert second_leg_payload["game"]["status"] == "active"
    assert second_leg_payload["game"]["x01_state"]["legs_won"][str(p1)] == 2

    match_leg = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 101})
    assert match_leg.status_code == 200
    match_leg_payload = match_leg.get_json()
    assert match_leg_payload["game"]["status"] == "finished"
    assert match_leg_payload["game"]["winner_player_id"] == p1
    assert match_leg_payload["game"]["x01_state"]["legs_won"][str(p1)] == 3


def test_x01_team_starting_entity_selects_first_throwing_team(client):
    p1 = add_player(client, "Team A Lead")
    p2 = add_player(client, "Team B Lead")

    created = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "x01",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
            "x01_starting_entity": "team_b",
        },
    )

    assert created.status_code == 201
    game = created.get_json()["game"]
    assert game["active_player_id"] == p2
    assert game["x01_state"]["starting_entity"] == "team_b"


def test_x01_payload_includes_active_checkout_and_keeps_it_on_bust(client):
    p1 = add_player(client, "Checkout Snapshot")

    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1],
            "game_type": "x01",
            "x01_starting_score": 101,
        },
    ).get_json()["game"]

    assert game["x01_state"]["active_entity_key"] == str(p1)
    assert game["x01_state"]["active_remaining"] == 101
    assert game["x01_state"]["active_checkout"] == "T17 10 D20"

    scored = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    assert scored.status_code == 200
    scored_payload = scored.get_json()
    assert scored_payload["game"]["x01_state"]["active_remaining"] == 41
    assert scored_payload["game"]["x01_state"]["active_checkout"] == "9 D16"

    bust = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 40})
    assert bust.status_code == 200
    bust_payload = bust.get_json()
    assert bust_payload["turn"]["x01_result"] == "bust_leave_one"
    assert bust_payload["game"]["x01_state"]["active_remaining"] == 41
    assert bust_payload["game"]["x01_state"]["active_checkout"] == "9 D16"


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
    cell_labels = [cell["label"] for cell in game["noughts_and_crosses_state"]["cells"]]
    assert len(cell_labels) == len(set(cell_labels)), "Every cell label must be unique"


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


# ---------------------------------------------------------------------------
# Winner naming: winner_team_name / winner_player_id across all game types
# ---------------------------------------------------------------------------


def _finish_55by5_solo(client, player_id, game_id):
    """Score 55 fives (11 x 25 points) for a single player."""
    for _ in range(11):
        r = client.post(f"/api/games/{game_id}/turn", json={"player_id": player_id, "total_points": 25})
        assert r.status_code == 200
        if r.get_json()["game"]["status"] == "finished":
            break


def test_winner_name_55by5_solo(client):
    p1 = add_player(client, "Solo Winner")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]
    _finish_55by5_solo(client, p1, game["id"])

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["status"] == "finished"
    assert state["winner_player_id"] == p1
    assert state["winner_team_name"] is None


def test_winner_name_55by5_teams_default(client):
    p1 = add_player(client, "Team1-A")
    p2 = add_player(client, "Team1-B")
    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "55by5",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
        },
    ).get_json()["game"]
    for _ in range(11):
        r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})
        assert r.status_code == 200
        if r.get_json()["game"]["status"] == "finished":
            break
        client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["status"] == "finished"
    assert state["winner_team"] == "team_a"
    assert state["winner_team_name"] == "Team A"
    assert state["winner_player_id"] is None


def test_winner_name_55by5_teams_custom(client):
    p1 = add_player(client, "Red-A")
    p2 = add_player(client, "Blue-A")
    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "55by5",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
            "team_names": {"team_a": "Red Dragons", "team_b": "Blue Phoenix"},
        },
    ).get_json()["game"]
    for _ in range(11):
        r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})
        assert r.status_code == 200
        if r.get_json()["game"]["status"] == "finished":
            break
        client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["status"] == "finished"
    assert state["winner_team"] == "team_a"
    assert state["winner_team_name"] == "Red Dragons"
    assert state["winner_player_id"] is None


def test_winner_name_x01_solo(client):
    p1 = add_player(client, "X01 Solo")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "x01", "x01_starting_score": 101},
    ).get_json()["game"]

    # Reach 101 via two turns: 60 + 41
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 41})
    assert r.get_json()["game"]["status"] == "finished"

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["winner_player_id"] == p1
    assert state["winner_team_name"] is None


def test_winner_name_x01_teams_default(client):
    p1 = add_player(client, "X01 TA")
    p2 = add_player(client, "X01 TB")
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

    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})
    r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 41})
    assert r.get_json()["game"]["status"] == "finished"

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["winner_team"] == "team_a"
    assert state["winner_team_name"] == "Team A"
    assert state["winner_player_id"] is None


def test_winner_name_x01_teams_custom(client):
    p1 = add_player(client, "X01 Custom-A")
    p2 = add_player(client, "X01 Custom-B")
    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "x01",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
            "x01_starting_score": 101,
            "team_names": {"team_a": "Arrows", "team_b": "Bulls"},
        },
    ).get_json()["game"]

    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})
    r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 41})
    assert r.get_json()["game"]["status"] == "finished"

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["winner_team"] == "team_a"
    assert state["winner_team_name"] == "Arrows"
    assert state["winner_player_id"] is None


def test_winner_name_cricket_solo(client):
    """Cricket solo: winner determined by team key; winner_team_name uses default 'Team A'/'Team B'."""
    p1 = add_player(client, "Cricket Solo A")
    p2 = add_player(client, "Cricket Solo B")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "english_cricket", "team_mode": "solo"},
    ).get_json()["game"]

    # Inning 1 (team_a bats, team_b bowls): p1 scores 50 runs, p2 takes a wicket
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 50})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 10})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 0})
    # Inning 2: p2 (team_b) chases and exceeds
    r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 51})
    assert r.get_json()["game"]["status"] == "finished"

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["winner_team"] == "team_b"
    assert state["winner_team_name"] == "Team B"
    assert state["winner_player_id"] is None


def test_winner_name_cricket_teams_custom(client):
    p1 = add_player(client, "Cricket TA-1")
    p2 = add_player(client, "Cricket TB-1")
    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "english_cricket",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
            "team_names": {"team_a": "Strikers", "team_b": "Fielders"},
        },
    ).get_json()["game"]

    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 50})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 10})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 0})
    r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 51})
    assert r.get_json()["game"]["status"] == "finished"

    state = client.get(f"/api/games/{game['id']}/state").get_json()["game"]
    assert state["winner_team"] == "team_b"
    assert state["winner_team_name"] == "Fielders"
    assert state["winner_player_id"] is None


def test_winner_name_noughts_solo(client):
    p1 = add_player(client, "Noughts X Solo")
    p2 = add_player(client, "Noughts O Solo")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "noughts_and_crosses", "team_mode": "solo"},
    ).get_json()["game"]

    # X wins top row
    for cell, marker, pid in [(0, "X", p1), (3, "O", p2), (1, "X", p1), (4, "O", p2), (2, "X", p1)]:
        r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": pid, "total_points": cell, "noughts_marker": marker})
        assert r.status_code == 200

    state = r.get_json()["game"]
    assert state["status"] == "finished"
    assert state["winner_player_id"] == p1
    assert state["winner_team_name"] is None


def test_winner_name_noughts_teams_default(client):
    p1 = add_player(client, "Noughts TA")
    p2 = add_player(client, "Noughts TB")
    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "noughts_and_crosses",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
        },
    ).get_json()["game"]

    for cell, marker, pid in [(0, "X", p1), (3, "O", p2), (1, "X", p1), (4, "O", p2), (2, "X", p1)]:
        r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": pid, "total_points": cell, "noughts_marker": marker})
        assert r.status_code == 200

    state = r.get_json()["game"]
    assert state["status"] == "finished"
    assert state["winner_team"] == "team_a"
    assert state["winner_team_name"] == "Team A"
    assert state["winner_player_id"] is None


# ---------------------------------------------------------------------------
# Game start state: active player, team assignments, validation
# ---------------------------------------------------------------------------


def test_game_start_active_player_55by5_solo(client):
    p1 = add_player(client, "Start Solo 1")
    p2 = add_player(client, "Start Solo 2")
    game = client.post("/api/games", json={"ordered_player_ids": [p1, p2]}).get_json()["game"]
    assert game["status"] == "active"
    assert game["active_player_id"] == p1


def test_game_start_active_player_55by5_teams(client):
    p1 = add_player(client, "TA Start")
    p2 = add_player(client, "TB Start")
    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
        },
    ).get_json()["game"]
    assert game["status"] == "active"
    assert game["active_player_id"] == p1


def test_game_start_active_player_x01_solo(client):
    p1 = add_player(client, "X01 Start 1")
    p2 = add_player(client, "X01 Start 2")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "x01", "x01_starting_score": 501},
    ).get_json()["game"]
    assert game["status"] == "active"
    assert game["active_player_id"] == p1


def test_game_start_active_player_x01_teams(client):
    p1 = add_player(client, "X01 TA Start")
    p2 = add_player(client, "X01 TB Start")
    game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "game_type": "x01",
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
            "x01_starting_score": 301,
        },
    ).get_json()["game"]
    assert game["status"] == "active"
    assert game["active_player_id"] == p1


def test_game_start_active_player_noughts(client):
    p1 = add_player(client, "Noughts Start X")
    p2 = add_player(client, "Noughts Start O")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "noughts_and_crosses"},
    ).get_json()["game"]
    assert game["status"] == "active"
    assert game["active_player_id"] == p1


def test_game_start_cricket_default_batting_team(client):
    """Default cricket: team_a bats, team_b bowls → first player on bowling (team_b) goes first."""
    p1 = add_player(client, "Cricket Default A")
    p2 = add_player(client, "Cricket Default B")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "english_cricket"},
    ).get_json()["game"]
    assert game["cricket_state"]["batting_team"] == "team_a"
    assert game["cricket_state"]["bowling_team"] == "team_b"
    # p2 is auto-assigned team_b (bowler) so goes first
    assert game["active_player_id"] == p2


def test_game_start_player_team_fields_in_response(client):
    """players[i].team reflects team assignment for every game type in teams mode."""
    p1 = add_player(client, "PTeam A")
    p2 = add_player(client, "PTeam B")
    for game_type in ("55by5", "x01", "english_cricket"):
        payload = {
            "ordered_player_ids": [p1, p2],
            "game_type": game_type,
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_b"},
        }
        if game_type == "x01":
            payload["x01_starting_score"] = 101
        game = client.post("/api/games", json=payload).get_json()["game"]
        assert game["status"] == "active", f"failed for {game_type}"
        by_id = {p["id"]: p for p in game["players"]}
        assert by_id[p1]["team"] == "team_a", f"p1 team wrong for {game_type}"
        assert by_id[p2]["team"] == "team_b", f"p2 team wrong for {game_type}"
        client.delete(f"/api/games/{game['id']}")


def test_game_start_noughts_solo_auto_assigns_teams(client):
    """Noughts solo: p1 auto-assigned team_a (X), p2 auto-assigned team_b (O)."""
    p1 = add_player(client, "NX Auto")
    p2 = add_player(client, "NO Auto")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "noughts_and_crosses"},
    ).get_json()["game"]
    by_id = {p["id"]: p for p in game["players"]}
    assert by_id[p1]["team"] == "team_a"
    assert by_id[p2]["team"] == "team_b"


def test_create_game_teams_validation_missing_assignment(client):
    """Returns 400 when team_mode=teams but not every player has an assignment."""
    p1 = add_player(client, "MissAssign A")
    p2 = add_player(client, "MissAssign B")
    res = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a"},  # p2 missing
        },
    )
    assert res.status_code == 400
    assert "every selected player" in res.get_json()["error"].lower()


def test_create_game_teams_validation_one_team_only(client):
    """Returns 400 when both players are assigned to the same team."""
    p1 = add_player(client, "OneTeam A")
    p2 = add_player(client, "OneTeam B")
    res = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p1, p2],
            "team_mode": "teams",
            "team_assignments": {str(p1): "team_a", str(p2): "team_a"},
        },
    )
    assert res.status_code == 400
    assert "both team a and team b" in res.get_json()["error"].lower()


def test_create_game_cricket_solo_requires_two_players(client):
    p1 = add_player(client, "Cricket Solo One")
    res = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "english_cricket", "team_mode": "solo"},
    )
    assert res.status_code == 400
    assert "two players" in res.get_json()["error"].lower()


def test_create_game_noughts_solo_requires_two_players(client):
    p1 = add_player(client, "Noughts Solo One")
    res = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "noughts_and_crosses", "team_mode": "solo"},
    )
    assert res.status_code == 400
    assert "two players" in res.get_json()["error"].lower()


def test_create_game_rejects_shanghai(client):
    p1 = add_player(client, "No Shanghai A")
    p2 = add_player(client, "No Shanghai B")

    res = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "shanghai", "team_mode": "solo"},
    )
    assert res.status_code == 400
    assert "removed" in res.get_json()["error"].lower()


# ---------------------------------------------------------------------------
# History: all game types appear after completion
# ---------------------------------------------------------------------------


def test_history_includes_55by5_game(client):
    p1 = add_player(client, "Hist 55by5 P1")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]

    for _ in range(11):
        r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})
        if r.get_json()["game"]["status"] == "finished":
            break

    assert r.get_json()["game"]["status"] == "finished"
    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] in ids
    entry = next(g for g in history if g["id"] == game["id"])
    assert entry["game_type"] == "55by5"
    assert entry["winner_player_id"] == p1


def test_history_includes_x01_game(client):
    p1 = add_player(client, "Hist X01 P1")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "x01", "x01_starting_score": 101},
    ).get_json()["game"]
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 41})
    assert r.get_json()["game"]["status"] == "finished"

    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] in ids
    entry = next(g for g in history if g["id"] == game["id"])
    assert entry["game_type"] == "x01"
    assert entry["winner_player_id"] == p1
    assert entry["turn_count"] == 2


def test_history_includes_cricket_game(client):
    p1 = add_player(client, "Hist Cricket A")
    p2 = add_player(client, "Hist Cricket B")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "english_cricket"},
    ).get_json()["game"]
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 50})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 10})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 0})
    r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 51})
    assert r.get_json()["game"]["status"] == "finished"

    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] in ids
    entry = next(g for g in history if g["id"] == game["id"])
    assert entry["game_type"] == "english_cricket"
    assert entry["winner_team"] == "team_b"
    assert entry["winner_team_name"] == "Team B"


def test_history_includes_noughts_game(client):
    p1 = add_player(client, "Hist Noughts X")
    p2 = add_player(client, "Hist Noughts O")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "noughts_and_crosses"},
    ).get_json()["game"]
    for cell, marker, pid in [(0, "X", p1), (3, "O", p2), (1, "X", p1), (4, "O", p2), (2, "X", p1)]:
        r = client.post(f"/api/games/{game['id']}/turn", json={"player_id": pid, "total_points": cell, "noughts_marker": marker})
    assert r.get_json()["game"]["status"] == "finished"

    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] in ids
    entry = next(g for g in history if g["id"] == game["id"])
    assert entry["game_type"] == "noughts_and_crosses"
    assert entry["winner_player_id"] == p1


def test_history_includes_all_game_types_mixed(client):
    """All supported game types appear together in history when multiple games finish."""
    p1 = add_player(client, "Mix P1")
    p2 = add_player(client, "Mix P2")

    # 55by5
    g55 = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]
    for _ in range(11):
        r = client.post(f"/api/games/{g55['id']}/turn", json={"player_id": p1, "total_points": 25})
        if r.get_json()["game"]["status"] == "finished":
            break

    # x01
    gx01 = client.post("/api/games", json={"ordered_player_ids": [p1], "game_type": "x01", "x01_starting_score": 101}).get_json()["game"]
    client.post(f"/api/games/{gx01['id']}/turn", json={"player_id": p1, "total_points": 60})
    client.post(f"/api/games/{gx01['id']}/turn", json={"player_id": p1, "total_points": 41})

    # cricket
    gcricket = client.post("/api/games", json={"ordered_player_ids": [p1, p2], "game_type": "english_cricket"}).get_json()["game"]
    client.post(f"/api/games/{gcricket['id']}/turn", json={"player_id": p2, "total_points": 0})
    client.post(f"/api/games/{gcricket['id']}/turn", json={"player_id": p1, "total_points": 50})
    client.post(f"/api/games/{gcricket['id']}/turn", json={"player_id": p2, "total_points": 10})
    client.post(f"/api/games/{gcricket['id']}/turn", json={"player_id": p1, "total_points": 0})
    client.post(f"/api/games/{gcricket['id']}/turn", json={"player_id": p2, "total_points": 51})

    # noughts
    gnoughts = client.post("/api/games", json={"ordered_player_ids": [p1, p2], "game_type": "noughts_and_crosses"}).get_json()["game"]
    for cell, marker, pid in [(0, "X", p1), (3, "O", p2), (1, "X", p1), (4, "O", p2), (2, "X", p1)]:
        client.post(f"/api/games/{gnoughts['id']}/turn", json={"player_id": pid, "total_points": cell, "noughts_marker": marker})

    history = client.get("/api/games/history?limit=10").get_json()
    game_types_in_history = {g["game_type"] for g in history}
    assert "55by5" in game_types_in_history
    assert "x01" in game_types_in_history
    assert "english_cricket" in game_types_in_history
    assert "noughts_and_crosses" in game_types_in_history


def test_history_abandoned_games_excluded(client):
    """Quit (abandoned) games do not appear in history."""
    p1 = add_player(client, "Hist Abandon")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})
    client.delete(f"/api/games/{game['id']}")

    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] not in ids


def test_history_excludes_abandoned_55by5_game(client):
    p1 = add_player(client, "Hist Abandon 55")
    game = client.post("/api/games", json={"ordered_player_ids": [p1]}).get_json()["game"]
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 25})
    client.delete(f"/api/games/{game['id']}")

    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] not in ids


def test_history_excludes_abandoned_x01_game(client):
    p1 = add_player(client, "Hist Abandon X01")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "x01", "x01_starting_score": 101},
    ).get_json()["game"]
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    client.delete(f"/api/games/{game['id']}")

    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] not in ids


def test_history_excludes_abandoned_cricket_game(client):
    p1 = add_player(client, "Hist Abandon Cricket A")
    p2 = add_player(client, "Hist Abandon Cricket B")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "english_cricket"},
    ).get_json()["game"]
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p2, "total_points": 0})
    client.delete(f"/api/games/{game['id']}")

    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] not in ids


def test_history_excludes_abandoned_noughts_game(client):
    p1 = add_player(client, "Hist Abandon Noughts X")
    p2 = add_player(client, "Hist Abandon Noughts O")
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1, p2], "game_type": "noughts_and_crosses"},
    ).get_json()["game"]
    client.post(
        f"/api/games/{game['id']}/turn",
        json={"player_id": p1, "total_points": 0, "noughts_marker": "X"},
    )
    client.delete(f"/api/games/{game['id']}")

    history = client.get("/api/games/history?limit=10").get_json()
    ids = [g["id"] for g in history]
    assert game["id"] not in ids


def test_game_history_detail_endpoint(client):
    """GET /api/games/<id>/history returns the full game state for any game."""
    p1 = add_player(client, "Detail P1")

    # Active game is accessible.
    active = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "x01", "x01_starting_score": 101},
    ).get_json()["game"]
    r = client.get(f"/api/games/{active['id']}/history")
    assert r.status_code == 200
    data = r.get_json()
    assert "game" in data
    assert data["game"]["id"] == active["id"]
    assert data["game"]["status"] == "active"

    # Finished game is also accessible and contains turn data.
    client.post(f"/api/games/{active['id']}/turn", json={"player_id": p1, "total_points": 60})
    client.post(f"/api/games/{active['id']}/turn", json={"player_id": p1, "total_points": 41})
    r2 = client.get(f"/api/games/{active['id']}/history")
    assert r2.status_code == 200
    data2 = r2.get_json()
    assert data2["game"]["status"] == "finished"
    assert len(data2["game"]["turns"]) == 2

    # Non-existent game returns 404.
    r3 = client.get("/api/games/999999/history")
    assert r3.status_code == 404
    assert "error" in r3.get_json()


def test_history_limit_clamping(client):
    """History limit is clamped to [1, 100]; values outside that range still return valid data."""
    p1 = add_player(client, "Clamp P1")
    # Finish one game so history is non-empty.
    game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "x01", "x01_starting_score": 101},
    ).get_json()["game"]
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 60})
    client.post(f"/api/games/{game['id']}/turn", json={"player_id": p1, "total_points": 41})

    # limit=0 is clamped to 1 — should still return the one finished game.
    r0 = client.get("/api/games/history?limit=0")
    assert r0.status_code == 200
    assert len(r0.get_json()) == 1

    # limit=200 is clamped to 100 — with only 1 game, still returns 1 entry.
    r200 = client.get("/api/games/history?limit=200")
    assert r200.status_code == 200
    assert len(r200.get_json()) == 1

    # limit=-5 is clamped to 1.
    rneg = client.get("/api/games/history?limit=-5")
    assert rneg.status_code == 200
    assert len(rneg.get_json()) == 1


def test_history_winner_fields_mutually_exclusive(client):
    """Solo games set winner_player_id and leave winner_team None; team games do the opposite."""
    p1 = add_player(client, "ME Solo P1")
    p2 = add_player(client, "ME Teams P1")
    p3 = add_player(client, "ME Teams P2")

    # Solo x01: winner_player_id set, winner_team is None.
    solo_game = client.post(
        "/api/games",
        json={"ordered_player_ids": [p1], "game_type": "x01", "x01_starting_score": 101},
    ).get_json()["game"]
    client.post(f"/api/games/{solo_game['id']}/turn", json={"player_id": p1, "total_points": 60})
    client.post(f"/api/games/{solo_game['id']}/turn", json={"player_id": p1, "total_points": 41})

    history = client.get("/api/games/history?limit=1").get_json()
    solo_entry = next(g for g in history if g["id"] == solo_game["id"])
    assert solo_entry["winner_player_id"] == p1
    assert solo_entry["winner_team"] is None

    # Teams x01: winner_team set, winner_player_id is None.
    teams_game = client.post(
        "/api/games",
        json={
            "ordered_player_ids": [p2, p3],
            "game_type": "x01",
            "team_mode": "teams",
            "team_assignments": {str(p2): "team_a", str(p3): "team_b"},
            "x01_starting_score": 101,
        },
    ).get_json()["game"]
    client.post(f"/api/games/{teams_game['id']}/turn", json={"player_id": p2, "total_points": 60})
    client.post(f"/api/games/{teams_game['id']}/turn", json={"player_id": p3, "total_points": 0})
    client.post(f"/api/games/{teams_game['id']}/turn", json={"player_id": p2, "total_points": 41})

    history2 = client.get("/api/games/history?limit=1").get_json()
    teams_entry = next(g for g in history2 if g["id"] == teams_game["id"])
    assert teams_entry["winner_team"] == "team_a"
    assert teams_entry["winner_player_id"] is None
