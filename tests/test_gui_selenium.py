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
    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-55by5"))).click()
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
    browser.find_element(By.ID, "start-game").click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    _wait(browser).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "#active-game-meta .current-player")))


def start_cricket_game(browser, first_player: str, second_player: str):
    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-english-cricket"))).click()
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

    browser.find_element(By.ID, "start-game").click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-dashboard")))


def test_start_game_shows_live_view(live_server, browser):
    browser.get(live_server)
    start_single_player_game(browser, "Alice")

    current_player = browser.find_element(By.CSS_SELECTOR, "#active-game-meta .current-player").text.strip()
    assert current_player == "Alice to Throw"
    assert browser.find_element(By.ID, "live-panel").is_displayed()
    assert "275" in browser.find_element(By.ID, "scoreboard").text


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
    assert batting_input.is_enabled()

    batting_input.clear()
    batting_input.send_keys("60")
    browser.find_element(By.ID, "cricket-submit-batting").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Jules to Throw"))
    updated_bowling_panel = browser.find_element(By.ID, "cricket-bowling-panel")
    assert "is-active" in updated_bowling_panel.get_attribute("class")


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

    turn_total = browser.find_element(By.ID, "turn-total")

    # Build to 54 fives with divisible-by-3 scores: 3x75 (45) + 3x15 (9)
    for _ in range(3):
        turn_total.clear()
        turn_total.send_keys("75")
        browser.find_element(By.ID, "submit-turn").click()

    for _ in range(3):
        turn_total.clear()
        turn_total.send_keys("15")
        browser.find_element(By.ID, "submit-turn").click()

    # 15 would push 54 -> 57, so this is a bust.
    turn_total.clear()
    turn_total.send_keys("15")
    browser.find_element(By.ID, "submit-turn").click()

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