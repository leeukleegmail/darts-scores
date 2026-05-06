import sys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait
from tests.selenium_helpers import (
    _wait,
    add_player,
    browser,
    close_player_manager,
    enter_value_with_keypad,
    live_server,
    noughts_click_cell,
    open_player_manager,
    start_cricket_game,
    start_noughts_game,
    start_noughts_team_game,
    start_single_player_game,
    start_x01_game,
    submit_cricket_score_with_keypad,
    submit_standard_score_with_keypad,
)


def test_start_game_shows_live_view(live_server, browser):
    """Starting a 55 by 5 game switches the UI into the live game view."""
    browser.get(live_server)
    start_single_player_game(browser, "Alice")

    current_player = browser.find_element(By.CSS_SELECTOR, "#active-game-meta .current-player").text.strip()
    assert current_player == "Alice to Throw"
    assert browser.find_element(By.ID, "live-panel").is_displayed()
    assert "275" in browser.find_element(By.ID, "scoreboard").text


def test_active_game_hides_select_game_panel_and_change_game_button(live_server, browser):
    """An active game hides the setup game picker and change-game control."""
    browser.get(live_server)
    start_single_player_game(browser, "Owen")

    assert browser.find_elements(By.ID, "change-game") == []
    assert not browser.find_element(By.ID, "game-selection-panel").is_displayed()


def test_55_by_5_onscreen_keypad_can_submit_a_score(live_server, browser):
    """The 55 by 5 keypad can enter, edit, and submit a turn total."""
    browser.get(live_server)
    start_single_player_game(browser, "Piper")

    turn_total = browser.find_element(By.ID, "turn-total")
    assert turn_total.get_attribute("readonly") is not None

    keypad = _wait(browser).until(ec.visibility_of_element_located((By.ID, "standard-score-keypad")))
    keypad.find_element(By.CSS_SELECTOR, "[data-keypad-value='7']").click()
    keypad.find_element(By.CSS_SELECTOR, "[data-keypad-value='8']").click()
    keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='backspace']").click()
    keypad.find_element(By.CSS_SELECTOR, "[data-keypad-value='5']").click()
    keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='submit']").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Piper: total 75"))
    assert "15" in browser.find_element(By.ID, "scoreboard").text


def test_standard_keypad_disables_submit_when_score_exceeds_180(live_server, browser):
    """The standard keypad disables submit for totals above the 180 limit."""
    browser.get(live_server)
    start_single_player_game(browser, "Piper")

    submit_button = enter_value_with_keypad(browser, "standard-score-keypad", "turn-total", 181)
    assert submit_button.get_attribute("disabled") is not None

    # Bring value back within limit and verify submission is re-enabled.
    submit_button = enter_value_with_keypad(browser, "standard-score-keypad", "turn-total", 180)
    assert submit_button.get_attribute("disabled") is None

    submit_button.click()
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Piper: total 180"))


def test_english_cricket_batting_panel_shows_onscreen_keypad(live_server, browser):
    """English Cricket batting uses the read-only on-screen keypad flow."""
    browser.get(live_server)
    start_cricket_game(browser, "Ivy", "Jules")

    batting_panel = _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-batting-panel")))
    keypad = batting_panel.find_element(By.CSS_SELECTOR, ".score-keypad")
    batting_input = batting_panel.find_element(By.ID, "cricket-batting-total")

    assert keypad.is_displayed()
    assert keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='submit']").text.strip() == "Submit Score"
    assert keypad.find_element(By.CSS_SELECTOR, "[data-keypad-action='no-score']").text.strip() == "No Score"
    assert batting_input.get_attribute("readonly") is not None
    assert batting_input.get_attribute("inputmode") == "none"


def test_cricket_batting_keypad_disables_submit_when_score_exceeds_180(live_server, browser):
    """The Cricket batting keypad enforces the same 180 maximum score cap."""
    browser.get(live_server)
    start_cricket_game(browser, "Ivy", "Jules")

    # Cricket opens on a bowling turn; submit one bowling turn so batting becomes active.
    bowling_submit = _wait(browser).until(ec.element_to_be_clickable((By.ID, "cricket-submit-bowling")))
    bowling_submit.click()

    def batting_submit_enabled(driver):
        try:
            button = driver.find_element(By.CSS_SELECTOR, "#cricket-batting-keypad [data-keypad-action='submit']")
            return button.get_attribute("disabled") is None
        except (NoSuchElementException, StaleElementReferenceException):
            return False

    _wait(browser).until(batting_submit_enabled)

    submit_button = enter_value_with_keypad(browser, "cricket-batting-keypad", "cricket-batting-total", 181)
    assert submit_button.get_attribute("disabled") is not None

    submit_button = enter_value_with_keypad(browser, "cricket-batting-keypad", "cricket-batting-total", 180)
    assert submit_button.get_attribute("disabled") is None


def test_noughts_and_crosses_board_allows_marking_x_and_o(live_server, browser):
    """The Noughts board allows players to mark cells with either X or O."""
    browser.get(live_server)
    start_noughts_game(browser, "Nina", "Otis")

    board = _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-dashboard")))
    squares = board.find_elements(By.CSS_SELECTOR, "[data-board-index]")
    assert len(squares) == 9
    assert "Bullseye" in squares[4].text

    squares[0].click()
    chooser = _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-mark-overlay")))
    chooser.find_element(By.CSS_SELECTOR, "[data-noughts-mark='X']").click()
    _wait(browser).until(lambda d: "X" in d.find_elements(By.CSS_SELECTOR, "[data-board-index]")[0].text)

    squares = board.find_elements(By.CSS_SELECTOR, "[data-board-index]")
    squares[1].click()
    chooser = _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-mark-overlay")))
    chooser.find_element(By.CSS_SELECTOR, "[data-noughts-mark='O']").click()
    _wait(browser).until(lambda d: "O" in d.find_elements(By.CSS_SELECTOR, "[data-board-index]")[1].text)


def test_logout_during_active_game_prompts_for_confirmation(live_server, browser):
    """Logging out mid-game prompts before abandoning the active match."""
    browser.get(live_server)
    start_single_player_game(browser, "Nora")

    browser.find_element(By.CSS_SELECTOR, ".logout-form button[type='submit']").click()
    alert = _wait(browser).until(ec.alert_is_present())

    assert "quit the current game" in alert.text.lower()

    alert.dismiss()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    assert "Nora to Throw" in browser.find_element(By.ID, "active-game-meta").text


def test_help_button_opens_user_manual_in_header(live_server, browser):
    """The header help button opens the manual and supports section navigation."""
    browser.get(live_server)

    help_button = _wait(browser).until(ec.element_to_be_clickable((By.ID, "help-button")))
    help_button.click()

    manual = _wait(browser).until(ec.visibility_of_element_located((By.ID, "help-overlay")))
    assert "User Manual" in manual.text
    assert "Quick Start" in manual.text

    browser.find_element(By.CSS_SELECTOR, "#help-nav [data-help-section='cricket']").click()
    _wait(browser).until(
        lambda d: "active" in d.find_element(By.CSS_SELECTOR, ".help-section[data-help-section='cricket']").get_attribute("class")
    )
    assert "Starting Roles" in browser.find_element(By.CSS_SELECTOR, ".help-section[data-help-section='cricket']").text


def test_team_assignment_can_be_configured_before_choosing_game(live_server, browser):
    """Team mode exposes team assignment inputs before a game type is selected."""
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

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "team-assignment")))
    assert browser.find_element(By.ID, "team-a-name").get_attribute("value") == "Team A"
    assert browser.find_element(By.ID, "team-b-name").get_attribute("value") == "Team B"


def test_team_assignment_can_rename_teams(live_server, browser):
    """Custom team names persist through start, quit, and return to setup."""
    browser.get(live_server)

    for player_name in ("Rhea", "Skye"):
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
    team_a_name = browser.find_element(By.ID, "team-a-name")
    team_b_name = browser.find_element(By.ID, "team-b-name")
    team_a_name.clear()
    team_a_name.send_keys("Red Arrows")
    team_b_name.clear()
    team_b_name.send_keys("Blue Rockets")

    browser.find_element(By.ID, "choose-english-cricket").click()
    popup = _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-start-overlay")))

    assert "Red Arrows Will" in popup.text

    browser.find_element(By.ID, "cricket-start-game").click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    browser.execute_script("window.confirm = function () { return true; };")
    browser.find_element(By.ID, "quit-game").click()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "team-a-name")))
    assert browser.find_element(By.ID, "team-a-name").get_attribute("value") == "Red Arrows"
    assert browser.find_element(By.ID, "team-b-name").get_attribute("value") == "Blue Rockets"


def test_start_without_players_shows_bust_style_error(live_server, browser):
    """Starting 55 by 5 without players shows the visible setup error banner."""
    browser.get(live_server)

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-55by5"))).click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "bust-banner"), "Select at least one player."))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "bust-banner").get_attribute("class"))
    assert not browser.find_element(By.ID, "live-panel").is_displayed()



def test_non_admin_user_does_not_see_clear_history_button(live_server, browser):
    """Non-admin users keep the clear-history admin control hidden after login."""
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

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))
    clear_history_button = browser.find_element(By.ID, "clear-history")
    assert not clear_history_button.is_displayed()
    assert "hidden" in clear_history_button.get_attribute("class")


def test_current_accounts_rows_start_collapsed_and_expand_on_click(live_server, browser):
    """Admin account rows start collapsed and expand to reveal edit controls."""
    browser.get(live_server)

    browser.find_element(By.ID, "new-username").send_keys("collapseduser")
    browser.find_element(By.ID, "new-password").send_keys("viewerpass")
    browser.find_element(By.CSS_SELECTOR, "#create-user-form button[type='submit']").click()

    account_toggle = _wait(browser).until(
        ec.element_to_be_clickable(
            (
                By.XPATH,
                "//ul[@id='user-accounts-list']/li[.//strong[normalize-space()='collapseduser']]//button[@data-admin-user-toggle]",
            )
        )
    )
    assert account_toggle.get_attribute("aria-expanded") == "false"

    account_item = account_toggle.find_element(By.XPATH, "ancestor::li[1]")
    details = account_item.find_element(By.CSS_SELECTOR, ".admin-user-details")
    assert "hidden" in details.get_attribute("class")

    account_toggle.click()

    _wait(browser).until(
        lambda d: d.find_element(
            By.XPATH,
            "//ul[@id='user-accounts-list']/li[.//strong[normalize-space()='collapseduser']]//button[@data-admin-user-toggle]",
        ).get_attribute("aria-expanded") == "true"
    )
    account_item = browser.find_element(
        By.XPATH,
        "//ul[@id='user-accounts-list']/li[.//strong[normalize-space()='collapseduser']]",
    )
    details = account_item.find_element(By.CSS_SELECTOR, ".admin-user-details")
    assert "hidden" not in details.get_attribute("class")
    assert details.find_element(By.CSS_SELECTOR, "input[name='password']").is_displayed()
    assert details.find_element(By.CSS_SELECTOR, "button[type='submit']").is_displayed()


def test_admin_can_expand_account_row_and_update_password(live_server, browser):
    """An admin can expand a user row, change its password, and log in with it."""
    browser.get(live_server)

    browser.find_element(By.ID, "new-username").send_keys("passworduser")
    browser.find_element(By.ID, "new-password").send_keys("viewerpass")
    browser.find_element(By.CSS_SELECTOR, "#create-user-form button[type='submit']").click()

    account_toggle = _wait(browser).until(
        ec.element_to_be_clickable(
            (
                By.XPATH,
                "//ul[@id='user-accounts-list']/li[.//strong[normalize-space()='passworduser']]//button[@data-admin-user-toggle]",
            )
        )
    )
    account_toggle.click()

    password_input = _wait(browser).until(
        ec.visibility_of_element_located(
            (
                By.XPATH,
                "//ul[@id='user-accounts-list']/li[.//strong[normalize-space()='passworduser']]//input[@name='password']",
            )
        )
    )
    password_input.send_keys("newviewerpass")
    browser.find_element(
        By.XPATH,
        "//ul[@id='user-accounts-list']/li[.//strong[normalize-space()='passworduser']]//button[@type='submit']",
    ).click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Password updated."))

    browser.find_element(By.CSS_SELECTOR, ".logout-form button[type='submit']").click()
    _wait(browser).until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".login-form")))

    browser.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys("passworduser")
    browser.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("newviewerpass")
    browser.find_element(By.CSS_SELECTOR, ".login-form button[type='submit']").click()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))
    assert "passworduser" in browser.find_element(By.ID, "current-user").text


def test_admin_created_user_adds_player_and_account_survives_player_delete(live_server, browser):
    """Deleting a same-named player leaves the separately created user account intact."""
    browser.get(live_server)

    browser.find_element(By.ID, "new-username").send_keys("pairedviewer")
    browser.find_element(By.ID, "new-password").send_keys("viewerpass")
    browser.find_element(By.CSS_SELECTOR, "#create-user-form button[type='submit']").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "user-accounts-list"), "pairedviewer"))
    open_player_manager(browser)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "players-list"), "pairedviewer"))

    delete_button = _wait(browser).until(
        ec.element_to_be_clickable(
            (
                By.XPATH,
                "//ul[@id='players-list']/li[.//button[@data-stats-id and normalize-space()='pairedviewer']]//button[@data-delete-id]",
            )
        )
    )
    delete_button.click()

    _wait(browser).until_not(ec.text_to_be_present_in_element((By.ID, "players-list"), "pairedviewer"))
    close_player_manager(browser)
    assert "pairedviewer" in browser.find_element(By.ID, "user-accounts-list").text

    browser.find_element(By.CSS_SELECTOR, ".logout-form button[type='submit']").click()
    _wait(browser).until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".login-form")))

    browser.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys("pairedviewer")
    browser.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("viewerpass")
    browser.find_element(By.CSS_SELECTOR, ".login-form button[type='submit']").click()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))
    clear_history_button = browser.find_element(By.ID, "clear-history")
    assert not clear_history_button.is_displayed()


def test_non_admin_does_not_see_player_delete_button(live_server, browser):
    """Non-admin users cannot see player deletion controls in the player manager."""
    browser.get(live_server)

    browser.find_element(By.ID, "new-username").send_keys("nodeleteuser")
    browser.find_element(By.ID, "new-password").send_keys("viewerpass")
    browser.find_element(By.CSS_SELECTOR, "#create-user-form button[type='submit']").click()

    browser.find_element(By.CSS_SELECTOR, ".logout-form button[type='submit']").click()
    _wait(browser).until(ec.visibility_of_element_located((By.CSS_SELECTOR, ".login-form")))

    browser.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys("nodeleteuser")
    browser.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("viewerpass")
    browser.find_element(By.CSS_SELECTOR, ".login-form button[type='submit']").click()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))
    open_player_manager(browser)
    assert browser.find_elements(By.CSS_SELECTOR, "#players-list [data-delete-id]") == []
    close_player_manager(browser)


def test_busy_badge_updates_while_setup_screen_stays_open(live_server, browser):
    """The setup player list refreshes busy badges while the screen stays open."""
    browser.get(live_server)
    add_player(browser, "Dynamic Busy")

    dynamic_checkbox = _wait(browser).until(
        ec.presence_of_element_located(
            (
                By.XPATH,
                "//div[@id='selectable-players']//label[.//span[normalize-space()='Dynamic Busy']]//input",
            )
        )
    )
    assert dynamic_checkbox.get_attribute("disabled") is None

    app_module = sys.modules["app"]
    client = app_module.app.test_client()
    players = client.get("/api/players")
    dynamic_player_id = next(
        player["id"]
        for player in players.get_json()
        if player["name"] == "Dynamic Busy"
    )

    started = client.post("/api/games", json={"ordered_player_ids": [dynamic_player_id]})
    assert started.status_code == 201
    game_id = started.get_json()["game"]["id"]

    disabled_checkbox = _wait(browser, timeout=10).until(
        ec.presence_of_element_located(
            (
                By.XPATH,
                "//div[@id='selectable-players']//label[contains(@class, 'chip-busy')][.//span[normalize-space()='Dynamic Busy']]//input[@disabled]",
            )
        )
    )
    assert disabled_checkbox.get_attribute("disabled") is not None
    assert browser.find_element(
        By.XPATH,
        "//div[@id='selectable-players']//label[.//span[normalize-space()='Dynamic Busy']]//span[contains(@class, 'chip-busy-sticker') and normalize-space()='Busy']",
    ).is_displayed()

    ended = client.delete(f"/api/games/{game_id}")
    assert ended.status_code == 200

    _wait(browser, timeout=10).until(
        lambda d: d.find_element(
            By.XPATH,
            "//div[@id='selectable-players']//label[.//span[normalize-space()='Dynamic Busy']]//input",
        ).get_attribute("disabled") is None
    )
    assert not browser.find_elements(
        By.XPATH,
        "//div[@id='selectable-players']//label[.//span[normalize-space()='Dynamic Busy']]//span[contains(@class, 'chip-busy-sticker') and normalize-space()='Busy']",
    )


def test_player_selection_panel_supports_search(live_server, browser):
    """The setup player selection panel refreshes correctly after players are added."""
    browser.get(live_server)

    for name in ("Charlie", "Alpha", "Bravo"):
        add_player(browser, name)

    _wait(browser).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#selectable-players label > span:first-of-type")) == 3
    )


def test_player_manager_supports_search_and_stats_overlay_stacks_above(live_server, browser):
    """Player manager search filters names and keeps stats overlay above the modal."""
    browser.get(live_server)

    for name in ("Charlie", "Alpha", "Bravo"):
        add_player(browser, name)

    open_player_manager(browser)

    manager_search = _wait(browser).until(ec.presence_of_element_located((By.ID, "player-manager-search")))
    manager_search.clear()
    manager_search.send_keys("br")

    _wait(browser).until(
        lambda d: [
            element.text for element in d.find_elements(By.CSS_SELECTOR, "#players-list .player-name-btn")
        ] == ["Bravo"]
    )

    browser.find_element(By.CSS_SELECTOR, "#players-list .player-name-btn").click()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "player-stats-overlay")))
    assert browser.find_element(By.ID, "player-stats-title").text.strip() == "Bravo's Stats"

    stats_z_index, manager_z_index = browser.execute_script(
        """
        const stats = window.getComputedStyle(document.getElementById('player-stats-overlay')).zIndex;
        const manager = window.getComputedStyle(document.getElementById('player-manager-overlay')).zIndex;
        return [Number(stats), Number(manager)];
        """
    )
    assert stats_z_index > manager_z_index

    search_input = browser.find_element(By.ID, "player-selection-search")
    search_input.clear()
    search_input.send_keys("br")

    _wait(browser).until(
        lambda d: [
            element.text for element in d.find_elements(By.CSS_SELECTOR, "#selectable-players label > span:first-of-type")
        ] == ["Bravo"]
    )

    search_input.send_keys(Keys.COMMAND, "a")
    search_input.send_keys(Keys.DELETE)
    _wait(browser).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#selectable-players label > span:first-of-type")) == 3
    )


def test_55_by_5_individual_game_can_complete_end_to_end(live_server, browser):
    """A solo 55 by 5 game can finish cleanly and return to setup state."""
    browser.get(live_server)
    start_single_player_game(browser, "Finn")

    turn_values = (75, 75, 75, 50)
    for turn_number, value in enumerate(turn_values, start=1):
        submit_standard_score_with_keypad(browser, value)
        if turn_number < len(turn_values):
            _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), f"#{turn_number} Finn: total {value}"))

    winner_overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert winner_overlay.is_displayed()
    assert browser.find_element(By.ID, "winner-name").text.strip() == "Finn"
    assert "Winner Finn" in browser.find_element(By.ID, "history-list").text

    browser.find_element(By.ID, "winner-continue").click()
    _wait(browser).until(lambda d: not d.find_element(By.ID, "winner-overlay").is_displayed())
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "hero-title"), "Set Up Your Darts Game"))
    assert "Pick your players" in browser.find_element(By.ID, "hero-subtitle").text
    assert browser.find_element(By.ID, "selected-game-label").text.strip() == ""
    finn_checkbox = browser.find_element(
        By.XPATH,
        "//div[@id='selectable-players']//label[.//span[normalize-space()='Finn']]//input",
    )
    assert finn_checkbox.is_selected()
    selected_names = [
        item.text.strip() for item in browser.find_elements(By.CSS_SELECTOR, "#order-list li .sortable-player-name")
    ]
    assert selected_names == ["Finn"]



def test_55_by_5_team_game_can_complete_end_to_end(live_server, browser):
    """A team 55 by 5 game can finish with custom team names preserved afterward."""
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
    team_a_name = browser.find_element(By.ID, "team-a-name")
    team_b_name = browser.find_element(By.ID, "team-b-name")
    team_a_name.clear()
    team_a_name.send_keys("Red Arrows")
    team_b_name.clear()
    team_b_name.send_keys("Blue Rockets")
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
        submit_standard_score_with_keypad(browser, value)
        if turn_number < len(scripted_turns):
            _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), f"#{turn_number} {player_name}: total {value}"))

    winner_overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert winner_overlay.is_displayed()
    assert browser.find_element(By.ID, "winner-name").text.strip() == "Red Arrows"
    assert "Winner Red Arrows" in browser.find_element(By.ID, "history-list").text

    browser.find_element(By.ID, "winner-continue").click()
    _wait(browser).until(lambda d: not d.find_element(By.ID, "winner-overlay").is_displayed())
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "team-a-name")))

    team_mode = browser.find_element(By.ID, "team-mode-teams")
    assert team_mode.is_selected()
    assert browser.find_element(By.ID, "team-a-name").get_attribute("value") == "Red Arrows"
    assert browser.find_element(By.ID, "team-b-name").get_attribute("value") == "Blue Rockets"

    for player_name in ("Aria", "Bryn"):
        checkbox = browser.find_element(
            By.XPATH,
            f"//div[@id='selectable-players']//label[.//span[normalize-space()='{player_name}']]//input",
        )
        assert checkbox.is_selected()

    team_a_players = [
        item.text.strip() for item in browser.find_elements(By.CSS_SELECTOR, "#team-a-list li .sortable-player-name")
    ]
    team_b_players = [
        item.text.strip() for item in browser.find_elements(By.CSS_SELECTOR, "#team-b-list li .sortable-player-name")
    ]
    assert team_a_players == ["Aria"]
    assert team_b_players == ["Bryn"]


def test_english_cricket_shows_starting_roles_popup_before_game_start(live_server, browser):
    """English Cricket shows the starting-role chooser before entering live play."""
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


def test_x01_shows_start_popup_with_defaults(live_server, browser):
    """The X01 start dialog exposes the default score, match, and starter settings."""
    browser.get(live_server)

    add_player(browser, "X01 Starter")
    player_checkbox = _wait(browser).until(
        ec.presence_of_element_located(
            (
                By.XPATH,
                "//div[@id='selectable-players']//label[.//span[normalize-space()='X01 Starter']]//input",
            )
        )
    )
    if not player_checkbox.is_selected():
        player_checkbox.click()

    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-x01"))).click()
    popup = _wait(browser).until(ec.visibility_of_element_located((By.ID, "x01-start-overlay")))

    assert popup.find_element(By.CSS_SELECTOR, "input[name='x01-starting-score'][value='501']").is_selected()
    assert Select(popup.find_element(By.ID, "x01-match-type")).first_selected_option.get_attribute("value") == "best_of"
    assert popup.find_element(By.ID, "x01-legs-value").get_attribute("value") == "1"
    assert popup.find_element(By.ID, "x01-legs-value-label").text.strip() == "1"

    starting_picker = Select(popup.find_element(By.ID, "x01-starting-entity"))
    option_labels = [option.text.strip() for option in starting_picker.options]
    assert option_labels == ["X01 Starter", "Random"]
    assert starting_picker.first_selected_option.text.strip() == "X01 Starter"

    browser.find_element(By.ID, "x01-start-game").click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    assert "501" in browser.find_element(By.ID, "scoreboard").text
    headers = browser.find_elements(By.CSS_SELECTOR, "#scoreboard-table thead th")
    visible_headers = [header.text.strip() for header in headers if header.is_displayed()]
    assert visible_headers == ["Player", "Remaining", "Legs", "Target"]

    first_row_cells = browser.find_elements(By.CSS_SELECTOR, "#scoreboard tr")[0].find_elements(By.TAG_NAME, "td")
    assert [cell.text.strip() for cell in first_row_cells] == ["X01 Starter", "501", "0", "1"]


def test_x01_singles_game_can_complete_end_to_end(live_server, browser):
    """A solo X01 game can play through checkout and show the winner overlay."""
    browser.get(live_server)
    start_x01_game(browser, ["Ava"], starting_score="101")

    submit_standard_score_with_keypad(browser, 60)

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "scoreboard"), "41"))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "x01-checkout-hint"), "9 D16"))

    submit_standard_score_with_keypad(browser, 41)

    winner_overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert winner_overlay.is_displayed()
    assert browser.find_element(By.ID, "winner-name").text.strip() == "Ava"


def test_x01_first_to_three_requires_three_legs_to_win_end_to_end(live_server, browser):
    """First-to X01 does not finish until the configured leg target is reached."""
    browser.get(live_server)
    start_x01_game(
        browser,
        ["Ava"],
        starting_score="101",
        match_type="first_to",
        legs_value=3,
    )

    submit_standard_score_with_keypad(browser, 101)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Ava: total 101"))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "scoreboard"), "101"))
    assert not browser.find_element(By.ID, "winner-overlay").is_displayed()

    submit_standard_score_with_keypad(browser, 101)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#2 Ava: total 101"))
    assert not browser.find_element(By.ID, "winner-overlay").is_displayed()

    submit_standard_score_with_keypad(browser, 101)
    winner_overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert winner_overlay.is_displayed()
    assert browser.find_element(By.ID, "winner-name").text.strip() == "Ava"


def test_x01_scoreboard_legs_and_target_increment_each_new_leg(live_server, browser):
    """X01 scoreboard leg counts advance while the target stays fixed across legs."""
    browser.get(live_server)
    start_x01_game(
        browser,
        ["Ava"],
        starting_score="101",
        match_type="first_to",
        legs_value=3,
    )

    def scoreboard_row_values():
        row = _wait(browser).until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "#scoreboard tr")))[0]
        cells = row.find_elements(By.TAG_NAME, "td")
        return [cell.text.strip() for cell in cells]

    assert scoreboard_row_values() == ["Ava", "101", "0", "3"]

    submit_standard_score_with_keypad(browser, 101)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Ava: total 101"))
    _wait(browser).until(lambda d: scoreboard_row_values() == ["Ava", "101", "1", "3"])

    submit_standard_score_with_keypad(browser, 101)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#2 Ava: total 101"))
    _wait(browser).until(lambda d: scoreboard_row_values() == ["Ava", "101", "2", "3"])


def test_x01_best_of_three_finishes_after_two_legs_end_to_end(live_server, browser):
    """Best-of-three X01 finishes as soon as one side secures two legs."""
    browser.get(live_server)
    start_x01_game(
        browser,
        ["Nora"],
        starting_score="101",
        match_type="best_of",
        legs_value=3,
    )

    submit_standard_score_with_keypad(browser, 101)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Nora: total 101"))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "scoreboard"), "101"))
    assert not browser.find_element(By.ID, "winner-overlay").is_displayed()

    submit_standard_score_with_keypad(browser, 101)
    winner_overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert winner_overlay.is_displayed()
    assert browser.find_element(By.ID, "winner-name").text.strip() == "Nora"


def test_x01_team_game_can_complete_end_to_end(live_server, browser):
    """A team X01 game can complete end to end with shared team scoring."""
    browser.get(live_server)
    start_x01_game(browser, ["Aria", "Bryn"], starting_score="101", team_mode="teams")

    scoreboard = _wait(browser).until(ec.visibility_of_element_located((By.ID, "scoreboard")))
    assert "Team A" in scoreboard.text
    assert "Team B" in scoreboard.text

    submit_standard_score_with_keypad(browser, 60)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "scoreboard"), "41"))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turn-player-name"), "Bryn"))

    submit_standard_score_with_keypad(browser, 0)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#2 Bryn: total 0"))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turn-player-name"), "Aria"))

    submit_standard_score_with_keypad(browser, 41)

    winner_overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert winner_overlay.is_displayed()
    assert browser.find_element(By.ID, "winner-name").text.strip() == "Team A"


def test_x01_team_mode_can_choose_team_b_to_throw_first(live_server, browser):
    """Team X01 can be configured so Team B throws the opening turn."""
    browser.get(live_server)
    start_x01_game(
        browser,
        ["Aria", "Bryn"],
        starting_score="101",
        team_mode="teams",
        starting_entity="team_b",
    )

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turn-player-name"), "Bryn"))


def test_english_cricket_rejects_more_than_two_individual_players(live_server, browser):
    """English Cricket blocks solo starts unless exactly two players are selected."""
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

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "bust-banner"), "Select exactly two players or teams to play English Cricket."))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "bust-banner").get_attribute("class"))
    assert not browser.find_element(By.ID, "cricket-start-overlay").is_displayed()


def test_noughts_and_crosses_team_mode_can_start(live_server, browser):
    """Noughts and Crosses can start in team mode once both teams are assigned."""
    browser.get(live_server)

    for player_name in ("Nora", "Omar", "Pia", "Quin"):
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
    _wait(browser).until(ec.element_to_be_clickable((By.ID, "choose-noughts-and-crosses"))).click()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "live-panel")))
    dashboard = _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-dashboard")))
    assert "Team A" in dashboard.text
    assert "Team B" in dashboard.text


def test_noughts_and_crosses_rejects_more_than_two_individual_players(live_server, browser):
    """Solo Noughts rejects starts with more than two selected players."""
    browser.get(live_server)

    for player_name in ("Rae", "Seth", "Tia"):
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

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "bust-banner"), "Select exactly two players to play Noughts and Crosses."))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "bust-banner").get_attribute("class"))
    assert not browser.find_element(By.ID, "live-panel").is_displayed()


def test_submit_turn_updates_score_and_clears_input(live_server, browser):
    """Submitting a 55 by 5 turn updates the board and clears the keypad display."""
    browser.get(live_server)
    start_single_player_game(browser, "Bob")

    turn_total = browser.find_element(By.ID, "turn-total")
    assert turn_total.get_attribute("readonly") is not None
    submit_standard_score_with_keypad(browser, 15)

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "scoreboard"), "3"))
    _wait(browser).until(lambda d: d.find_element(By.ID, "turn-total").get_attribute("value") == "")

    scoreboard_text = browser.find_element(By.ID, "scoreboard").text
    assert "Bob" in scoreboard_text
    assert "3" in scoreboard_text
    assert "260" in scoreboard_text


def test_english_cricket_live_view_uses_two_panels(live_server, browser):
    """English Cricket live play shows separate bowling and batting control panels."""
    browser.get(live_server)
    start_cricket_game(browser, "Ivy", "Jules")

    bowling_panel = _wait(browser).until(ec.visibility_of_element_located((By.ID, "cricket-bowling-panel")))
    batting_panel = browser.find_element(By.ID, "cricket-batting-panel")
    batting_input = browser.find_element(By.ID, "cricket-batting-total")

    assert "bowling side" in bowling_panel.text.lower()
    assert "batting side" in batting_panel.text.lower()
    assert "this throw:" not in bowling_panel.text.lower()
    assert "maximum 6 per throw" not in bowling_panel.text.lower()
    assert "click any bull markers" not in bowling_panel.text.lower()
    assert len(browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip")) == 10
    assert not batting_input.is_enabled()
    assert "Jules to Throw" in browser.find_element(By.ID, "active-game-meta").text

    cricket_undo = browser.find_element(By.ID, "cricket-undo-turn")
    assert cricket_undo.is_displayed()

    bull_buttons = browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled])")
    assert len(bull_buttons) == 10
    for index in (0, 2, 4, 6, 8, 9):
        browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled])")[index].click()

    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip.is-selected")) == 6)
    browser.find_element(By.ID, "cricket-submit-bowling").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Ivy to Throw"))
    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip.is-hit")) == 6)
    _wait(browser).until(lambda d: d.find_element(By.ID, "cricket-batting-total").is_enabled())
    submit_cricket_score_with_keypad(browser, 60)

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Jules to Throw"))
    browser.find_element(By.ID, "cricket-undo-turn").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Last turn undone."))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Ivy to Throw"))
    updated_bowling_panel = browser.find_element(By.ID, "cricket-bowling-panel")
    assert "is-inactive" in updated_bowling_panel.get_attribute("class")


def test_english_cricket_shows_target_and_remaining_runs_in_second_innings(live_server, browser):
    """Second-innings Cricket batting shows the chase target and remaining runs."""
    browser.get(live_server)
    start_cricket_game(browser, "Ivy", "Jules")

    for index in (0, 2, 4, 6, 8, 9):
        browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled])")[index].click()
    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip.is-selected")) == 6)
    browser.find_element(By.ID, "cricket-submit-bowling").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Ivy to Throw"))
    _wait(browser).until(lambda d: d.find_element(By.ID, "cricket-batting-total").is_enabled())
    submit_cricket_score_with_keypad(browser, 60)

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "active-game-meta"), "Jules to Throw"))
    for _ in range(4):
        browser.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip:not([disabled]):not(.is-selected)")[0].click()
    _wait(browser).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cricket-bowling-panel .bullseye-chip.is-selected")) == 4)
    browser.find_element(By.ID, "cricket-submit-bowling").click()

    _wait(browser).until(lambda d: "jules" in d.find_element(By.ID, "cricket-batting-panel").text.lower())
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "cricket-batting-panel"), "TARGET"))
    batting_panel = browser.find_element(By.ID, "cricket-batting-panel")
    panel_text = batting_panel.text.lower()
    assert "target" in panel_text
    assert "remaining runs" in panel_text
    assert "21" in panel_text


def test_english_cricket_shows_message_only_when_more_than_six_marks_selected(live_server, browser):
    """Cricket warns only after submitting more than six selected wicket marks."""
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
    """Quitting a live game respects cancel first and only exits after confirmation."""
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
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "hero-title"), "Set Up Your Darts Game"))
    assert "Pick your players" in browser.find_element(By.ID, "hero-subtitle").text
    assert browser.find_element(By.ID, "selected-game-label").text.strip() == ""
    assert browser.find_element(By.ID, "setup-panel").is_displayed()


def test_quit_restores_selected_players_in_setup(live_server, browser):
    """Quitting a game returns to setup with the prior player selection restored."""
    browser.get(live_server)

    for player_name in ("Charlie", "Dana"):
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

    browser.execute_script("window.confirm = function () { return true; };")
    browser.find_element(By.ID, "quit-game").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Game quit."))
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "setup-panel")))

    selected_names = [
        item.text.strip() for item in browser.find_elements(By.CSS_SELECTOR, "#order-list li .sortable-player-name")
    ]
    assert selected_names == ["Charlie", "Dana"]

    for player_name in ("Charlie", "Dana"):
        checkbox = browser.find_element(
            By.XPATH,
            f"//div[@id='selectable-players']//label[.//span[normalize-space()='{player_name}']]//input",
        )
        assert checkbox.is_selected()


def test_bust_shows_red_banner_for_three_seconds(live_server, browser):
    """A bust shows the red banner immediately and then dismisses after a short delay."""
    browser.get(live_server)
    start_single_player_game(browser, "Dana")

    turn_values = [75, 75, 75, 15, 15, 15]

    for turn_number, value in enumerate(turn_values, start=1):
        submit_standard_score_with_keypad(browser, value)
        _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), f"#{turn_number} Dana: total {value}"))

    # Final 15 causes bust; assert the banner immediately rather than after score refresh.
    submit_standard_score_with_keypad(browser, 15)
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "bust-banner"), "Bust"))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "bust-banner").get_attribute("class"))
    WebDriverWait(browser, 5).until(
        lambda d: "visible" not in d.find_element(By.ID, "bust-banner").get_attribute("class")
    )


def test_non_divisible_by_five_shows_popup_and_keeps_total(live_server, browser):
    """Non-divisible scores show a warning while leaving the running total unchanged."""
    browser.get(live_server)
    start_single_player_game(browser, "Eve")

    submit_standard_score_with_keypad(browser, 12)

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "score-warning-banner"), "Total scored must be divisible by 5."))
    _wait(browser).until(lambda d: "visible" in d.find_element(By.ID, "score-warning-banner").get_attribute("class"))
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "total 12 (+0 fives)"))

    scoreboard_text = browser.find_element(By.ID, "scoreboard").text
    assert "Eve" in scoreboard_text
    assert "0" in scoreboard_text


# ---------------------------------------------------------------------------
# Noughts and Crosses – individual play
# ---------------------------------------------------------------------------

def test_noughts_individual_x_o_pills_show_player_names(live_server, browser):
    """X and O side pills display the individual player names."""
    browser.get(live_server)
    start_noughts_game(browser, "Alice", "Bob")

    dashboard = browser.find_element(By.ID, "noughts-dashboard")
    pills = dashboard.find_elements(By.CSS_SELECTOR, ".noughts-side-pill")
    pill_text = " ".join(p.text for p in pills)
    assert "Alice" in pill_text
    assert "Bob" in pill_text


def test_noughts_individual_cell_can_be_claimed_with_x(live_server, browser):
    """Clicking an unclaimed cell and choosing X marks it as X."""
    browser.get(live_server)
    start_noughts_game(browser, "Clara", "Dan")

    noughts_click_cell(browser, 0, "X")

    cell = browser.find_element(By.CSS_SELECTOR, "[data-board-index='0']")
    assert "is-x" in cell.get_attribute("class")
    assert cell.find_element(By.CSS_SELECTOR, ".noughts-cell-mark").text.strip() == "X"


def test_noughts_individual_cell_can_be_claimed_with_o(live_server, browser):
    """Clicking an unclaimed cell and choosing O marks it as O."""
    browser.get(live_server)
    start_noughts_game(browser, "Eli", "Fay")

    noughts_click_cell(browser, 1, "O")

    cell = browser.find_element(By.CSS_SELECTOR, "[data-board-index='1']")
    assert "is-o" in cell.get_attribute("class")
    assert cell.find_element(By.CSS_SELECTOR, ".noughts-cell-mark").text.strip() == "O"


def test_noughts_individual_turn_appears_in_turn_log(live_server, browser):
    """Each claimed cell is recorded in the turns list."""
    browser.get(live_server)
    start_noughts_game(browser, "Grace", "Hal")

    noughts_click_cell(browser, 2, "X")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Grace:"))
    turn_text = browser.find_element(By.ID, "turns-list").text
    assert "X" in turn_text or "x" in turn_text.lower()

    noughts_click_cell(browser, 3, "O")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#2 Hal:"))


def test_noughts_individual_undo_button_is_visible_and_functional(live_server, browser):
    """Undo removes the last claimed cell from the board."""
    browser.get(live_server)
    start_noughts_game(browser, "Ida", "Jake")

    noughts_click_cell(browser, 4, "X")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Ida:"))

    undo_btn = _wait(browser).until(ec.element_to_be_clickable((By.ID, "cricket-undo-turn")))
    assert undo_btn.is_displayed()
    undo_btn.click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Last turn undone."))
    # Cell should be unclaimed again
    cell = _wait(browser).until(
        lambda d: d.find_element(By.CSS_SELECTOR, "[data-board-index='4']")
    )
    _wait(browser).until(lambda d: "is-marked" not in d.find_element(By.CSS_SELECTOR, "[data-board-index='4']").get_attribute("class"))


def test_noughts_individual_undo_preserves_other_cells(live_server, browser):
    """Undoing the last move does not disturb previously claimed cells."""
    browser.get(live_server)
    start_noughts_game(browser, "Kim", "Leo")

    noughts_click_cell(browser, 0, "X")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Kim:"))
    noughts_click_cell(browser, 1, "O")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#2 Leo:"))

    browser.find_element(By.ID, "cricket-undo-turn").click()
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Last turn undone."))

    # Cell 0 (first move) must still be claimed
    _wait(browser).until(lambda d: "is-marked" in d.find_element(By.CSS_SELECTOR, "[data-board-index='0']").get_attribute("class"))
    # Cell 1 (undone move) must be unclaimed
    _wait(browser).until(lambda d: "is-marked" not in d.find_element(By.CSS_SELECTOR, "[data-board-index='1']").get_attribute("class"))


def test_noughts_individual_winning_line_shows_winner_overlay(live_server, browser):
    """Completing a three-in-a-row triggers the winner overlay."""
    browser.get(live_server)
    start_noughts_game(browser, "Mia", "Ned")

    # Claim cells 0, 1, 2 with X (rows 0–2 of the top row) to make X win
    # Alternate marks: Mia=X, Ned=O
    noughts_click_cell(browser, 0, "X")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Mia:"))
    noughts_click_cell(browser, 3, "O")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#2 Ned:"))
    noughts_click_cell(browser, 1, "X")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#3 Mia:"))
    noughts_click_cell(browser, 4, "O")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#4 Ned:"))
    noughts_click_cell(browser, 2, "X")

    # Winner overlay must appear
    overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert overlay.is_displayed()
    winner_text = overlay.text
    assert "Mia" in winner_text or "X" in winner_text


def test_noughts_individual_claimed_cell_is_disabled(live_server, browser):
    """A cell that has already been claimed cannot be clicked again."""
    browser.get(live_server)
    start_noughts_game(browser, "Ona", "Pat")

    noughts_click_cell(browser, 5, "X")
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "turns-list"), "#1 Ona:"))

    cell = browser.find_element(By.CSS_SELECTOR, "[data-board-index='5']")
    assert cell.get_attribute("disabled") is not None


def test_noughts_individual_cancel_overlay_leaves_cell_unclaimed(live_server, browser):
    """Cancelling the mark overlay leaves the cell unclaimed."""
    browser.get(live_server)
    start_noughts_game(browser, "Ray", "Sue")

    board = browser.find_element(By.ID, "noughts-dashboard")
    board.find_element(By.CSS_SELECTOR, "[data-board-index='6']").click()
    chooser = _wait(browser).until(ec.visibility_of_element_located((By.ID, "noughts-mark-overlay")))
    cancel_btn = chooser.find_element(By.ID, "noughts-mark-cancel")
    cancel_btn.click()

    _wait(browser).until(ec.invisibility_of_element_located((By.ID, "noughts-mark-overlay")))
    cell = browser.find_element(By.CSS_SELECTOR, "[data-board-index='6']")
    assert "is-marked" not in (cell.get_attribute("class") or "")


def test_noughts_individual_quit_returns_to_setup(live_server, browser):
    """Quitting an active Noughts game returns to the setup screen."""
    browser.get(live_server)
    start_noughts_game(browser, "Tom", "Uma")

    browser.execute_script("window.confirm = function () { return true; };")
    browser.find_element(By.ID, "quit-game").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Game quit."))
    _wait(browser).until(lambda d: not d.find_element(By.ID, "live-panel").is_displayed())
    assert browser.find_element(By.ID, "setup-panel").is_displayed()


# ---------------------------------------------------------------------------
# Noughts and Crosses – team play
# ---------------------------------------------------------------------------

def test_noughts_team_x_o_pills_show_team_names_with_initials(live_server, browser):
    """In team mode the X/O pills show 'Team A (V & X)' style initials labels.

    Auto-balance with add-order [Vera, Walt, Xena, Yuki] yields:
    Team A: Vera, Xena  Team B: Walt, Yuki
    """
    browser.get(live_server)
    start_noughts_team_game(browser, ["Vera", "Walt"], ["Xena", "Yuki"])

    dashboard = browser.find_element(By.ID, "noughts-dashboard")
    pills = dashboard.find_elements(By.CSS_SELECTOR, ".noughts-side-pill")
    pill_text = " ".join(p.text for p in pills)
    assert "Team A" in pill_text
    assert "Team B" in pill_text
    # Initials in parentheses should be present (Team A: V & X, Team B: W & Y)
    assert "(" in pill_text
    assert "V" in pill_text or "X" in pill_text


def test_noughts_team_cell_can_be_claimed_by_team(live_server, browser):
    """A team member can claim a cell; the cell shows the team's marker.

    Auto-balance with [Zara, Andy, Beth, Cole] → Team A: Zara, Beth; Team B: Andy, Cole.
    First turn belongs to Zara (Team A / X).
    """
    browser.get(live_server)
    start_noughts_team_game(browser, ["Zara", "Andy"], ["Beth", "Cole"])

    noughts_click_cell(browser, 0, "X")
    _wait(browser).until(lambda d: "#1" in d.find_element(By.ID, "turns-list").text)

    cell = browser.find_element(By.CSS_SELECTOR, "[data-board-index='0']")
    assert "is-marked" in cell.get_attribute("class")


def test_noughts_team_undo_restores_cell(live_server, browser):
    """Undo in team mode un-claims the cell and the board label is preserved.

    Auto-balance with [Dean, Ella, Fred, Gwen] → Team A: Dean, Fred; Team B: Ella, Gwen.
    First turn: Dean (Team A / X).
    """
    browser.get(live_server)
    start_noughts_team_game(browser, ["Dean", "Ella"], ["Fred", "Gwen"])

    board = browser.find_element(By.ID, "noughts-dashboard")
    first_cell = board.find_elements(By.CSS_SELECTOR, "[data-board-index]")[0]
    original_label = first_cell.find_element(By.CSS_SELECTOR, ".noughts-cell-label").text.strip()

    noughts_click_cell(browser, 0, "X")
    _wait(browser).until(lambda d: "#1" in d.find_element(By.ID, "turns-list").text)

    browser.find_element(By.ID, "cricket-undo-turn").click()
    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Last turn undone."))

    _wait(browser).until(lambda d: "is-marked" not in d.find_element(By.CSS_SELECTOR, "[data-board-index='0']").get_attribute("class"))
    restored_label = browser.find_element(By.CSS_SELECTOR, "[data-board-index='0'] .noughts-cell-label").text.strip()
    assert restored_label == original_label


def test_noughts_team_winning_line_shows_winner_overlay(live_server, browser):
    """Team X completing a three-in-a-row triggers the winner overlay.

    Auto-balance with [Hugo, Iris, Jack, Kate] → Team A: Hugo, Jack; Team B: Iris, Kate.
    Interleaved order: Hugo(X), Iris(O), Jack(X), Kate(O).
    Hugo and Jack play X; Iris plays O for the blocking turns.
    """
    browser.get(live_server)
    start_noughts_team_game(browser, ["Hugo", "Iris"], ["Jack", "Kate"])

    noughts_click_cell(browser, 0, "X")
    _wait(browser).until(lambda d: "#1" in d.find_element(By.ID, "turns-list").text)
    noughts_click_cell(browser, 3, "O")
    _wait(browser).until(lambda d: "#2" in d.find_element(By.ID, "turns-list").text)
    noughts_click_cell(browser, 1, "X")
    _wait(browser).until(lambda d: "#3" in d.find_element(By.ID, "turns-list").text)
    noughts_click_cell(browser, 4, "O")
    _wait(browser).until(lambda d: "#4" in d.find_element(By.ID, "turns-list").text)
    noughts_click_cell(browser, 2, "X")

    overlay = _wait(browser).until(ec.visibility_of_element_located((By.ID, "winner-overlay")))
    assert overlay.is_displayed()
    winner_text = overlay.text
    assert "Team A" in winner_text
    assert "(" in winner_text and ")" in winner_text


def test_noughts_team_quit_returns_to_setup(live_server, browser):
    """Quitting a team Noughts game returns to the setup screen."""
    browser.get(live_server)
    start_noughts_team_game(browser, ["Liam", "Maya"], ["Noel", "Orla"])

    browser.execute_script("window.confirm = function () { return true; };")
    browser.find_element(By.ID, "quit-game").click()

    _wait(browser).until(ec.text_to_be_present_in_element((By.ID, "message"), "Game quit."))
    _wait(browser).until(lambda d: not d.find_element(By.ID, "live-panel").is_displayed())
    assert browser.find_element(By.ID, "setup-panel").is_displayed()
