import importlib
import socket
import sys
import tempfile
import threading
import time
from urllib.request import urlopen

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.serving import make_server


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_http_ready(base_url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(base_url, timeout=1):  # noqa: S310
                return
        except Exception:
            time.sleep(0.15)
    raise RuntimeError(f"Timed out waiting for server at {base_url}")


@pytest.fixture()
def live_server(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="darts-selenium-") as db_dir:
        db_path = f"{db_dir}/selenium.db"

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

        port = free_port()
        server = make_server("127.0.0.1", port, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        base_url = f"http://127.0.0.1:{port}"
        wait_http_ready(base_url)
        yield base_url

        server.shutdown()
        thread.join(timeout=3)


def _build_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)


def _build_firefox_driver():
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    return webdriver.Firefox(options=options)


@pytest.fixture()
def browser():
    driver = None
    builders = (_build_chrome_driver, _build_firefox_driver)
    for build in builders:
        try:
            driver = build()
            break
        except WebDriverException:
            continue

    if driver is None:
        pytest.skip("No compatible WebDriver/browser found for Selenium GUI tests.")

    try:
        yield driver
    finally:
        driver.quit()


def _wait(browser, timeout=8):
    return WebDriverWait(browser, timeout)


def add_player(browser, name: str):
    name_input = _wait(browser).until(ec.presence_of_element_located((By.ID, "player-name")))
    name_input.clear()
    name_input.send_keys(name)
    browser.find_element(By.CSS_SELECTOR, "#player-form button[type='submit']").click()
    _wait(browser).until(
        ec.text_to_be_present_in_element((By.ID, "players-list"), name)
    )


def start_single_player_game(browser, player_name: str):
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))
    add_player(browser, player_name)
    player_checkbox = _wait(browser).until(
        ec.presence_of_element_located(
            (
                By.XPATH,
                f"//div[@id='selectable-players']//label[.//span[normalize-space()='{player_name}']]//input",
            )
        )
    )
    if not player_checkbox.is_selected():
        player_checkbox.click()
    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-55by5"))).click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    _wait(browser).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "#active-game-meta .current-player")))


def start_cricket_game(browser, first_player: str, second_player: str, starting_batting_team=None):
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))

    for player_name in (first_player, second_player):
        add_player(browser, player_name)
        player_checkbox = _wait(browser).until(
            ec.presence_of_element_located(
                (
                    By.XPATH,
                    f"//div[@id='selectable-players']//label[.//span[normalize-space()='{player_name}']]//input",
                )
            )
        )
        if not player_checkbox.is_selected():
            player_checkbox.click()

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-english-cricket"))).click()
    popup = _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-start-overlay")))

    if starting_batting_team == "team_b":
        role_radio = popup.find_element(By.CSS_SELECTOR, "input[name='cricket-start-choice'][value='bowl']")
        if not role_radio.is_selected():
            role_radio.click()

    browser.find_element(By.ID, "cricket-start-game").click()
    _wait(browser).until(ec.invisibility_of_element_located((By.ID, "cricket-start-overlay")))
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-dashboard")))


def test_start_game_shows_live_view(live_server, browser):
    browser.get(live_server)
    start_single_player_game(browser, "Alice")

    current_player = browser.find_element(By.CSS_SELECTOR, "#active-game-meta .current-player").text.strip()
    assert current_player == "Alice to Throw"
    assert browser.find_element(By.ID, "live-panel").is_displayed()
    assert "275" in browser.find_element(By.ID, "scoreboard").text


def test_team_assignment_can_be_configured_before_choosing_game(live_server, browser):
    browser.get(live_server)

    for player_name in ("Alpha", "Bravo"):
        add_player(browser, player_name)
        player_checkbox = _wait(browser).until(
            ec.presence_of_element_located(
                (
                    By.XPATH,
                    f"//div[@id='selectable-players']//label[.//span[normalize-space()='{player_name}']]//input",
                )
            )
        )
        if not player_checkbox.is_selected():
            player_checkbox.click()

    team_mode = _wait(browser).until(ec.element_to_be_clickable((By.ID, "team-mode-teams")))
    if not team_mode.is_selected():
        team_mode.click()

    team_assignment = _wait(browser).until(ec.visibility_of_element_located((By.ID, "team-assignment")))
    assert "Team A" in team_assignment.text
    assert "Team B" in team_assignment.text


def test_start_without_players_shows_bust_style_error(live_server, browser):
    browser.get(live_server)

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-55by5"))).click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "bust-banner"), "Select at least one player."))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "bust-banner").get_attribute("class"))
    assert not browser.find_element(By.ID, "live-panel").is_displayed()



def test_non_admin_user_does_not_see_clear_history_button(live_server, browser):
    browser.get(live_server)

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "clear-history")))

    browser.find_element(By.ID, "new-username").send_keys("viewer")
    browser.find_element(By.ID, "new-password").send_keys("viewerpass")
    browser.find_element(By.CSS_SELECTOR, "#create-user-form button[type='submit']").click()
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "user-accounts-list"), "viewer"))

    browser.find_element(By.CSS_SELECTOR, ".logout-form button[type='submit']").click()
    _wait(browser).until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".login-form")))

    browser.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys("viewer")
    browser.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("viewerpass")
    browser.find_element(By.CSS_SELECTOR, ".login-form button[type='submit']").click()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "players-panel")))
    clear_history_button = browser.find_element(By.ID, "clear-history")
    assert not clear_history_button.is_displayed()
    assert "hidden" in clear_history_button.get_attribute("class")


def test_55_by_5_individual_game_can_complete_end_to_end(live_server, browser):
    browser.get(live_server)
    start_single_player_game(browser, "Finn")

    turn_values = (75, 75, 75, 50)
    for turn_number, value in enumerate(turn_values, start=1):
        turn_total = browser.find_element(By.ID, "turn-total")
        turn_total.clear()
        turn_total.send_keys(str(value))
        browser.find_element(By.ID, "submit-turn").click()
        if turn_number < len(turn_values):
            _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), f"#{turn_number} Finn: total {value}"))

    winner_overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert winner_overlay.is_displayed()
    assert browser.find_element(By.ID, "winner-name").text.strip() == "Finn"
    assert "Winner Finn" in browser.find_element(By.ID, "history-list").text



def test_55_by_5_team_game_can_complete_end_to_end(live_server, browser):
    browser.get(live_server)

    for player_name in ("Aria", "Bryn"):
        add_player(browser, player_name)
        player_checkbox = _wait(browser).until(
            ec.presence_of_element_located(
                (
                    By.XPATH,
                    f"//div[@id='selectable-players']//label[.//span[normalize-space()='{player_name}']]//input",
                )
            )
        )
        if not player_checkbox.is_selected():
            player_checkbox.click()

    team_mode = _wait(browser).until(ec.element_to_be_clickable((By.ID, "team-mode-teams")))
    if not team_mode.is_selected():
        team_mode.click()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "team-assignment")))
    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-55by5"))).click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))

    scripted_turns = [
        ("Aria", 75),
        ("Bryn", 0),
        ("Aria", 75),
        ("Bryn", 0),
        ("Aria", 75),
        ("Bryn", 0),
        ("Aria", 50),
    ]

    for turn_number, (player_name, value) in enumerate(scripted_turns, start=1):
        _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), f"{player_name} to Throw"))
        turn_total = browser.find_element(By.ID, "turn-total")
        turn_total.clear()
        turn_total.send_keys(str(value))
        browser.find_element(By.ID, "submit-turn").click()
        if turn_number < len(scripted_turns):
            _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), f"#{turn_number} {player_name}: total {value}"))

    winner_overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert winner_overlay.is_displayed()
    assert browser.find_element(By.ID, "winner-name").text.strip() == "Team A"
    assert "Winner Team A" in browser.find_element(By.ID, "history-list").text


def test_english_cricket_shows_starting_roles_popup_before_game_start(live_server, browser):
    browser.get(live_server)

    for player_name in ("Ivy", "Jules"):
        add_player(browser, player_name)
        player_checkbox = _wait(browser).until(
            ec.presence_of_element_located(
                (
                    By.XPATH,
                    f"//div[@id='selectable-players']//label[.//span[normalize-space()='{player_name}']]//input",
                )
            )
        )
        if not player_checkbox.is_selected():
            player_checkbox.click()

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-english-cricket"))).click()
    popup = _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-start-overlay")))

    assert "will" in popup.text.lower()
    assert len(browser.find_elements(By.NAME, "cricket-start-choice")) == 2
    assert browser.find_element(By.ID, "cricket-start-game").is_displayed()


def test_english_cricket_rejects_more_than_two_individual_players(live_server, browser):
    browser.get(live_server)

    for player_name in ("Ivy", "Jules", "Kai"):
        add_player(browser, player_name)
        player_checkbox = _wait(browser).until(
            ec.presence_of_element_located(
                (
                    By.XPATH,
                    f"//div[@id='selectable-players']//label[.//span[normalize-space()='{player_name}']]//input",
                )
            )
        )
        if not player_checkbox.is_selected():
            player_checkbox.click()

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-english-cricket"))).click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "bust-banner"), "Select exactly two players before starting English Cricket."))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "bust-banner").get_attribute("class"))
    assert not browser.find_element(By.ID, "cricket-start-overlay").is_displayed()


def test_submit_turn_updates_score_and_clears_input(live_server, browser):
    browser.get(live_server)
    start_single_player_game(browser, "Bob")

    turn_total = browser.find_element(By.ID, "turn-total")
    turn_total.clear()
    turn_total.send_keys("15")
    browser.find_element(By.ID, "submit-turn").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "scoreboard"), "3"))
    _wait(browser).until(lambda d: d.find_element(By.ID, "turn-total").get_attribute("value") == "")

    scoreboard_text = browser.find_element(By.ID, "scoreboard").text
    assert "Bob" in scoreboard_text
    assert "3" in scoreboard_text
    assert "260" in scoreboard_text


def test_english_cricket_live_view_uses_two_panels(live_server, browser):
    browser.get(live_server)
    start_cricket_game(browser, "Ivy", "Jules")

    bowling_panel = _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-bowling-panel")))
    batting_panel = browser.find_element(By.ID, "cricket-batting-panel")
    batting_input = browser.find_element(By.ID, "cricket-batting-total")

    assert "bowling side" in bowling_panel.text.lower()
    assert "batting side" in batting_panel.text.lower()
    assert len(browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip")) == 10
    assert not batting_input.is_enabled()
    assert "Jules to Throw" in browser.find_element(By.ID, "active-game-meta").text

    bull_buttons = browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled])")
    assert len(bull_buttons) == 10
    for index in (0, 2, 4, 6, 8, 9):
        browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled])")[index].click()

    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip.is-selected")) == 6)
    browser.find_element(By.ID, "cricket-submit-bowling").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Ivy to Throw"))
    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip.is-hit")) == 6)
    batting_input = _wait(browser).until(ec.element_to_be_clickable((By.ID, "cricket-batting-total")))
    batting_input.clear()
    batting_input.send_keys("60")
    browser.find_element(By.ID, "cricket-submit-batting").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Jules to Throw"))
    updated_bowling_panel = browser.find_element(By.ID, "cricket-bowling-panel")
    assert "is-active" in updated_bowling_panel.get_attribute("class")


def test_english_cricket_shows_target_and_remaining_runs_in_second_innings(live_server, browser):
    browser.get(live_server)
    start_cricket_game(browser, "Ivy", "Jules")

    for index in (0, 2, 4, 6, 8, 9):
        browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled])")[index].click()
    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip.is-selected")) == 6)
    browser.find_element(By.ID, "cricket-submit-bowling").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Ivy to Throw"))
    batting_input = _wait(browser).until(ec.element_to_be_clickable((By.ID, "cricket-batting-total")))
    batting_input.clear()
    batting_input.send_keys("60")
    browser.find_element(By.ID, "cricket-submit-batting").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Jules to Throw"))
    for _ in range(4):
        browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled]):not(.is-selected)")[0].click()
    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip.is-selected")) == 4)
    browser.find_element(By.ID, "cricket-submit-bowling").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "cricket-batting-panel"), "Jules"))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "cricket-batting-panel"), "TARGET"))
    batting_panel = browser.find_element(By.ID, "cricket-batting-panel")
    panel_text = batting_panel.text.lower()
    assert "target" in panel_text
    assert "remaining runs" in panel_text
    assert "21" in panel_text


def test_english_cricket_shows_message_only_when_more_than_six_marks_selected(live_server, browser):
    browser.get(live_server)
    start_cricket_game(browser, "Kai", "Lena")

    bull_buttons = browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled])")
    assert len(bull_buttons) == 10
    assert "at most 6 wicket marks" not in browser.find_element(By.ID, "message").text

    for index in range(7):
        browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled])")[index].click()

    assert "at most 6 wicket marks" not in browser.find_element(By.ID, "message").text
    browser.find_element(By.ID, "cricket-submit-bowling").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "at most 6 wicket marks"))
    assert "Lena to Throw" in browser.find_element(By.ID, "active-game-meta").text


def test_quit_requires_confirmation(live_server, browser):
    browser.get(live_server)
    start_single_player_game(browser, "Charlie")

    browser.execute_script("window.confirm = function () { return false; };")
    browser.find_element(By.ID, "quit-game").click()

    _wait(browser).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "#active-game-meta .current-player")))
    assert browser.find_element(By.ID, "live-panel").is_displayed()

    browser.execute_script("window.confirm = function () { return true; };")
    browser.find_element(By.ID, "quit-game").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Game quit."))
    _wait(browser).until(lambda d: not d.find_element(By.ID, "live-panel").is_displayed())
    assert browser.find_element(By.ID, "players-panel").is_displayed()


def test_bust_shows_red_banner_for_three_seconds(live_server, browser):
    browser.get(live_server)
    start_single_player_game(browser, "Dana")

    turn_values = [75, 75, 75, 15, 15, 15, 15]

    for turn_number, value in enumerate(turn_values, start=1):
        turn_total = browser.find_element(By.ID, "turn-total")
        turn_total.clear()
        turn_total.send_keys(str(value))
        browser.find_element(By.ID, "submit-turn").click()
        _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), f"#{turn_number} Dana: total {value}"))

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "bust-banner"), "Dana bust!"))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "bust-banner").get_attribute("class"))
    WebDriverWait(browser, 5).until(
        lambda d: "visible" not in d.find_element(By.ID, "bust-banner").get_attribute("class")
    )


def test_non_divisible_by_five_shows_popup_and_keeps_total(live_server, browser):
    browser.get(live_server)
    start_single_player_game(browser, "Eve")

    turn_total = browser.find_element(By.ID, "turn-total")
    turn_total.clear()
    turn_total.send_keys("12")
    browser.find_element(By.ID, "submit-turn").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "score-warning-banner"), "Total scored must be divisible by 5."))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "score-warning-banner").get_attribute("class"))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "total 12 (+0 fives)"))

    scoreboard_text = browser.find_element(By.ID, "scoreboard").text
    assert "Eve" in scoreboard_text
    assert "0" in scoreboard_text