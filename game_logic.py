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
X01_VALID_MATCH_TYPES = ("best_of", "first_to")
X01_RESULT_SCORED = 0
X01_RESULT_BUST_OVERSHOOT = 1
X01_RESULT_BUST_LEAVE_ONE = 2
HI_LOW_DEFAULT_LOW = 26
HI_LOW_DEFAULT_HIGH = 45
HI_LOW_RESULT_SUCCESS = 0
HI_LOW_RESULT_ELIMINATED = 1
HALVE_IT_VARIANTS = ("standard", "hardcore")
HALVE_IT_ROUNDS: tuple[dict[str, Any], ...] = (
    {"target": "15", "kind": "number", "entry_mode": "hits", "number": 15},
    {"target": "16", "kind": "number", "entry_mode": "hits", "number": 16},
    {"target": "Any Double", "kind": "double", "entry_mode": "points"},
    {"target": "17", "kind": "number", "entry_mode": "hits", "number": 17},
    {"target": "18", "kind": "number", "entry_mode": "hits", "number": 18},
    {"target": "Any Triple", "kind": "triple", "entry_mode": "points"},
    {"target": "19", "kind": "number", "entry_mode": "hits", "number": 19},
    {"target": "20", "kind": "number", "entry_mode": "hits", "number": 20},
    {"target": "Bullseye", "kind": "bull", "entry_mode": "hits_or_points"},
)
HALVE_IT_TOTAL_ROUNDS = len(HALVE_IT_ROUNDS)
HALVE_IT_HARDCORE_TOTAL_ROUNDS = 9

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
    all_combinations = [
        f"{segment} {number}"
        for segment in NOUGHTS_AND_CROSSES_SEGMENTS
        for number in NOUGHTS_AND_CROSSES_DARTBOARD_NUMBERS
    ]
    chosen = random.sample(all_combinations, 8)
    targets = chosen[:4] + ["Bullseye"] + chosen[4:]
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
    if game_type in {"hi_low", "hi-low", "hilow", "higher_and_lower", "higher-and-lower"}:
        return "hi_low"
    if game_type in {"halve_it", "halve-it", "halveit"}:
        return "halve_it"
    if game_type in {"noughts_and_crosses", "noughts-and-crosses", "noughts", "tic_tac_toe", "tic-tac-toe", "tic tac toe"}:
        return "noughts_and_crosses"
    return "55by5"


def normalize_halve_it_variant(raw_variant: object, default: str = "standard") -> str:
    if isinstance(raw_variant, str):
        candidate = raw_variant.strip().lower()
        if candidate in HALVE_IT_VARIANTS:
            return candidate
    return default


def build_halve_it_standard_rounds() -> list[dict[str, Any]]:
    return [
        {
            "round": index,
            "target": round_def["target"],
            "kind": round_def["kind"],
            "entry_mode": round_def["entry_mode"],
            "number": round_def.get("number"),
        }
        for index, round_def in enumerate(HALVE_IT_ROUNDS, start=1)
    ]


def build_halve_it_hardcore_rounds() -> list[dict[str, Any]]:
    round_3_number = random.choice([19, 16])

    round_8_exact_presets = [41, 101, 123]
    round_5_high_targets = list(round_8_exact_presets)
    round_5_kind = random.choice(["number", "exact_total"])
    round_5_value = 17 if round_5_kind == "number" else random.choice(round_5_high_targets)

    round_8_exact_targets = sorted(round_8_exact_presets)

    return [
        {"round": 1, "target": "20", "kind": "number", "entry_mode": "hits", "number": 20},
        {"round": 2, "target": "Any Double", "kind": "double", "entry_mode": "points"},
        {
            "round": 3,
            "target": str(round_3_number),
            "kind": "number",
            "entry_mode": "hits",
            "number": round_3_number,
        },
        {
            "round": 4,
            "target": "Three Different Colors",
            "kind": "manual_points",
            "entry_mode": "points",
        },
        {
            "round": 5,
            "target": "Score 17" if round_5_kind == "number" else f"Exact {round_5_value}",
            "kind": round_5_kind,
            "entry_mode": "hits" if round_5_kind == "number" else "points",
            "number": 17 if round_5_kind == "number" else None,
            "exact_total": round_5_value if round_5_kind == "exact_total" else None,
        },
        {
            "round": 6,
            "target": "Black-White-Black",
            "kind": "manual_points",
            "entry_mode": "points",
        },
        {"round": 7, "target": "Any Treble", "kind": "triple", "entry_mode": "points"},
        {
            "round": 8,
            "target": f"Exact {round_8_exact_targets[0]} / {round_8_exact_targets[1]} / {round_8_exact_targets[2]}",
            "kind": "exact_total",
            "entry_mode": "points",
            "exact_totals": round_8_exact_targets,
            "exact_presets": round_8_exact_presets,
        },
        {
            "round": 9,
            "target": "Bullseye",
            "kind": "bull",
            "entry_mode": "hits_or_points",
        },
    ]


def build_initial_halve_it_state(variant: str = "standard") -> dict[str, Any]:
    normalized_variant = normalize_halve_it_variant(variant)
    rounds = (
        build_halve_it_hardcore_rounds()
        if normalized_variant == "hardcore"
        else build_halve_it_standard_rounds()
    )
    return {
        "variant": normalized_variant,
        "rounds": rounds,
        "total_rounds": len(rounds),
    }


def parse_halve_it_state(raw_value: str | None) -> dict[str, Any]:
    default_state = build_initial_halve_it_state("standard")
    if not raw_value:
        return default_state
    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError):
        return default_state
    if not isinstance(decoded, dict):
        return default_state

    variant = normalize_halve_it_variant(decoded.get("variant"), "standard")
    rounds = decoded.get("rounds") if isinstance(decoded.get("rounds"), list) else None
    if not rounds:
        return build_initial_halve_it_state(variant)

    normalized_rounds: list[dict[str, Any]] = []
    for index, raw_round in enumerate(rounds, start=1):
        if not isinstance(raw_round, dict):
            continue
        round_copy = dict(raw_round)
        round_copy["round"] = index
        if not isinstance(round_copy.get("target"), str) or not round_copy["target"].strip():
            round_copy["target"] = f"Round {index}"
        round_copy["kind"] = str(round_copy.get("kind") or "number")
        round_copy["entry_mode"] = str(round_copy.get("entry_mode") or "points")
        normalized_rounds.append(round_copy)

    if not normalized_rounds:
        return build_initial_halve_it_state(variant)

    return {
        "variant": variant,
        "rounds": normalized_rounds,
        "total_rounds": len(normalized_rounds),
    }


def halve_it_round_info(round_number: int, halve_it_state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = halve_it_state or build_initial_halve_it_state("standard")
    rounds = state.get("rounds") if isinstance(state.get("rounds"), list) and state.get("rounds") else build_halve_it_standard_rounds()
    total_rounds = len(rounds)
    clamped_round = max(1, min(total_rounds, int(round_number or 1)))
    base = rounds[clamped_round - 1]
    return {
        "round": clamped_round,
        "target": base.get("target", f"Round {clamped_round}"),
        "kind": base.get("kind", "number"),
        "entry_mode": base.get("entry_mode", "points"),
        "number": base.get("number"),
        "exact_total": base.get("exact_total"),
        "exact_totals": base.get("exact_totals"),
        "required_hits": base.get("required_hits"),
        "fixed_points": base.get("fixed_points"),
        "random_numbers": base.get("random_numbers"),
    }


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


def normalize_x01_match_type(raw_match_type: object, default: str = "best_of") -> str:
    if isinstance(raw_match_type, str):
        candidate = raw_match_type.strip().lower()
        if candidate in X01_VALID_MATCH_TYPES:
            return candidate
    return default


def normalize_x01_legs_value(raw_legs_value: object, default: int = 1) -> int:
    if isinstance(raw_legs_value, int) and 1 <= raw_legs_value <= 9:
        return raw_legs_value
    return default


def required_legs_for_x01(match_type: str, legs_value: int) -> int:
    normalized_match_type = normalize_x01_match_type(match_type)
    normalized_legs_value = normalize_x01_legs_value(legs_value)
    if normalized_match_type == "first_to":
        return normalized_legs_value
    return (normalized_legs_value + 1) // 2


def normalize_x01_starting_entity(
    raw_starting_entity: object,
    team_mode: str,
    ordered_player_ids: list[int],
    assignments: dict[int, str],
    default: str | None = None,
) -> str:
    if team_mode == "teams":
        if raw_starting_entity in {TEAM_A, TEAM_B, "random"}:
            return str(raw_starting_entity)
        if default in {TEAM_A, TEAM_B, "random"}:
            return str(default)
        return TEAM_A

    valid_player_ids = {str(player_id) for player_id in ordered_player_ids}
    if isinstance(raw_starting_entity, int) and str(raw_starting_entity) in valid_player_ids:
        return str(raw_starting_entity)
    if isinstance(raw_starting_entity, str):
        candidate = raw_starting_entity.strip().lower()
        if candidate == "random":
            return "random"
        if raw_starting_entity.strip() in valid_player_ids:
            return raw_starting_entity.strip()
    if isinstance(default, str) and default in valid_player_ids | {"random"}:
        return default
    if ordered_player_ids:
        return str(ordered_player_ids[0])
    return "random"


def x01_starting_turn_position(
    ordered_player_ids: list[int],
    assignments: dict[int, str],
    team_mode: str,
    starting_entity: str,
) -> int:
    if not ordered_player_ids:
        return 0
    if starting_entity == "random":
        return random.randrange(len(ordered_player_ids))

    if team_mode == "teams":
        for index, player_id in enumerate(ordered_player_ids):
            if assignments.get(player_id, TEAM_A) == starting_entity:
                return index
        return 0

    for index, player_id in enumerate(ordered_player_ids):
        if str(player_id) == starting_entity:
            return index
    return 0


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
    match_type: str = "best_of",
    legs_value: int = 1,
    starting_entity: str | None = None,
    initial_turn_position: int = 0,
) -> dict[str, Any]:
    normalized_start = normalize_x01_starting_score(starting_score)
    normalized_match_type = normalize_x01_match_type(match_type)
    normalized_legs_value = normalize_x01_legs_value(legs_value)
    entity_keys = x01_entity_keys(team_mode, ordered_player_ids, assignments)
    normalized_starting_entity = normalize_x01_starting_entity(
        starting_entity,
        team_mode,
        ordered_player_ids,
        assignments,
        default=(entity_keys[0] if entity_keys else "random"),
    )
    safe_turn_position = initial_turn_position if 0 <= initial_turn_position < max(1, len(ordered_player_ids)) else 0
    return {
        "starting_score": normalized_start,
        "match_type": normalized_match_type,
        "legs_value": normalized_legs_value,
        "required_legs": required_legs_for_x01(normalized_match_type, normalized_legs_value),
        "starting_entity": normalized_starting_entity,
        "initial_turn_position": safe_turn_position,
        "remaining_scores": {
            key: normalized_start
            for key in entity_keys
        },
        "legs_won": {
            key: 0
            for key in entity_keys
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
    match_type = normalize_x01_match_type(decoded.get("match_type"), default_state["match_type"])
    legs_value = normalize_x01_legs_value(decoded.get("legs_value"), default_state["legs_value"])
    starting_entity = normalize_x01_starting_entity(
        decoded.get("starting_entity"),
        team_mode,
        ordered_player_ids,
        assignments,
        default=default_state["starting_entity"],
    )
    initial_turn_position = decoded.get("initial_turn_position")
    if not isinstance(initial_turn_position, int):
        initial_turn_position = default_state["initial_turn_position"]

    state = build_initial_x01_state(
        ordered_player_ids,
        assignments,
        team_mode,
        starting_score,
        match_type,
        legs_value,
        starting_entity,
        initial_turn_position,
    )
    remaining_scores = decoded.get("remaining_scores") if isinstance(decoded.get("remaining_scores"), dict) else {}
    for key in state["remaining_scores"]:
        raw_remaining = remaining_scores.get(key)
        if isinstance(raw_remaining, int) and 0 <= raw_remaining <= starting_score:
            state["remaining_scores"][key] = raw_remaining

    legs_won = decoded.get("legs_won") if isinstance(decoded.get("legs_won"), dict) else {}
    max_legs = max(1, state["legs_value"])
    for key in state["legs_won"]:
        raw_legs = legs_won.get(key)
        if isinstance(raw_legs, int) and 0 <= raw_legs <= max_legs:
            state["legs_won"][key] = raw_legs

    state["required_legs"] = required_legs_for_x01(state["match_type"], state["legs_value"])
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


def normalize_hi_low_bound(raw_value: object, default: int) -> int:
    if isinstance(raw_value, int) and 0 <= raw_value <= MAX_TURN_TOTAL:
        return raw_value
    return default


def normalize_hi_low_match_type(raw_match_type: object, default: str = "best_of") -> str:
    if isinstance(raw_match_type, str):
        candidate = raw_match_type.strip().lower()
        if candidate in X01_VALID_MATCH_TYPES:
            return candidate
    return default


def normalize_hi_low_legs_value(raw_legs_value: object, default: int = 1) -> int:
    if isinstance(raw_legs_value, int) and 1 <= raw_legs_value <= 9:
        return raw_legs_value
    return default


def required_legs_for_hi_low(match_type: str, legs_value: int) -> int:
    return required_legs_for_x01(
        normalize_hi_low_match_type(match_type),
        normalize_hi_low_legs_value(legs_value),
    )


def normalize_hi_low_start_bounds(
    *,
    use_custom: bool,
    raw_low: object,
    raw_high: object,
) -> tuple[int, int, str | None]:
    if not use_custom:
        return HI_LOW_DEFAULT_LOW, HI_LOW_DEFAULT_HIGH, None

    low_value = normalize_hi_low_bound(raw_low, HI_LOW_DEFAULT_LOW)
    high_value = normalize_hi_low_bound(raw_high, HI_LOW_DEFAULT_HIGH)
    if low_value >= high_value:
        return low_value, high_value, "Hi/Low custom values require low to be less than high."
    return low_value, high_value, None


def hi_low_entity_keys(team_mode: str, ordered_player_ids: list[int], assignments: dict[int, str]) -> list[str]:
    if team_mode == "teams":
        present_teams = {assignments.get(player_id) for player_id in ordered_player_ids}
        return [team_key for team_key in (TEAM_A, TEAM_B) if team_key in present_teams]
    return [str(player_id) for player_id in ordered_player_ids]


def build_initial_hi_low_state(
    low_bound: int = HI_LOW_DEFAULT_LOW,
    high_bound: int = HI_LOW_DEFAULT_HIGH,
    ordered_player_ids: list[int] | None = None,
    assignments: dict[int, str] | None = None,
    team_mode: str = "solo",
    match_type: str = "best_of",
    legs_value: int = 1,
) -> dict[str, Any]:
    normalized_low = normalize_hi_low_bound(low_bound, HI_LOW_DEFAULT_LOW)
    normalized_high = normalize_hi_low_bound(high_bound, HI_LOW_DEFAULT_HIGH)
    if normalized_low >= normalized_high:
        normalized_low = HI_LOW_DEFAULT_LOW
        normalized_high = HI_LOW_DEFAULT_HIGH
    normalized_match_type = normalize_hi_low_match_type(match_type)
    normalized_legs_value = normalize_hi_low_legs_value(legs_value)
    normalized_assignments = assignments or {}
    entity_keys = hi_low_entity_keys(team_mode, ordered_player_ids or [], normalized_assignments)
    return {
        "start_low": normalized_low,
        "start_high": normalized_high,
        "current_low": normalized_low,
        "current_high": normalized_high,
        "match_type": normalized_match_type,
        "legs_value": normalized_legs_value,
        "required_legs": required_legs_for_hi_low(normalized_match_type, normalized_legs_value),
        "legs_won": {
            key: 0
            for key in entity_keys
        },
        "phase": "bounds",
        "current_target": None,
        "eliminated_players": [],
        "last_success": {},
    }


def parse_hi_low_state(
    raw_value: str | None,
    ordered_player_ids: list[int],
    assignments: dict[int, str] | None = None,
    team_mode: str = "solo",
) -> dict[str, Any]:
    default_state = build_initial_hi_low_state(
        ordered_player_ids=ordered_player_ids,
        assignments=assignments,
        team_mode=team_mode,
    )
    if not raw_value:
        return default_state
    try:
        decoded = json.loads(raw_value)
    except (TypeError, ValueError):
        return default_state
    if not isinstance(decoded, dict):
        return default_state

    start_low = normalize_hi_low_bound(decoded.get("start_low"), HI_LOW_DEFAULT_LOW)
    start_high = normalize_hi_low_bound(decoded.get("start_high"), HI_LOW_DEFAULT_HIGH)
    if start_low >= start_high:
        start_low = HI_LOW_DEFAULT_LOW
        start_high = HI_LOW_DEFAULT_HIGH

    match_type = normalize_hi_low_match_type(decoded.get("match_type"), default_state["match_type"])
    legs_value = normalize_hi_low_legs_value(decoded.get("legs_value"), default_state["legs_value"])

    state = build_initial_hi_low_state(
        start_low,
        start_high,
        ordered_player_ids,
        assignments,
        team_mode,
        match_type,
        legs_value,
    )

    current_low = decoded.get("current_low")
    if not isinstance(current_low, int) or not (0 <= current_low <= MAX_TURN_TOTAL):
        current_low = start_low

    current_high = decoded.get("current_high")
    if not isinstance(current_high, int) or not (0 <= current_high <= MAX_TURN_TOTAL):
        current_high = start_high

    if current_low >= current_high:
        current_low = start_low
        current_high = start_high

    allowed_ids = set(ordered_player_ids)
    raw_eliminated = decoded.get("eliminated_players")
    eliminated_players: list[int] = []
    if isinstance(raw_eliminated, list):
        for raw_player_id in raw_eliminated:
            if isinstance(raw_player_id, int) and raw_player_id in allowed_ids and raw_player_id not in eliminated_players:
                eliminated_players.append(raw_player_id)

    last_success: dict[str, int] = {}
    raw_last_success = decoded.get("last_success")
    if isinstance(raw_last_success, dict):
        for raw_player_id, raw_score in raw_last_success.items():
            try:
                player_id = int(raw_player_id)
            except (TypeError, ValueError):
                continue
            if player_id not in allowed_ids or player_id in eliminated_players:
                continue
            if isinstance(raw_score, int) and 0 <= raw_score <= MAX_TURN_TOTAL:
                last_success[str(player_id)] = raw_score

    legs_won = decoded.get("legs_won") if isinstance(decoded.get("legs_won"), dict) else {}
    max_legs = max(1, state["legs_value"])
    for key in state["legs_won"]:
        raw_legs = legs_won.get(key)
        if isinstance(raw_legs, int) and 0 <= raw_legs <= max_legs:
            state["legs_won"][key] = raw_legs

    state["current_low"] = current_low
    state["current_high"] = current_high
    state["phase"] = "bounds"
    state["current_target"] = None
    state["eliminated_players"] = eliminated_players
    state["last_success"] = last_success
    state["required_legs"] = required_legs_for_hi_low(state["match_type"], state["legs_value"])
    return state


def active_hi_low_player_ids(ordered_players: list[dict[str, Any]], hi_low_state: dict[str, Any]) -> list[int]:
    eliminated = set(hi_low_state.get("eliminated_players") or [])
    return [player["id"] for player in ordered_players if player["id"] not in eliminated]


def first_active_hi_low_turn_position(ordered_players: list[dict[str, Any]], hi_low_state: dict[str, Any]) -> int:
    active_ids = set(active_hi_low_player_ids(ordered_players, hi_low_state))
    for index, player in enumerate(ordered_players):
        if player["id"] in active_ids:
            return index
    return 0


def next_active_hi_low_turn_position(current_position: int, ordered_players: list[dict[str, Any]], hi_low_state: dict[str, Any]) -> int:
    if not ordered_players:
        return 0
    active_ids = set(active_hi_low_player_ids(ordered_players, hi_low_state))
    if not active_ids:
        return current_position
    for offset in range(1, len(ordered_players) + 1):
        candidate = (current_position + offset) % len(ordered_players)
        if ordered_players[candidate]["id"] in active_ids:
            return candidate
    return current_position


def encode_hi_low_turn_result(result: str | None) -> int:
    if result == "eliminated":
        return HI_LOW_RESULT_ELIMINATED
    return HI_LOW_RESULT_SUCCESS


def decode_hi_low_turn_result(encoded_result: int | None) -> str:
    if encoded_result == HI_LOW_RESULT_ELIMINATED:
        return "eliminated"
    return "success"


def hi_low_leg_winner_entity(
    game: Any,
    ordered_players: list[dict[str, Any]],
    assignments: dict[int, str],
    hi_low_state: dict[str, Any],
) -> str | None:
    active_ids = active_hi_low_player_ids(ordered_players, hi_low_state)
    if getattr(game, "team_mode", "solo") == "teams":
        active_teams = {assignments.get(player_id, TEAM_A) for player_id in active_ids}
        if len(active_teams) == 1:
            return next(iter(active_teams))
        return None

    if len(active_ids) == 1:
        return str(active_ids[0])
    return None


def reset_hi_low_leg_state(hi_low_state: dict[str, Any]) -> None:
    start_low = int(hi_low_state.get("start_low", HI_LOW_DEFAULT_LOW))
    start_high = int(hi_low_state.get("start_high", HI_LOW_DEFAULT_HIGH))
    if start_low >= start_high:
        start_low = HI_LOW_DEFAULT_LOW
        start_high = HI_LOW_DEFAULT_HIGH
    hi_low_state["current_low"] = start_low
    hi_low_state["current_high"] = start_high
    hi_low_state["phase"] = "bounds"
    hi_low_state["current_target"] = None
    hi_low_state["eliminated_players"] = []
    hi_low_state["last_success"] = {}


def apply_hi_low_turn(
    game: Any,
    turn: Any,
    ordered_players: list[dict[str, Any]],
    score_row: Any,
    assignments: dict[int, str],
    hi_low_state: dict[str, Any],
) -> None:
    del score_row
    eliminated_ids = set(hi_low_state.get("eliminated_players") or [])
    if turn.player_id in eliminated_ids:
        return

    start_low = int(hi_low_state.get("start_low", HI_LOW_DEFAULT_LOW))
    start_high = int(hi_low_state.get("start_high", HI_LOW_DEFAULT_HIGH))
    current_low = hi_low_state.get("current_low")
    if not isinstance(current_low, int) or not (0 <= current_low <= MAX_TURN_TOTAL):
        current_low = start_low

    current_high = hi_low_state.get("current_high")
    if not isinstance(current_high, int) or not (0 <= current_high <= MAX_TURN_TOTAL):
        current_high = start_high

    if current_low >= current_high:
        current_low = start_low
        current_high = start_high

    score = int(turn.total_points)
    success = False
    if score != 0:
        success = score < current_low or score > current_high

    if success:
        if score < current_low:
            hi_low_state["current_low"] = score
        elif score > current_high:
            hi_low_state["current_high"] = score
        hi_low_state["phase"] = "bounds"
        hi_low_state["current_target"] = None
        hi_low_state.setdefault("last_success", {})[str(turn.player_id)] = score
        turn.counted = True
        turn.fives_awarded = score
        turn.dart_3 = encode_hi_low_turn_result("success")
        return

    eliminated = hi_low_state.setdefault("eliminated_players", [])
    if turn.player_id not in eliminated:
        eliminated.append(turn.player_id)
    turn.counted = False
    turn.fives_awarded = 0
    turn.dart_3 = encode_hi_low_turn_result("eliminated")

    leg_winner = hi_low_leg_winner_entity(game, ordered_players, assignments, hi_low_state)
    if not leg_winner:
        return

    legs_won = hi_low_state.setdefault("legs_won", {})
    previous_legs = legs_won.get(leg_winner, 0)
    legs_won[leg_winner] = previous_legs + 1

    required_legs = required_legs_for_hi_low(
        hi_low_state.get("match_type", "best_of"),
        hi_low_state.get("legs_value", 1),
    )
    hi_low_state["required_legs"] = required_legs

    if legs_won[leg_winner] >= required_legs:
        if getattr(game, "team_mode", "solo") == "teams":
            finish_game(game, winner_team=leg_winner)
        else:
            finish_game(game, winner_player_id=int(leg_winner))
        return

    reset_hi_low_leg_state(hi_low_state)


def halve_it_points_from_entry(round_info: dict[str, Any], entry_value: int) -> tuple[int | None, str | None]:
    kind = round_info.get("kind")
    target = round_info.get("target")

    if kind == "number":
        if entry_value > 9:
            return None, f"Round {round_info['round']} ({target}) expects hit count from 0 to 9."
        number_value = int(round_info.get("number") or 0)
        return entry_value * number_value, None

    if kind == "double":
        if entry_value > 120:
            return None, "Any Double round allows up to 120 points."
        if entry_value != 0 and entry_value % 2 != 0:
            return None, "Any Double round score must be divisible by 2."
        return entry_value, None

    if kind == "triple":
        if entry_value > 180:
            return None, "Any Triple round allows up to 180 points."
        if entry_value != 0 and entry_value % 3 != 0:
            return None, "Any Triple round score must be divisible by 3."
        return entry_value, None

    if kind == "bull":
        # Supports hit-count entry (0-6 marks) and explicit bull points (0-150, step 25).
        if 0 <= entry_value <= 6:
            return entry_value * 25, None
        if entry_value > 150:
            return None, "Bullseye round allows up to 150 points."
        if entry_value % 25 != 0:
            return None, "Bullseye round must be entered as hit count (0-6) or points in steps of 25."
        return entry_value, None

    if kind == "exact_total":
        raw_totals = round_info.get("exact_totals")
        if isinstance(raw_totals, list) and raw_totals:
            allowed_totals = {int(value) for value in raw_totals}
            if entry_value in allowed_totals:
                matched_total = next(total for total in allowed_totals if total == entry_value)
                return matched_total, None
            return 0, None
        exact_total = int(round_info.get("exact_total") or 0)
        if entry_value == exact_total:
            return exact_total, None
        # Non-exact entries are valid attempts that simply miss the target.
        return 0, None

    if kind == "all_darts_hits":
        required_hits = int(round_info.get("required_hits") or 3)
        if entry_value == 0:
            return 0, None
        if entry_value != required_hits:
            return None, f"{target} requires all {required_hits} darts to score."
        fixed_points = int(round_info.get("fixed_points") or 0)
        return fixed_points, None

    if kind == "manual_points":
        if entry_value > 180:
            return None, f"{target} allows up to 180 points."
        return entry_value, None

    return None, "Invalid Halve It round configuration."


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
    turn.dart_2 = 0

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
        legs_won = x01_state.setdefault("legs_won", {})
        previous_legs = legs_won.get(entity_key, 0)
        legs_won[entity_key] = previous_legs + 1
        turn.dart_2 = legs_won[entity_key]

        required_legs = required_legs_for_x01(
            x01_state.get("match_type", "best_of"),
            x01_state.get("legs_value", 1),
        )
        x01_state["required_legs"] = required_legs

        if legs_won[entity_key] >= required_legs:
            if getattr(game, "team_mode", "solo") == "teams":
                finish_game(game, winner_team=entity_key)
            else:
                finish_game(game, winner_player_id=turn.player_id)
            return

        for key in remaining_scores:
            remaining_scores[key] = x01_state["starting_score"]

        if getattr(game, "team_mode", "solo") == "teams":
            for player in ordered_players:
                player_team = assignments.get(player["id"], TEAM_A)
                score_row = score_by_player.get(player["id"])
                if score_row:
                    score_row.fives = remaining_scores.get(player_team, x01_state["starting_score"])
        else:
            for player in ordered_players:
                score_row = score_by_player.get(player["id"])
                if score_row:
                    player_key = str(player["id"])
                    score_row.fives = remaining_scores.get(player_key, x01_state["starting_score"])


def apply_halve_it_turn(
    game: Any,
    turn: Any,
    score_row: Any,
    player_rounds: dict[int, int],
    halve_it_state: dict[str, Any],
) -> None:
    round_number = player_rounds.get(turn.player_id, 0) + 1
    round_info = halve_it_round_info(round_number, halve_it_state)
    scored_points, validation_error = halve_it_points_from_entry(round_info, turn.total_points)
    if validation_error:
        scored_points = 0

    current_total = int(score_row.fives)
    turn.dart_2 = round_number

    if not scored_points:
        halved_total = current_total // 2
        turn.counted = False
        turn.fives_awarded = halved_total - current_total
        turn.dart_3 = 1
        score_row.fives = halved_total
    else:
        turn.counted = True
        turn.fives_awarded = scored_points
        turn.dart_3 = 0
        score_row.fives = current_total + scored_points

    player_rounds[turn.player_id] = min(round_number, int(halve_it_state.get("total_rounds") or HALVE_IT_TOTAL_ROUNDS))


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
    stored_halve_it_state = parse_halve_it_state(getattr(game, "halve_it_state", None))
    if game.game_type == "halve_it" and stored_halve_it_state.get("variant") == "standard":
        initial_score = 20
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
    stored_hi_low_state = parse_hi_low_state(
        getattr(game, "hi_low_state", None),
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
            stored_x01_state.get("match_type", "best_of"),
            stored_x01_state.get("legs_value", 1),
            stored_x01_state.get("starting_entity"),
            stored_x01_state.get("initial_turn_position", 0),
        )
        game.current_turn_position = x01_state.get("initial_turn_position", 0)
    else:
        x01_state = stored_x01_state

    if game.game_type == "hi_low":
        hi_low_state = build_initial_hi_low_state(
            stored_hi_low_state.get("start_low", HI_LOW_DEFAULT_LOW),
            stored_hi_low_state.get("start_high", HI_LOW_DEFAULT_HIGH),
            [player["id"] for player in ordered_players],
            assignments,
            game.team_mode,
            stored_hi_low_state.get("match_type", "best_of"),
            stored_hi_low_state.get("legs_value", 1),
        )
        hi_low_state["required_legs"] = required_legs_for_hi_low(
            hi_low_state.get("match_type", "best_of"),
            hi_low_state.get("legs_value", 1),
        )
        game.current_turn_position = first_active_hi_low_turn_position(ordered_players, hi_low_state)
    else:
        hi_low_state = stored_hi_low_state

    halve_it_state = stored_halve_it_state

    player_rounds = {player["id"]: 0 for player in ordered_players}

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
        elif game.game_type == "halve_it":
            apply_halve_it_turn(game, turn, score_row, player_rounds, halve_it_state)
            if all(
                player_rounds.get(player["id"], 0) >= int(halve_it_state.get("total_rounds") or HALVE_IT_TOTAL_ROUNDS)
                for player in ordered_players
            ):
                best_total = max((int(score_by_player[player["id"]].fives) for player in ordered_players), default=0)
                winners = [
                    player["id"]
                    for player in ordered_players
                    if int(score_by_player[player["id"]].fives) == best_total
                ]
                if len(winners) == 1:
                    finish_game(game, winner_player_id=winners[0])
                else:
                    finish_game(game)
        elif game.game_type == "hi_low":
            apply_hi_low_turn(game, turn, ordered_players, score_row, assignments, hi_low_state)
        else:
            apply_standard_turn(game, turn, score_row, assignments, team_totals)

        if game.status == "active":
            if game.game_type == "hi_low":
                game.current_turn_position = next_active_hi_low_turn_position(
                    game.current_turn_position,
                    ordered_players,
                    hi_low_state,
                )
            else:
                game.current_turn_position = (game.current_turn_position + 1) % len(ordered_players)

    if game.game_type == "english_cricket":
        game.cricket_state = json.dumps(cricket_state)
    if game.game_type == "x01":
        game.x01_state = json.dumps(x01_state)
    if game.game_type == "noughts_and_crosses":
        game.noughts_and_crosses_state = json.dumps(noughts_state)
    if game.game_type == "halve_it":
        game.halve_it_state = json.dumps(halve_it_state)
    if game.game_type == "hi_low":
        game.hi_low_state = json.dumps(hi_low_state)


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
    hi_low_state: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    hi_low_eliminated = set((hi_low_state or {}).get("eliminated_players") or [])
    hi_low_last_success = (hi_low_state or {}).get("last_success") or {}
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
            "hi_low_eliminated": (item["id"] in hi_low_eliminated) if game.game_type == "hi_low" else None,
            "hi_low_last_success": (
                hi_low_last_success.get(str(item["id"]))
                if game.game_type == "hi_low"
                else None
            ),
        }
        for item in ordered_players
    ]


def serialize_turns_for_game(turn_rows: list[tuple[Any, Any]], game: Any) -> list[dict[str, Any]]:
    noughts_state = parse_noughts_and_crosses_state(game.noughts_and_crosses_state) if game.game_type == "noughts_and_crosses" else {}
    halve_it_state = parse_halve_it_state(getattr(game, "halve_it_state", None)) if game.game_type == "halve_it" else None
    return [
        {
            "turn_number": turn.turn_number,
            "player_id": turn.player_id,
            "player_name": player.name,
            "total_points": turn.total_points,
            "counted": turn.counted,
            "fives_awarded": turn.fives_awarded,
            "x01_result": decode_x01_turn_result(turn.dart_3) if game.game_type == "x01" else None,
            "x01_leg_won": bool(turn.dart_2) if game.game_type == "x01" else None,
            "x01_leg_number": int(turn.dart_2) if game.game_type == "x01" and turn.dart_2 else None,
            "halve_it_round": int(turn.dart_2) if game.game_type == "halve_it" and turn.dart_2 else None,
            "halve_it_halved": bool(turn.dart_3) if game.game_type == "halve_it" else None,
            "halve_it_target": (
                halve_it_round_info(int(turn.dart_2), halve_it_state)["target"]
                if game.game_type == "halve_it" and turn.dart_2
                else None
            ),
            "noughts_marker": decode_noughts_marker(turn.dart_2) if game.game_type == "noughts_and_crosses" else None,
            "hi_low_result": decode_hi_low_turn_result(turn.dart_3) if game.game_type == "hi_low" else None,
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
    halve_it_base_state = parse_halve_it_state(getattr(game, "halve_it_state", None))
    hi_low_state = parse_hi_low_state(
        getattr(game, "hi_low_state", None),
        [player["id"] for player in ordered_players],
        assignments,
        game.team_mode,
    )

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

    halve_it_state = None
    if game.game_type == "halve_it":
        player_rounds = {player["id"]: 0 for player in ordered_players}
        for turn, _ in turn_rows:
            if turn.player_id in player_rounds and player_rounds[turn.player_id] < int(halve_it_base_state.get("total_rounds") or HALVE_IT_TOTAL_ROUNDS):
                player_rounds[turn.player_id] += 1

        active_round = 1
        if active_player_id is not None and active_player_id in player_rounds:
            active_round = min(
                player_rounds[active_player_id] + 1,
                int(halve_it_base_state.get("total_rounds") or HALVE_IT_TOTAL_ROUNDS),
            )

        round_info = halve_it_round_info(active_round, halve_it_base_state)
        halve_it_state = {
            "variant": halve_it_base_state.get("variant", "standard"),
            "total_rounds": int(halve_it_base_state.get("total_rounds") or HALVE_IT_TOTAL_ROUNDS),
            "current_round": active_round,
            "current_target": round_info["target"],
            "current_entry_mode": round_info["entry_mode"],
            "player_rounds": {str(player_id): rounds for player_id, rounds in player_rounds.items()},
            "rounds": [
                halve_it_round_info(index, halve_it_base_state)
                for index in range(1, int(halve_it_base_state.get("total_rounds") or HALVE_IT_TOTAL_ROUNDS) + 1)
            ],
        }

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
        "hi_low_state": hi_low_state if game.game_type == "hi_low" else None,
        "halve_it_state": halve_it_state,
        "noughts_and_crosses_state": noughts_state if game.game_type == "noughts_and_crosses" else None,
        "players": serialize_players_for_game(ordered_players, scores, assignments, game, x01_state, hi_low_state),
        "turns": serialize_turns_for_game(turn_rows, game),
    }


def game_type_label(game_type: str | None) -> str:
    normalized = normalize_game_type(game_type)
    if normalized == "english_cricket":
        return "English Cricket"
    if normalized == "x01":
        return "X01"
    if normalized == "hi_low":
        return "Hi/Low"
    if normalized == "halve_it":
        return "Halve It"
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

    if game_type == "halve_it" and team_mode == "teams":
        return None, "Halve It does not support teams. Choose Singles mode."

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
    x01_match_type: str = "best_of",
    x01_legs_value: int = 1,
    x01_starting_entity: str | None = None,
    halve_it_variant: str = "standard",
    hi_low_start_low: int = HI_LOW_DEFAULT_LOW,
    hi_low_start_high: int = HI_LOW_DEFAULT_HIGH,
    hi_low_match_type: str = "best_of",
    hi_low_legs_value: int = 1,
) -> tuple[int, str | None, str | None, str | None, str | None, str | None]:
    if game_type == "english_cricket":
        opening_state = build_initial_cricket_state(starting_batting_team)
        ordered_for_start = [{"id": player_id} for player_id in ordered_player_ids]
        initial_turn_position = starting_turn_position(
            ordered_for_start,
            normalized_assignments,
            opening_state["bowling_team"],
        )
        return initial_turn_position, json.dumps(opening_state), None, None, None, None

    if game_type == "x01":
        initial_turn_position = x01_starting_turn_position(
            ordered_player_ids,
            normalized_assignments,
            team_mode,
            normalize_x01_starting_entity(
                x01_starting_entity,
                team_mode,
                ordered_player_ids,
                normalized_assignments,
                default=(str(ordered_player_ids[0]) if ordered_player_ids else "random"),
            ),
        )
        x01_state = build_initial_x01_state(
            ordered_player_ids,
            normalized_assignments,
            team_mode,
            x01_starting_score,
            x01_match_type,
            x01_legs_value,
            x01_starting_entity,
            initial_turn_position,
        )
        return initial_turn_position, None, None, json.dumps(x01_state), None, None

    if game_type == "noughts_and_crosses":
        return 0, None, json.dumps(build_initial_noughts_and_crosses_state()), None, None, None

    if game_type == "halve_it":
        return 0, None, None, None, json.dumps(build_initial_halve_it_state(halve_it_variant)), None

    if game_type == "hi_low":
        hi_low_state = build_initial_hi_low_state(
            hi_low_start_low,
            hi_low_start_high,
            ordered_player_ids,
            normalized_assignments,
            team_mode,
            hi_low_match_type,
            hi_low_legs_value,
        )
        return 0, None, None, None, None, json.dumps(hi_low_state)

    return 0, None, None, None, None, None