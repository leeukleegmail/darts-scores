import importlib
import socket
import sys
import tempfile
import threading
import time
from contextlib import suppress
from urllib.request import urlopen

import pytest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait
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
        _safe_quit_driver(driver)


def _safe_quit_driver(driver) -> None:
    if driver is None:
        return

    # Close extra windows first; this helps prevent quit() hangs in CI/headless runs.
    with suppress(Exception):
        for handle in list(driver.window_handles):
            with suppress(Exception):
                driver.switch_to.window(handle)
                driver.close()

    for _ in range(3):
        try:
            driver.quit()
            break
        except Exception:
            time.sleep(0.2)

    service = getattr(driver, "service", None)
    if service is None:
        return

    with suppress(Exception):
        service.stop()

    process = getattr(service, "process", None)
    if process is None:
        return

    with suppress(Exception):
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=2)

    with suppress(Exception):
        if process.poll() is None:
            process.kill()


def _wait(browser, timeout=8):
    return WebDriverWait(browser, timeout)


def open_player_manager(browser):
    trigger = _wait(browser).until(ec.element_to_be_clickable((By.ID, "player-manager-open")))
    trigger.click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "player-manager-overlay")))


def close_player_manager(browser):
    close_button = _wait(browser).until(ec.element_to_be_clickable((By.ID, "player-manager-close")))
    close_button.click()
    _wait(browser).until(ec.invisibility_of_element_located((By.ID, "player-manager-overlay")))


def add_player(browser, name: str):
    open_player_manager(browser)
    name_input = _wait(browser).until(ec.presence_of_element_located((By.ID, "player-name")))
    name_input.clear()
    name_input.send_keys(name)
    browser.find_element(By.CSS_SELECTOR, "#player-form button[type='submit']").click()
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "players-list"), name))
    close_player_manager(browser)


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


def start_noughts_game(browser, first_player: str, second_player: str):
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

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-noughts-and-crosses"))).click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-dashboard")))


def start_shanghai_game(browser, player_names, team_mode="solo"):
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))

    for player_name in player_names:
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

    if team_mode == "teams":
        team_mode_toggle = _wait(browser).until(ec.element_to_be_clickable((By.ID, "team-mode-teams")))
        if not team_mode_toggle.is_selected():
            team_mode_toggle.click()

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-shanghai"))).click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    _wait(browser).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "#active-game-meta .current-player")))


def start_x01_game(
    browser,
    player_names,
    starting_score="501",
    team_mode="solo",
    match_type="best_of",
    legs_value=1,
    starting_entity=None,
):
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))

    for player_name in player_names:
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

    if team_mode == "teams":
        team_mode_toggle = _wait(browser).until(ec.element_to_be_clickable((By.ID, "team-mode-teams")))
        if not team_mode_toggle.is_selected():
            team_mode_toggle.click()
        _wait(browser).until(ec.visibility_of_element_located((By.ID, "team-assignment")))
        _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#team-a-list li")) > 0)
        _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#team-b-list li")) > 0)

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-x01"))).click()
    popup = _wait(browser).until(ec.visibility_of_element_located((By.ID, "x01-start-overlay")))

    popup.find_element(By.CSS_SELECTOR, f"input[name='x01-starting-score'][value='{starting_score}']").click()

    Select(popup.find_element(By.ID, "x01-match-type")).select_by_value(match_type)

    slider = popup.find_element(By.ID, "x01-legs-value")
    browser.execute_script(
        """
        const slider = arguments[0];
        const value = String(arguments[1]);
        slider.value = value;
        slider.dispatchEvent(new Event('input', { bubbles: true }));
        slider.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        slider,
        int(legs_value),
    )

    if starting_entity is not None:
        selector = Select(popup.find_element(By.ID, "x01-starting-entity"))
        selector.select_by_value(str(starting_entity))

    browser.find_element(By.ID, "x01-start-game").click()
    _wait(browser).until(ec.invisibility_of_element_located((By.ID, "x01-start-overlay")))
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))


def start_noughts_team_game(browser, team_a_players: list, team_b_players: list):
    """Start a Noughts and Crosses game in teams mode.

    Players are added in the order team_a_players + team_b_players.
    syncTeamAssignments() auto-balances them alternately into Team A / Team B,
    so the calling convention determines which players end up on which team:
      add order [a0, a1, b0, b1] -> Team A: a0, b0; Team B: a1, b1
    We let the auto-balance handle placement rather than using the swap UI,
    which avoids relying on fragile drag/swap interaction details.
    """
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))

    all_players = team_a_players + team_b_players
    for player_name in all_players:
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
    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#team-a-list li")) > 0)
    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#team-b-list li")) > 0)

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-noughts-and-crosses"))).click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-dashboard")))


def noughts_click_cell(browser, cell_index: int, mark: str) -> None:
    """Click a Noughts board cell and confirm the mark in the overlay."""
    board = _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-dashboard")))
    cell = board.find_element(By.CSS_SELECTOR, f"[data-board-index='{cell_index}']")
    cell.click()
    chooser = _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-mark-overlay")))
    chooser.find_element(By.CSS_SELECTOR, f"[data-noughts-mark='{mark}']").click()
    _wait(browser).until(
        lambda d: d.find_elements(By.CSS_SELECTOR, f"[data-board-index='{cell_index}'].is-marked")
    )


def submit_standard_score_with_keypad(browser, value: int):
    keypad = _wait(browser).until(ec.visibility_of_element_located((By.ID, "standard-score-keypad")))
    display = browser.find_element(By.ID, "turn-total")

    existing_value = display.get_attribute("value") or ""
    for _ in existing_value:
        keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='backspace']").click()

    for digit in str(value):
        keypad.find_element(By.CSS_SELECTOR, f"[data-keypad-value='{digit}']").click()

    keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='submit']").click()


def submit_cricket_score_with_keypad(browser, value: int):
    keypad = _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-batting-keypad")))
    display = browser.find_element(By.ID, "cricket-batting-total")

    existing_value = display.get_attribute("value") or ""
    for _ in existing_value:
        keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='backspace']").click()

    for digit in str(value):
        keypad.find_element(By.CSS_SELECTOR, f"[data-keypad-value='{digit}']").click()

    keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='submit']").click()


def enter_value_with_keypad(browser, keypad_id: str, display_id: str, value: int):
    keypad = _wait(browser).until(ec.visibility_of_element_located((By.ID, keypad_id)))
    display = browser.find_element(By.ID, display_id)

    existing_value = display.get_attribute("value") or ""
    for _ in existing_value:
        keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='backspace']").click()

    for digit in str(value):
        keypad.find_element(By.CSS_SELECTOR, f"[data-keypad-value='{digit}']").click()

    return keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='submit']")
