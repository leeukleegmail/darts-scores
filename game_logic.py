from __future__ import annotations

from datetime import datetime, timezone
import json
import random
from typing import Any


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
X01_VALID_STARTING_SCORES = (1001, 501, 301, 101)
X01_RESULT_SCORED = 0
X01_RESULT_BUST_OVERSHOOT = 1
X01_RESULT_BUST_LEAVE_ONE = 2

X01_CHECKOUTS = {
    170: "T20 T20 Bull",
    167: "T20 T19 Bull",
    164: "T20 T18 Bull",
    161: "T20 T17 Bull",
    160: "T20 T20 D20",
    158: "T20 T20 D19",
    157: "T20 T19 D20",
    156: "T20 T20 D18",
    155: "T20 T19 D19",
    154: "T20 T18 D20",
    153: "T20 T19 D18",
    152: "T20 T20 D16",
    151: "T20 T17 D20",
    150: "T20 T18 D18",
    149: "T20 T19 D16",
    148: "T20 T16 D20",
    147: "T20 T17 D18",
    146: "T20 T18 D16",
    145: "T20 T15 D20",
    144: "T20 T20 D12",
    143: "T20 T17 D16",
    142: "T20 T14 D20",
    141: "T20 T19 D12",
    140: "T20 T20 D10",
    139: "T19 T14 D20",
    138: "T20 T18 D12",
    137: "T19 T16 D16",
    136: "T20 T20 D8",
    135: "Bull T15 D20",
    134: "T20 T14 D16",
    133: "T20 T19 D8",
    132: "Bull Bull D16",
    131: "T20 T13 D16",
    130: "T20 T20 D5",
    129: "T19 T16 D12",
    128: "T18 T14 D16",
    127: "T20 T17 D8",
    126: "T19 T19 D6",
    125: "Bull T15 D20",
    124: "T20 T16 D8",
    123: "T19 T16 D9",
    122: "T18 T18 D7",
    121: "T20 T11 D14",
    120: "T20 20 D20",
    119: "T19 T12 D13",
    118: "T20 18 D20",
    117: "T20 17 D20",
    116: "T20 16 D20",
    115: "T20 15 D20",
    114: "T20 14 D20",
    113: "T20 13 D20",
    112: "T20 20 D16",
    111: "T20 19 D16",
    110: "T20 18 D16",
    109: "T20 17 D16",
    108: "T20 16 D16",
    107: "T19 18 D16",
    106: "T20 14 D16",
    105: "T20 13 D16",
    104: "T18 18 D16",
    103: "T19 10 D18",
    102: "T20 10 D16",
    101: "T17 10 D20",
    100: "T20 D20",
    99: "T19 10 D16",
    98: "T20 D19",
    97: "T19 D20",
    96: "T20 D18",
    95: "T19 D19",
    94: "T18 D20",
    93: "T19 D18",
    92: "T20 D16",
    91: "T17 D20",
    90: "T18 D18",
    89: "T19 D16",
    88: "T16 D20",
    87: "T17 D18",
    86: "T18 D16",
    85: "T15 D20",
    84: "T20 D12",
    83: "T17 D16",
    82: "Bull D16",
    81: "T19 D12",
    80: "T20 D10",
    79: "T19 D11",
    78: "T18 D12",
    77: "T19 D10",
    76: "T20 D8",
    75: "T17 D12",
    74: "T14 D16",
    73: "T19 D8",
    72: "T16 D12",
    71: "T13 D16",
    70: "T18 D8",
    69: "T19 D6",
    68: "T20 D4",
    67: "T17 D8",
    66: "T10 D18",
    65: "25 D20",
    64: "T16 D8",
    63: "T13 D12",
    62: "T10 D16",
    61: "T15 D8",
    60: "20 D20",
    59: "19 D20",
    58: "18 D20",
    57: "17 D20",
    56: "16 D20",
    55: "15 D20",
    54: "14 D20",
    53: "13 D20",
    52: "20 D16",
    51: "19 D16",
    50: "18 D16",
    49: "17 D16",
    48: "16 D16",
    47: "15 D16",
    46: "14 D16",
    45: "13 D16",
    44: "12 D16",
    43: "11 D16",
    42: "10 D16",
    41: "9 D16",
    40: "D20",
    39: "7 D16",
    38: "D19",
    37: "5 D16",
    36: "D18",
    35: "3 D16",
    34: "D17",
    33: "1 D16",
    32: "D16",
    31: "15 D8",
    30: "10 D10",
    28: "D14",
    26: "D13",
    24: "D12",
    22: "D11",
    20: "D10",
    18: "D9",
    16: "D8",
    14: "D7",
    12: "D6",
    10: "D5",
    8: "D4",
    6: "D3",
    4: "D2",
    2: "D1",
}


def now_iso(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.isoformat()


def generate_random_noughts_targets() -> list[str]:
    targets = []
    for index in range(9):
        if index == 4:
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
    if game_type in {"x01", "501", "301", "1001", "101"}:
        return "x01"
    if game_type in {"noughts_and_crosses", "noughts-and-crosses", "noughts", "tic_tac_toe", "tic-tac-toe", "tic tac toe"}:
        return "noughts_and_crosses"
    return "55by5"


def normalize_team_mode(raw_mode: str | None) -> str:
    team_mode = (raw_mode or "solo").strip().lower()
    return "teams" if team_mode == "teams" else "solo"


def normalize_cricket_team(raw_team: str | None, default: str = TEAM_A) -> str:
    team = (raw_team or default).strip().lower() if isinstance(raw_team, str) else default
    return TEAM_B if team == TEAM_B else TEAM_A


def build_initial_cricket_state(starting_batting_team: str | None = TEAM_A) -> dict[str, Any]:
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


def build_initial_noughts_and_crosses_state() -> dict[str, Any]:
    return {
        "cells": [{"label": label, "mark": None} for label in generate_random_noughts_targets()],
        "winner_marker": None,
        "winning_line": [],
    }


def normalize_x01_starting_score(raw_score: object, default: int = 501) -> int:
    if isinstance(raw_score, int) and raw_score in X01_VALID_STARTING_SCORES:
        return raw_score
    return default


def x01_entity_keys(team_mode: str, ordered_player_ids: list[int], assignments: dict[int, str]) -> list[str]:
    if team_mode == "teams":
        present_teams = {assignments.get(player_id) for player_id in ordered_player_ids}
        return [team_key for team_key in (TEAM_A, TEAM_B) if team_key in present_teams]
    return [str(player_id) for player_id in ordered_player_ids]


def build_initial_x01_state(
    ordered_player_ids: list[int],
    assignments: dict[int, str],
    team_mode: str,
    starting_score: int = 501,
) -> dict[str, Any]:
    normalized_start = normalize_x01_starting_score(starting_score)
    return {
        "starting_score": normalized_start,
        "remaining_scores": {
            key: normalized_start
            for key in x01_entity_keys(team_mode, ordered_player_ids, assignments)
        },
    }


def parse_x01_state(
    raw_value: str | None,
    ordered_player_ids: list[int],
    assignments: dict[int, str],
    team_mode: str,
) -> dict[str, Any]:
    default_state = build_initial_x01_state(ordered_player_ids, assignments, team_mode)
    if not raw_value:
        return default_state
    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError):
        return default_state
    if not isinstance(decoded, dict):
        return default_state

    starting_score = normalize_x01_starting_score(decoded.get("starting_score"), default_state["starting_score"])
    state = build_initial_x01_state(ordered_player_ids, assignments, team_mode, starting_score)
    remaining_scores = decoded.get("remaining_scores") if isinstance(decoded.get("remaining_scores"), dict) else {}
    for key in state["remaining_scores"]:
        raw_remaining = remaining_scores.get(key)
        if isinstance(raw_remaining, int) and 0 <= raw_remaining <= starting_score:
            state["remaining_scores"][key] = raw_remaining
    return state


def x01_entity_key_for_player(game: Any, player_id: int, assignments: dict[int, str]) -> str:
    if getattr(game, "team_mode", "solo") == "teams":
        return assignments.get(player_id, TEAM_A)
    return str(player_id)


def encode_x01_turn_result(result: str | None) -> int:
    if result == "bust_overshoot":
        return X01_RESULT_BUST_OVERSHOOT
    if result == "bust_leave_one":
        return X01_RESULT_BUST_LEAVE_ONE
    return X01_RESULT_SCORED


def decode_x01_turn_result(encoded_result: int | None) -> str:
    if encoded_result == X01_RESULT_BUST_OVERSHOOT:
        return "bust_overshoot"
    if encoded_result == X01_RESULT_BUST_LEAVE_ONE:
        return "bust_leave_one"
    return "scored"


def x01_checkout_hint(remaining: int, opened: bool) -> str | None:
    if not opened:
        return None
    return X01_CHECKOUTS.get(remaining)


def starting_turn_position(ordered_players: list[dict[str, Any]], assignments: dict[int, str], bowling_team: str | None) -> int:
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

    assignments: dict[int, str] = {}
    for key, value in decoded.items():
        try:
            player_id = int(key)
        except (TypeError, ValueError):
            continue
        if value in {TEAM_A, TEAM_B}:
            assignments[player_id] = value
    return assignments


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


def parse_cricket_state(raw_value: str | None) -> dict[str, Any]:
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


def parse_noughts_and_crosses_state(raw_value: str | None) -> dict[str, Any]:
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
    winning_line = [index for index in raw_winning_line if isinstance(index, int) and 0 <= index < 9][:3]
    return {
        "cells": cells,
        "winner_marker": normalize_noughts_marker(decoded.get("winner_marker"), None),
        "winning_line": winning_line,
    }


def marker_for_team(team_key: str | None) -> str:
    return NOUGHTS_AND_CROSSES_MARK_O if team_key == TEAM_B else NOUGHTS_AND_CROSSES_MARK_X


def check_noughts_and_crosses_winner(cells: list[dict[str, Any]]) -> tuple[str | None, list[int]]:
    for line in NOUGHTS_AND_CROSSES_WIN_LINES:
        marks = [cells[index].get("mark") for index in line]
        if marks[0] and marks.count(marks[0]) == 3:
            return marks[0], list(line)
    return None, []


def finish_game(game: Any, *, winner_player_id: int | None = None, winner_team: str | None = None) -> None:
    game.status = "finished"
    game.winner_player_id = winner_player_id
    game.winner_team = winner_team
    game.finished_at = datetime.now(timezone.utc)


def finish_noughts_and_crosses_game(
    game: Any,
    ordered_players: list[dict[str, Any]],
    assignments: dict[int, str],
    marker: str,
) -> None:
    winning_team = TEAM_A if marker == NOUGHTS_AND_CROSSES_MARK_X else TEAM_B
    if getattr(game, "team_mode", "solo") == "teams":
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


def reset_game_scores(score_rows: list[Any], initial_value: int = 0) -> dict[int, Any]:
    score_by_player = {row.player_id: row for row in score_rows}
    for row in score_rows:
        row.fives = initial_value
    return score_by_player


def reset_game_progress(game: Any) -> None:
    game.status = "active"
    game.current_turn_position = 0
    game.winner_player_id = None
    game.winner_team = None
    game.finished_at = None


def apply_standard_turn(
    game: Any,
    turn: Any,
    score_row: Any,
    assignments: dict[int, str],
    team_totals: dict[str, int],
) -> None:
    _, counted, awarded = turn_result(turn.total_points)

    if getattr(game, "team_mode", "solo") == "teams":
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
    game: Any,
    turn: Any,
    score_row: Any,
    assignments: dict[int, str],
    cricket_state: dict[str, Any],
) -> None:
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
    game: Any,
    turn: Any,
    ordered_players: list[dict[str, Any]],
    assignments: dict[int, str],
    noughts_state: dict[str, Any],
) -> None:
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


def apply_x01_turn(
    game: Any,
    turn: Any,
    ordered_players: list[dict[str, Any]],
    score_by_player: dict[int, Any],
    assignments: dict[int, str],
    x01_state: dict[str, Any],
) -> None:
    entity_key = x01_entity_key_for_player(game, turn.player_id, assignments)
    remaining_scores = x01_state["remaining_scores"]
    remaining = int(remaining_scores.get(entity_key, x01_state["starting_score"]))
    result = "scored"

    projected_remaining = remaining - turn.total_points
    if projected_remaining < 0:
        result = "bust_overshoot"
    elif projected_remaining == 1:
        result = "bust_leave_one"
    if result != "scored":
        turn.counted = False
        turn.fives_awarded = 0
        turn.dart_3 = encode_x01_turn_result(result)
        return

    turn.counted = turn.total_points > 0 or projected_remaining == 0
    turn.fives_awarded = turn.total_points
    turn.dart_3 = encode_x01_turn_result("scored")
    remaining_scores[entity_key] = projected_remaining

    if getattr(game, "team_mode", "solo") == "teams":
        for player in ordered_players:
            if assignments.get(player["id"], TEAM_A) == entity_key:
                score_row = score_by_player.get(player["id"])
                if score_row:
                    score_row.fives = projected_remaining
    else:
        score_row = score_by_player.get(turn.player_id)
        if score_row:
            score_row.fives = projected_remaining

    if projected_remaining == 0:
        if getattr(game, "team_mode", "solo") == "teams":
            finish_game(game, winner_team=entity_key)
        else:
            finish_game(game, winner_player_id=turn.player_id)


def recompute_game_state(
    game: Any,
    *,
    ordered_players: list[dict[str, Any]],
    score_rows: list[Any],
    turns: list[Any],
) -> None:
    if not ordered_players:
        return

    assignments = parse_team_assignments(game.team_assignments)
    initial_score = 0
    if game.game_type == "x01":
        stored_x01_state = parse_x01_state(
            game.x01_state,
            [player["id"] for player in ordered_players],
            assignments,
            game.team_mode,
        )
        initial_score = stored_x01_state["starting_score"]

    score_by_player = reset_game_scores(score_rows, initial_score)
    reset_game_progress(game)

    stored_cricket_state = parse_cricket_state(game.cricket_state)
    stored_noughts_state = parse_noughts_and_crosses_state(game.noughts_and_crosses_state)
    stored_x01_state = parse_x01_state(
        game.x01_state,
        [player["id"] for player in ordered_players],
        assignments,
        game.team_mode,
    )

    if game.game_type == "english_cricket":
        cricket_state = build_initial_cricket_state(stored_cricket_state["starting_batting_team"])
        game.current_turn_position = starting_turn_position(ordered_players, assignments, cricket_state["bowling_team"])
    else:
        cricket_state = stored_cricket_state

    if game.game_type == "noughts_and_crosses":
        noughts_state = stored_noughts_state
        for cell in noughts_state["cells"]:
            cell["mark"] = None
        noughts_state["winner_marker"] = None
        noughts_state["winning_line"] = []
    else:
        noughts_state = stored_noughts_state

    if game.game_type == "x01":
        x01_state = build_initial_x01_state(
            [player["id"] for player in ordered_players],
            assignments,
            game.team_mode,
            stored_x01_state["starting_score"],
        )
    else:
        x01_state = stored_x01_state

    team_totals = {TEAM_A: 0, TEAM_B: 0}
    for index, turn in enumerate(turns, start=1):
        turn.turn_number = index
        turn.counted = False
        turn.fives_awarded = 0

        if game.status != "active":
            continue

        expected_player_id = ordered_players[game.current_turn_position]["id"]
        if turn.player_id != expected_player_id:
            continue

        score_row = score_by_player.get(turn.player_id)
        if not score_row:
            continue

        if game.game_type == "english_cricket":
            apply_cricket_turn(game, turn, score_row, assignments, cricket_state)
        elif game.game_type == "x01":
            apply_x01_turn(game, turn, ordered_players, score_by_player, assignments, x01_state)
        elif game.game_type == "noughts_and_crosses":
            apply_noughts_and_crosses_turn(game, turn, ordered_players, assignments, noughts_state)
        else:
            apply_standard_turn(game, turn, score_row, assignments, team_totals)

        if game.status == "active":
            game.current_turn_position = (game.current_turn_position + 1) % len(ordered_players)

    if game.game_type == "english_cricket":
        game.cricket_state = json.dumps(cricket_state)
    if game.game_type == "x01":
        game.x01_state = json.dumps(x01_state)
    if game.game_type == "noughts_and_crosses":
        game.noughts_and_crosses_state = json.dumps(noughts_state)


def active_player_id_for_game(game: Any, ordered_players: list[dict[str, Any]]) -> int | None:
    if game.status != "active" or not ordered_players:
        return None
    if not 0 <= game.current_turn_position < len(ordered_players):
        return None
    return ordered_players[game.current_turn_position]["id"]


def serialize_players_for_game(
    ordered_players: list[dict[str, Any]],
    scores: dict[int, int],
    assignments: dict[int, str],
    game: Any,
    x01_state: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "name": item["name"],
            "position": item["position"],
            "fives": scores.get(item["id"], 0),
            "team": assignments.get(item["id"]),
            "x01_remaining": (
                (x01_state or {}).get("remaining_scores", {}).get(
                    x01_entity_key_for_player(game, item["id"], assignments),
                    scores.get(item["id"], 0),
                )
                if game.game_type == "x01"
                else None
            ),
        }
        for item in ordered_players
    ]


def serialize_turns_for_game(turn_rows: list[tuple[Any, Any]], game: Any) -> list[dict[str, Any]]:
    noughts_state = parse_noughts_and_crosses_state(game.noughts_and_crosses_state) if game.game_type == "noughts_and_crosses" else {}
    return [
        {
            "turn_number": turn.turn_number,
            "player_id": turn.player_id,
            "player_name": player.name,
            "total_points": turn.total_points,
            "counted": turn.counted,
            "fives_awarded": turn.fives_awarded,
            "x01_result": decode_x01_turn_result(turn.dart_3) if game.game_type == "x01" else None,
            "noughts_marker": decode_noughts_marker(turn.dart_2) if game.game_type == "noughts_and_crosses" else None,
            "board_index": turn.total_points if game.game_type == "noughts_and_crosses" else None,
            "board_label": (
                noughts_state.get("cells", [])[turn.total_points].get("label")
                if game.game_type == "noughts_and_crosses" and 0 <= turn.total_points < 9
                else None
            ),
            "created_at": now_iso(turn.created_at),
        }
        for turn, player in turn_rows
    ]


def noughts_side_name(
    ordered_players: list[dict[str, Any]],
    assignments: dict[int, str],
    team_names: dict[str, str],
    team_key: str,
    team_mode: str,
) -> str:
    if team_mode == "teams":
        return team_label(team_key, team_names) or ("Team X" if team_key == TEAM_A else "Team O")
    player = next((item for item in ordered_players if assignments.get(item["id"], TEAM_A) == team_key), None)
    return player["name"] if player else ("X" if team_key == TEAM_A else "O")


def build_game_state_payload(
    game: Any,
    *,
    ordered_players: list[dict[str, Any]],
    scores: dict[int, int],
    turn_rows: list[tuple[Any, Any]],
) -> dict[str, Any]:
    assignments = parse_team_assignments(game.team_assignments)
    team_names = parse_team_names(game.team_names)
    noughts_state = parse_noughts_and_crosses_state(game.noughts_and_crosses_state)
    x01_state = parse_x01_state(game.x01_state, [player["id"] for player in ordered_players], assignments, game.team_mode)

    if game.game_type == "noughts_and_crosses":
        noughts_state["x_name"] = noughts_side_name(ordered_players, assignments, team_names, TEAM_A, game.team_mode)
        noughts_state["o_name"] = noughts_side_name(ordered_players, assignments, team_names, TEAM_B, game.team_mode)

    active_player_id = active_player_id_for_game(game, ordered_players)
    if game.game_type == "x01" and active_player_id is not None:
        active_entity_key = x01_entity_key_for_player(game, active_player_id, assignments)
        remaining = x01_state["remaining_scores"].get(active_entity_key, x01_state["starting_score"])
        x01_state["active_entity_key"] = active_entity_key
        x01_state["active_remaining"] = remaining
        x01_state["active_checkout"] = x01_checkout_hint(remaining, True)

    return {
        "id": game.id,
        "status": game.status,
        "game_type": game.game_type,
        "team_mode": game.team_mode,
        "winner_team": game.winner_team,
        "winner_team_name": team_label(game.winner_team, team_names),
        "team_names": team_names,
        "current_turn_position": game.current_turn_position,
        "active_player_id": active_player_id,
        "winner_player_id": game.winner_player_id,
        "started_at": now_iso(game.started_at),
        "finished_at": now_iso(game.finished_at),
        "team_assignments": {str(key): value for key, value in assignments.items()},
        "cricket_state": parse_cricket_state(game.cricket_state) if game.game_type == "english_cricket" else None,
        "x01_state": x01_state if game.game_type == "x01" else None,
        "noughts_and_crosses_state": noughts_state if game.game_type == "noughts_and_crosses" else None,
        "players": serialize_players_for_game(ordered_players, scores, assignments, game, x01_state),
        "turns": serialize_turns_for_game(turn_rows, game),
    }


def game_type_label(game_type: str | None) -> str:
    normalized = normalize_game_type(game_type)
    if normalized == "english_cricket":
        return "English Cricket"
    if normalized == "x01":
        return "X01"
    if normalized == "noughts_and_crosses":
        return "Noughts and Crosses"
    return "55 by 5"


def player_outcome_for_game(game: Any, player_id: int) -> str | None:
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
                player_id = int(raw_player_id)
            except (TypeError, ValueError):
                return None, "team_assignments contains invalid player id."
            if player_id not in ordered_player_ids:
                return None, "team_assignments contains unknown player id."
            if team not in {TEAM_A, TEAM_B}:
                return None, "team_assignments must use team_a or team_b."
            normalized_assignments[player_id] = team

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
    team_mode: str,
    starting_batting_team: str | None,
    x01_starting_score: int,
) -> tuple[int, str | None, str | None, str | None]:
    if game_type == "english_cricket":
        opening_state = build_initial_cricket_state(starting_batting_team)
        ordered_for_start = [{"id": player_id} for player_id in ordered_player_ids]
        initial_turn_position = starting_turn_position(
            ordered_for_start,
            normalized_assignments,
            opening_state["bowling_team"],
        )
        return initial_turn_position, json.dumps(opening_state), None, None

    if game_type == "x01":
        x01_state = build_initial_x01_state(
            ordered_player_ids,
            normalized_assignments,
            team_mode,
            x01_starting_score,
        )
        return 0, None, None, json.dumps(x01_state)

    if game_type == "noughts_and_crosses":
        return 0, None, json.dumps(build_initial_noughts_and_crosses_state()), None

    return 0, None, None, None