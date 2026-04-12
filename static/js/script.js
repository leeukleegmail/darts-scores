const state = {
  players: [],
  selectedPlayerIds: new Set(),
  orderedPlayerIds: [],
  game: null,
  gameType: null,
  teamMode: "solo",
  teamAssignments: {},
  teamNames: { team_a: "Team A", team_b: "Team B" },
  cricketPendingMarks: 0,
  cricketSelectedMarks: [],
  cricketStartingBattingTeam: "team_a",
  pendingNoughtsCellIndex: null,
};

const appShellEl = document.querySelector(".app-shell");
const heroTitleEl = document.getElementById("hero-title");
const heroSubtitleEl = document.getElementById("hero-subtitle");
const playersPanelEl = document.getElementById("players-panel");
const gameSelectionPanelEl = document.getElementById("game-selection-panel");
const setupPanelEl = document.getElementById("setup-panel");
const livePanelEl = document.getElementById("live-panel");
const messageEl = document.getElementById("message");
const playersListEl = document.getElementById("players-list");
const selectablePlayersEl = document.getElementById("selectable-players");
const orderListEl = document.getElementById("order-list");
const orderSectionEl = document.getElementById("order-section");
const activeGameMetaEl = document.getElementById("active-game-meta");
const scoreboardEl = document.getElementById("scoreboard");
const turnsListEl = document.getElementById("turns-list");
const historyListEl = document.getElementById("history-list");
const turnInputEl = document.getElementById("turn-input");
const standardTurnControlsEl = document.getElementById("standard-turn-controls");
const sharedTurnActionsEl = document.querySelector(".shared-actions");
const cricketUndoTurnEl = document.getElementById("cricket-undo-turn");
const standardScoreKeypadEl = document.getElementById("standard-score-keypad");
const bullHitEl = document.getElementById("bull-hit");
const selectedGameLabelEl = document.getElementById("selected-game-label");
const teamAssignmentEl = document.getElementById("team-assignment");
const cricketStartOverlayEl = document.getElementById("cricket-start-overlay");
const cricketStartPromptEl = document.getElementById("cricket-start-prompt");
const cricketStartOptionsEl = document.getElementById("cricket-start-options");
const cricketStartGameEl = document.getElementById("cricket-start-game");
const cricketStartCancelEl = document.getElementById("cricket-start-cancel");
const teamAListEl = document.getElementById("team-a-list");
const teamBListEl = document.getElementById("team-b-list");
const teamANameInputEl = document.getElementById("team-a-name");
const teamBNameInputEl = document.getElementById("team-b-name");
const turnInputLabelEl = document.getElementById("turn-input-label");
const cricketDashboardEl = document.getElementById("cricket-dashboard");
const cricketBowlingPanelEl = document.getElementById("cricket-bowling-panel");
const cricketBattingPanelEl = document.getElementById("cricket-batting-panel");
const noughtsDashboardEl = document.getElementById("noughts-dashboard");
const noughtsMarkOverlayEl = document.getElementById("noughts-mark-overlay");
const noughtsMarkPromptEl = document.getElementById("noughts-mark-prompt");
const noughtsMarkOptionsEl = document.getElementById("noughts-mark-options");
const noughtsMarkCancelEl = document.getElementById("noughts-mark-cancel");
const scoreboardSectionEl = document.getElementById("standard-scoreboard-section");
const historyPanelEl = document.getElementById("history-panel");
const winnerOverlayEl = document.getElementById("winner-overlay");
const bustBannerEl = document.getElementById("bust-banner");
const scoreWarningBannerEl = document.getElementById("score-warning-banner");
const currentUserEl = document.getElementById("current-user");
const logoutFormEl = document.querySelector(".logout-form");
const adminPanelEl = document.getElementById("admin-panel");
const clearHistoryEl = document.getElementById("clear-history");
const userAccountsListEl = document.getElementById("user-accounts-list");
const helpButtonEl = document.getElementById("help-button");
const helpOverlayEl = document.getElementById("help-overlay");
const helpCloseEl = document.getElementById("help-close");
const helpNavEl = document.getElementById("help-nav");
const helpPrevEl = document.getElementById("help-prev");
const helpNextEl = document.getElementById("help-next");
const helpSections = Array.from(document.querySelectorAll(".help-section"));
const helpSectionOrder = helpSections
  .map((section) => section.getAttribute("data-help-section"))
  .filter(Boolean);
const SESSION_IDLE_TIMEOUT_MS = 30 * 60 * 1000;

let bustBannerTimeoutId = null;
let scoreWarningTimeoutId = null;
let pendingTurnSubmission = Promise.resolve();
let activeHelpSection = helpSectionOrder[0] || "quick-start";
let inactivityLogoutTimeoutId = null;
let idleLogoutInProgress = false;

function showBustBanner(text) {
  if (!bustBannerEl) return;
  bustBannerEl.textContent = text;
  bustBannerEl.classList.add("visible");
  if (bustBannerTimeoutId) {
    clearTimeout(bustBannerTimeoutId);
  }
  bustBannerTimeoutId = window.setTimeout(() => {
    bustBannerEl.classList.remove("visible");
  }, 3000);
}

function showScoreWarningBanner(text) {
  if (!scoreWarningBannerEl) return;
  scoreWarningBannerEl.textContent = text;
  scoreWarningBannerEl.classList.add("visible");
  if (scoreWarningTimeoutId) {
    clearTimeout(scoreWarningTimeoutId);
  }
  scoreWarningTimeoutId = window.setTimeout(() => {
    scoreWarningBannerEl.classList.remove("visible");
  }, 3000);
}

function launchFireworks(canvas) {
  const ctx = canvas.getContext("2d");
  const COLORS = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#ff922b", "#cc5de8", "#f06595", "#ffffff"];
  const particles = [];
  let animId;
  let frame = 0;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  function burst(x, y) {
    const count = 70 + Math.floor(Math.random() * 40);
    const baseColor = COLORS[Math.floor(Math.random() * COLORS.length)];
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.3;
      const speed = 2 + Math.random() * 7;
      particles.push({
        x, y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 1,
        alpha: 1,
        color: Math.random() < 0.7 ? baseColor : COLORS[Math.floor(Math.random() * COLORS.length)],
        size: 2 + Math.random() * 4,
      });
    }
  }

  function tick() {
    animId = requestAnimationFrame(tick);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    frame++;
    if (frame % 38 === 0) {
      burst(
        canvas.width * (0.15 + Math.random() * 0.7),
        canvas.height * (0.05 + Math.random() * 0.5)
      );
    }
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.vy += 0.07;
      p.vx *= 0.99;
      p.x += p.vx;
      p.y += p.vy;
      p.alpha -= 0.013;
      if (p.alpha <= 0) { particles.splice(i, 1); continue; }
      ctx.globalAlpha = p.alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  burst(canvas.width * 0.3, canvas.height * 0.3);
  burst(canvas.width * 0.7, canvas.height * 0.25);
  burst(canvas.width * 0.5, canvas.height * 0.4);
  tick();

  return function stop() {
    cancelAnimationFrame(animId);
    window.removeEventListener("resize", resize);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };
}

let stopFireworks = null;

function showWinnerOverlay(winnerName) {
  const winnerNameEl = document.getElementById("winner-name");
  const fireworksCanvas = document.getElementById("fireworks-canvas");
  if (!winnerOverlayEl || !winnerNameEl || !fireworksCanvas) {
    return;
  }
  winnerNameEl.textContent = winnerName;
  winnerOverlayEl.classList.add("visible");
  stopFireworks = launchFireworks(fireworksCanvas);
}

function showMessage(text, isError = false) {
  messageEl.textContent = text;
  messageEl.className = isError ? "message error" : "message";
}

function createScoreKeypadMarkup({
  submitButtonId,
  submitLabel = "Submit Score",
  noScoreButtonId,
  noScoreLabel = "No Score",
  disabled = false,
  showUndo = true,
}) {
  const disabledAttr = disabled ? "disabled" : "";
  const digitButtons = Array.from({ length: 9 }, (_, index) => {
    const value = String(index + 1);
    return `
      <button type="button" class="score-key score-key--digit" data-keypad-value="${value}" ${disabledAttr}>${value}</button>
    `;
  }).join("");

  const toolbarButtons = [
    `<button type="button" class="score-key score-key--backspace" data-keypad-action="backspace" aria-label="Backspace" title="Backspace" ${disabledAttr}>⌫</button>`,
    showUndo
      ? `<button type="button" class="score-key score-key--undo" data-keypad-action="undo" aria-label="Undo last turn" title="Undo last turn" ${disabledAttr}>↺</button>`
      : "",
  ].join("");

  return `
    <div class="score-keypad-toolbar${showUndo ? "" : " score-keypad-toolbar--single"}">
      ${toolbarButtons}
    </div>
    ${digitButtons}
    <button id="${noScoreButtonId}" type="button" class="score-key score-key--danger" data-keypad-action="no-score" ${disabledAttr}>${noScoreLabel}</button>
    <button type="button" class="score-key score-key--digit score-key--zero" data-keypad-value="0" ${disabledAttr}>0</button>
    <button id="${submitButtonId}" type="button" class="score-key score-key--submit" data-keypad-action="submit" ${disabledAttr}>${submitLabel}</button>
  `;
}

function renderStandardScoreKeypad() {
  if (!standardScoreKeypadEl) return;
  standardScoreKeypadEl.innerHTML = createScoreKeypadMarkup({
    submitButtonId: "submit-turn",
    noScoreButtonId: "no-score",
  });
}

function appendDigitToScoreInput(input, digit) {
  if (!(input instanceof HTMLInputElement) || input.disabled) return;
  const currentValue = input.value === "0" ? "" : input.value.trim();
  input.value = `${currentValue}${digit}`.slice(0, 3);
  input.focus();
}

async function undoLastTurn() {
  if (!state.game || state.game.status !== "active") return;
  try {
    const response = await api(`/api/games/${state.game.id}/turn`, { method: "DELETE" });
    syncStateFromGame(response.game);
    renderGame();
    await loadHistory();
    showMessage("Last turn undone.");
  } catch (err) {
    showMessage(err.message, true);
  }
}

function setupScoreKeypad() {
  renderStandardScoreKeypad();

  document.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const button = target.closest(".score-key");
    if (!(button instanceof HTMLButtonElement)) return;

    const keypad = button.closest(".score-keypad");
    if (!(keypad instanceof HTMLElement) || button.disabled) return;

    const targetId = keypad.getAttribute("data-keypad-target");
    const input = targetId ? document.getElementById(targetId) : null;
    const digit = button.getAttribute("data-keypad-value");

    if (digit !== null) {
      appendDigitToScoreInput(input, digit);
      return;
    }

    const action = button.getAttribute("data-keypad-action");
    if (action === "backspace") {
      if (input instanceof HTMLInputElement) {
        input.value = input.value.slice(0, -1);
        input.focus();
      }
      return;
    }

    if (action === "undo") {
      await undoLastTurn();
      return;
    }

    if (action === "no-score") {
      if (input instanceof HTMLInputElement) {
        input.value = "0";
      }
      await submitScore(0);
      return;
    }

    if (action === "submit") {
      const total = Number(input instanceof HTMLInputElement ? input.value : 0);
      await submitScore(total);
    }
  });

  const turnTotalInput = document.getElementById("turn-total");
  if (turnTotalInput) {
    turnTotalInput.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        await submitScore(Number(turnTotalInput.value || 0));
      }
    });
  }
}

function confirmLogoutIfNeeded() {
  if (!state.game || state.game.status !== "active") {
    return true;
  }

  return window.confirm("Logging out will also quit the current game. Continue?");
}

async function logoutForInactivity() {
  if (idleLogoutInProgress) return;
  idleLogoutInProgress = true;

  try {
    await fetch("/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    // Ignore network issues and continue to the login screen.
  }

  window.location.assign("/login");
}

function resetInactivityTimer() {
  if (idleLogoutInProgress) return;

  if (inactivityLogoutTimeoutId) {
    window.clearTimeout(inactivityLogoutTimeoutId);
  }

  inactivityLogoutTimeoutId = window.setTimeout(() => {
    logoutForInactivity();
  }, SESSION_IDLE_TIMEOUT_MS);
}

function setHelpSection(sectionName) {
  if (!helpSections.length) return;

  const nextSection = helpSectionOrder.includes(sectionName)
    ? sectionName
    : helpSectionOrder[0];

  if (!nextSection) return;
  activeHelpSection = nextSection;

  helpSections.forEach((section) => {
    const isActive = section.getAttribute("data-help-section") === nextSection;
    section.classList.toggle("active", isActive);
  });

  if (helpNavEl) {
    helpNavEl.querySelectorAll("[data-help-section]").forEach((button) => {
      const isActive = button.getAttribute("data-help-section") === nextSection;
      button.classList.toggle("active", isActive);
    });
  }

  const currentIndex = helpSectionOrder.indexOf(nextSection);
  if (helpPrevEl) {
    helpPrevEl.disabled = currentIndex <= 0;
  }
  if (helpNextEl) {
    helpNextEl.textContent = currentIndex >= helpSectionOrder.length - 1 ? "Done" : "Next";
  }
}

function openHelpOverlay(sectionName = activeHelpSection) {
  if (!helpOverlayEl) return;
  setHelpSection(sectionName);
  helpOverlayEl.classList.add("visible");
}

function closeHelpOverlay() {
  if (!helpOverlayEl) return;
  helpOverlayEl.classList.remove("visible");
}

function stepHelpSection(direction) {
  if (!helpSectionOrder.length) return;

  const currentIndex = helpSectionOrder.indexOf(activeHelpSection);
  const nextIndex = Math.min(
    helpSectionOrder.length - 1,
    Math.max(0, currentIndex + direction),
  );

  if (direction > 0 && nextIndex === currentIndex && currentIndex === helpSectionOrder.length - 1) {
    closeHelpOverlay();
    return;
  }

  setHelpSection(helpSectionOrder[nextIndex]);
}

function renderAdminUsers(users) {
  if (!userAccountsListEl) return;

  if (!users.length) {
    userAccountsListEl.innerHTML = '<li class="hint">No user accounts found.</li>';
    return;
  }

  userAccountsListEl.innerHTML = users
    .map((user) => `
      <li class="admin-user-item">
        <div class="admin-user-meta">
          <strong>${user.username}</strong>
          <span class="admin-user-badges">
            ${user.is_admin ? '<span class="chip chip-static">Admin</span>' : '<span class="chip chip-static">User</span>'}
          </span>
        </div>
        <form class="admin-user-password-form" data-user-id="${user.id}">
          <input type="password" name="password" minlength="8" placeholder="New password" required />
          <button type="submit">Update Password</button>
        </form>
      </li>
    `)
    .join("");
}

async function loadAdminUsers() {
  if (!userAccountsListEl) return;
  const users = await api("/api/auth/users");
  renderAdminUsers(users);
}

async function submitScore(totalPoints) {
  const executeSubmission = async () => {
    if (!state.game || state.game.status !== "active") return;

    const numericTotal = Number.isFinite(Number(totalPoints)) ? Number(totalPoints) : 0;

    if (state.game.game_type === "55by5" && numericTotal % 5 !== 0) {
      showScoreWarningBanner("Total scored must be divisible by 5.");
    }

    try {
      const response = await api(`/api/games/${state.game.id}/turn`, {
        method: "POST",
        body: JSON.stringify({
          player_id: state.game.active_player_id,
          total_points: numericTotal,
        }),
      });
      syncStateFromGame(response.game);
      state.cricketPendingMarks = 0;
      state.cricketSelectedMarks = [];

      const turnTotalInput = document.getElementById("turn-total");
      if (turnTotalInput) {
        turnTotalInput.value = "";
      }
      const cricketBattingInput = document.getElementById("cricket-batting-total");
      if (cricketBattingInput) {
        cricketBattingInput.value = "";
      }

      if (response.game.status === "finished") {
        state.gameType = null;
        resetTeamNames();
      }

      renderGame();
      await loadHistory();

      if (response.game.status === "finished") {
        const winnerName = response.game.winner_team_name || response.game.players.find((p) => p.id === response.game.winner_player_id)?.name || "Tie";
        showWinnerOverlay(winnerName);
        return;
      }

      const t = response.turn;
      const isBust = response.game.game_type === "55by5" && !t.counted && t.total_points % 5 === 0;
      if (isBust) {
        const bustedPlayer = response.game.players.find((p) => p.id === t.player_id)?.name || "Player";
        showBustBanner(`${bustedPlayer} bust!`);
      }

      if (response.game.game_type === "english_cricket") {
        const resultLabel = t.counted
          ? t.total_points <= 6
            ? `${t.fives_awarded} wicket mark${t.fives_awarded === 1 ? "" : "s"}`
            : `${t.fives_awarded} run${t.fives_awarded === 1 ? "" : "s"}`
          : "no score";
        showMessage(
          t.counted
            ? `Cricket turn saved: ${resultLabel}.`
            : `Cricket turn saved: ${t.total_points} with no score.`
        );
        return;
      }

      if (response.game.game_type === "noughts_and_crosses") {
        showMessage(
          t.counted
            ? `${t.noughts_marker || "Move"} claimed ${t.board_label || `square ${t.board_index + 1}`}.`
            : `${t.board_label || "That square"} is already claimed.`
        );
        return;
      }

      showMessage(
        t.counted
          ? `Turn counted: ${t.total_points} points = +${t.fives_awarded} fives.`
          : isBust
            ? `Bust: ${t.total_points} would exceed 55 and does not count.`
            : `Turn not counted: ${t.total_points} is not divisible by 5.`
      );
    } catch (err) {
      showMessage(err.message, true);
    }
  };

  pendingTurnSubmission = pendingTurnSubmission.then(executeSubmission, executeSubmission);
  return pendingTurnSubmission;
}

async function submitNoughtsMove(cellIndex, marker) {
  const executeSubmission = async () => {
    if (!state.game || state.game.status !== "active") return;

    try {
      const response = await api(`/api/games/${state.game.id}/turn`, {
        method: "POST",
        body: JSON.stringify({
          player_id: state.game.active_player_id,
          total_points: cellIndex,
          noughts_marker: marker,
        }),
      });

      closeNoughtsMarkOverlay();
      syncStateFromGame(response.game);
      renderGame();
      await loadHistory();

      if (response.game.status === "finished") {
        const winnerName = response.game.winner_team_name || response.game.players.find((p) => p.id === response.game.winner_player_id)?.name || "Tie";
        showWinnerOverlay(winnerName);
        return;
      }

      const turn = response.turn;
      showMessage(
        turn.counted
          ? `${turn.noughts_marker || marker} claimed ${turn.board_label || `square ${cellIndex + 1}`}.`
          : `${turn.board_label || "That square"} is already claimed.`
      );
    } catch (err) {
      showMessage(err.message, true);
    }
  };

  pendingTurnSubmission = pendingTurnSubmission.then(executeSubmission, executeSubmission);
  return pendingTurnSubmission;
}

async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) {
    if (res.status === 401) {
      window.location.assign("/login");
    }
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function renderPlayers() {
  playersListEl.innerHTML = "";
  selectablePlayersEl.innerHTML = "";

  for (const player of state.players) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${player.name}</strong> <button data-delete-id="${player.id}">Delete</button>`;
    playersListEl.appendChild(li);

    const chip = document.createElement("label");
    chip.className = "chip";
    chip.innerHTML = `
      <input type="checkbox" data-select-id="${player.id}" ${
      state.selectedPlayerIds.has(player.id) ? "checked" : ""
    } />
      <span>${player.name}</span>
    `;
    selectablePlayersEl.appendChild(chip);
  }

  renderTeamAssignment();
}

function selectedGameName() {
  if (state.gameType === "english_cricket") return "English Cricket";
  if (state.gameType === "noughts_and_crosses") return "Noughts and Crosses";
  if (state.gameType === "55by5") return "55 by 5";
  return "";
}

function updateHeroCopy(game) {
  if (!heroTitleEl || !heroSubtitleEl) return;

  const activeGameType = game && game.status === "active" ? game.game_type : null;
  if (activeGameType === "55by5") {
    heroTitleEl.textContent = "55 by 5";
    heroSubtitleEl.textContent = "Score in multiples of 5 and reach exactly 55 fives to win the game.";
    return;
  }

  if (activeGameType === "english_cricket") {
    heroTitleEl.textContent = "English Cricket";
    heroSubtitleEl.textContent = "Batting scores runs above 40 while bowling hunts 10 bull hits to finish the innings.";
    return;
  }

  if (activeGameType === "noughts_and_crosses") {
    heroTitleEl.textContent = "Noughts and Crosses";
    heroSubtitleEl.textContent = "Click a dart target square and assign it to X or O to build three in a row.";
    return;
  }

  heroTitleEl.textContent = "Set Up Your Darts Game";
  heroSubtitleEl.textContent = "Pick your players, sort out teams and order, then choose a game to start scoring.";
}

function getTeamMode() {
  const checked = document.querySelector("input[name='team-mode']:checked");
  if (!(checked instanceof HTMLInputElement)) {
    return "solo";
  }
  return checked.value === "teams" ? "teams" : "solo";
}

function normalizeTeamNames(rawNames = {}) {
  const names = rawNames && typeof rawNames === "object" ? rawNames : {};
  const fallback = { team_a: "Team A", team_b: "Team B" };
  return {
    team_a: typeof names.team_a === "string" && names.team_a.trim() ? names.team_a.trim().slice(0, 40) : fallback.team_a,
    team_b: typeof names.team_b === "string" && names.team_b.trim() ? names.team_b.trim().slice(0, 40) : fallback.team_b,
  };
}

function setTeamNames(rawNames = state.teamNames, { syncInputs = true } = {}) {
  state.teamNames = normalizeTeamNames(rawNames);
  if (syncInputs && teamANameInputEl) {
    teamANameInputEl.value = state.teamNames.team_a;
  }
  if (syncInputs && teamBNameInputEl) {
    teamBNameInputEl.value = state.teamNames.team_b;
  }
  return state.teamNames;
}

function resetTeamNames() {
  setTeamNames({});
}

function syncStateFromGame(game) {
  state.game = game;
  state.pendingNoughtsCellIndex = null;
  if (!game) return;

  state.gameType = game.game_type || "55by5";
  state.teamMode = game.team_mode || "solo";
  state.teamAssignments = game.team_assignments || {};
  setTeamNames(game.team_names || {}, { syncInputs: true });
  state.cricketStartingBattingTeam = game.cricket_state?.starting_batting_team || game.cricket_state?.batting_team || "team_a";
}

function teamDisplayName(teamKey, rawNames = state.teamNames) {
  const names = normalizeTeamNames(rawNames);
  return teamKey === "team_b" ? names.team_b : names.team_a;
}

function oppositeTeam(teamKey) {
  return teamKey === "team_b" ? "team_a" : "team_b";
}

function getSelectedPlayersInOrder() {
  return state.orderedPlayerIds
    .map((id) => state.players.find((player) => player.id === id))
    .filter(Boolean);
}

function getCricketStartContext() {
  const selectedPlayers = getSelectedPlayersInOrder();

  if (state.teamMode === "teams") {
    syncTeamAssignments();
    const teamAPlayers = selectedPlayers.filter((player) => state.teamAssignments[player.id] === "team_a");
    const teamBPlayers = selectedPlayers.filter((player) => state.teamAssignments[player.id] === "team_b");

    if (!teamAPlayers.length || !teamBPlayers.length) {
      return {
        canStart: false,
        error: "Assign at least one player to each team before starting English Cricket.",
      };
    }

    const teamALabel = teamDisplayName("team_a");
    const teamBLabel = teamDisplayName("team_b");
    return {
      canStart: true,
      teamALabel,
      teamBLabel,
      chooserLabel: `${teamALabel} Will`,
    };
  }

  if (selectedPlayers.length !== 2) {
    return {
      canStart: false,
      error: "Select exactly two players or teams to play English Cricket.",
    };
  }

  const [firstPlayer, secondPlayer] = selectedPlayers;
  return {
    canStart: true,
    teamALabel: firstPlayer.name,
    teamBLabel: secondPlayer.name,
    chooserLabel: `${firstPlayer.name} Will`,
  };
}

function closeCricketStartOverlay() {
  if (cricketStartOverlayEl) {
    cricketStartOverlayEl.classList.remove("visible");
  }
}

function closeNoughtsMarkOverlay() {
  state.pendingNoughtsCellIndex = null;
  if (noughtsMarkOverlayEl) {
    noughtsMarkOverlayEl.classList.remove("visible");
  }
}

function openNoughtsMarkOverlay(cellIndex, label) {
  if (!noughtsMarkOverlayEl || !noughtsMarkPromptEl || !noughtsMarkOptionsEl || !state.game) return;

  const activePlayer = state.game.players.find((player) => player.id === state.game.active_player_id);
  const defaultMarker = activePlayer?.team === "team_b" ? "O" : "X";
  const noughtsState = state.game.noughts_and_crosses_state || {};
  const xName = noughtsState.x_name || "X";
  const oName = noughtsState.o_name || "O";

  state.pendingNoughtsCellIndex = cellIndex;
  noughtsMarkPromptEl.textContent = `Assign ${label} to:`;
  noughtsMarkOptionsEl.innerHTML = `
    <button type="button" class="noughts-mark-choice${defaultMarker === "X" ? " is-default" : ""}" data-noughts-mark="X">
      <strong>X</strong>
      <span>${xName}</span>
    </button>
    <button type="button" class="noughts-mark-choice${defaultMarker === "O" ? " is-default" : ""}" data-noughts-mark="O">
      <strong>O</strong>
      <span>${oName}</span>
    </button>
  `;

  noughtsMarkOptionsEl.querySelectorAll("[data-noughts-mark]").forEach((button) => {
    button.addEventListener("click", async () => {
      const marker = button.getAttribute("data-noughts-mark") || defaultMarker;
      await submitNoughtsMove(cellIndex, marker);
    });
  });

  noughtsMarkOverlayEl.classList.add("visible");
}

function renderCricketRoleSelection() {
  if (!cricketStartOverlayEl || !cricketStartPromptEl || !cricketStartOptionsEl) return;

  const show = state.gameType === "english_cricket";
  if (!show) {
    closeCricketStartOverlay();
    cricketStartPromptEl.textContent = "";
    cricketStartOptionsEl.innerHTML = "";
    return;
  }

  const context = getCricketStartContext();
  if (!context.canStart) {
    if (cricketStartOverlayEl.classList.contains("visible")) {
      closeCricketStartOverlay();
      showBustBanner(context.error);
    }
    cricketStartPromptEl.textContent = "";
    cricketStartOptionsEl.innerHTML = "";
    return;
  }

  const selectedChoice = state.cricketStartingBattingTeam === "team_b" ? "bowl" : "bat";
  cricketStartPromptEl.textContent = context.chooserLabel;
  cricketStartOptionsEl.innerHTML = `
    <label class="cricket-role-choice">
      <input
        type="radio"
        name="cricket-start-choice"
        value="bat"
        ${selectedChoice === "bat" ? "checked" : ""}
      />
      <span>
        <strong>Bat</strong>
      </span>
    </label>
    <label class="cricket-role-choice">
      <input
        type="radio"
        name="cricket-start-choice"
        value="bowl"
        ${selectedChoice === "bowl" ? "checked" : ""}
      />
      <span>
        <strong>Bowl</strong>
      </span>
    </label>
  `;

  cricketStartOptionsEl.querySelectorAll('input[name="cricket-start-choice"]').forEach((input) => {
    input.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) return;
      state.cricketStartingBattingTeam = target.value === "bowl" ? "team_b" : "team_a";
    });
  });
}

function openCricketStartOverlay() {
  const context = getCricketStartContext();
  if (!context.canStart) {
    showBustBanner(context.error);
    return false;
  }

  renderCricketRoleSelection();
  if (cricketStartOverlayEl) {
    cricketStartOverlayEl.classList.add("visible");
  }
  return true;
}

function syncTeamAssignments() {
  const selected = state.orderedPlayerIds;
  const selectedSet = new Set(selected);
  for (const key of Object.keys(state.teamAssignments)) {
    if (!selectedSet.has(Number(key))) {
      delete state.teamAssignments[key];
    }
  }

  let teamACount = 0;
  let teamBCount = 0;
  for (const id of selected) {
    const team = state.teamAssignments[id];
    if (team === "team_a") teamACount += 1;
    if (team === "team_b") teamBCount += 1;
  }

  for (const id of selected) {
    if (state.teamAssignments[id]) continue;
    if (teamACount <= teamBCount) {
      state.teamAssignments[id] = "team_a";
      teamACount += 1;
    } else {
      state.teamAssignments[id] = "team_b";
      teamBCount += 1;
    }
  }
}

function interleaveTeamOrder(teamAIds, teamBIds) {
  const ordered = [];
  const maxLen = Math.max(teamAIds.length, teamBIds.length);
  for (let index = 0; index < maxLen; index += 1) {
    if (index < teamAIds.length) {
      ordered.push(teamAIds[index]);
    }
    if (index < teamBIds.length) {
      ordered.push(teamBIds[index]);
    }
  }
  return ordered;
}

function updateOrderFromTeamLists() {
  if (!teamAListEl || !teamBListEl) return;
  const teamAIds = Array.from(teamAListEl.querySelectorAll("li"))
    .map((li) => Number(li.dataset.playerId))
    .filter(Boolean);
  const teamBIds = Array.from(teamBListEl.querySelectorAll("li"))
    .map((li) => Number(li.dataset.playerId))
    .filter(Boolean);

  for (const id of teamAIds) {
    state.teamAssignments[id] = "team_a";
  }
  for (const id of teamBIds) {
    state.teamAssignments[id] = "team_b";
  }

  state.orderedPlayerIds = interleaveTeamOrder(teamAIds, teamBIds);
  renderOrderList();
  renderCricketRoleSelection();
}

function renderTeamAssignment() {
  if (!teamAssignmentEl || !teamAListEl || !teamBListEl) return;
  const show = state.teamMode === "teams";
  setTeamNames(state.teamNames);
  teamAssignmentEl.classList.toggle("hidden", !show);
  if (orderSectionEl) {
    orderSectionEl.classList.toggle("hidden", show);
  }
  if (!show) {
    renderCricketRoleSelection();
    return;
  }

  syncTeamAssignments();
  teamAListEl.innerHTML = "";
  teamBListEl.innerHTML = "";

  for (const id of state.orderedPlayerIds) {
    const player = state.players.find((p) => p.id === id);
    if (!player) continue;
    const li = document.createElement("li");
    li.draggable = true;
    li.dataset.playerId = String(id);
    li.textContent = player.name;
    const team = state.teamAssignments[id] || "team_a";
    if (team === "team_b") {
      teamBListEl.appendChild(li);
    } else {
      teamAListEl.appendChild(li);
    }
  }

  updateOrderFromTeamLists();
  renderCricketRoleSelection();
}

function setupSortableLists(lists, onDrop) {
  let dragging = null;

  lists.forEach((list) => {
    if (!(list instanceof HTMLElement)) return;

    list.addEventListener("dragstart", (event) => {
      if (!(event.target instanceof HTMLElement)) return;
      dragging = event.target.closest("li");
      if (!dragging) return;
      dragging.classList.add("dragging");
    });

    list.addEventListener("dragend", (event) => {
      const target = event.target instanceof HTMLElement ? event.target.closest("li") : null;
      if (target) {
        target.classList.remove("dragging");
      }
      dragging = null;
    });

    list.addEventListener("dragover", (event) => {
      event.preventDefault();
      if (!dragging) return;

      const target = event.target instanceof HTMLElement ? event.target.closest("li") : null;
      if (!target || target === dragging) {
        if (event.currentTarget instanceof HTMLElement && event.target === event.currentTarget) {
          event.currentTarget.appendChild(dragging);
        }
        return;
      }

      const rect = target.getBoundingClientRect();
      const shouldInsertBefore = event.clientY < rect.top + rect.height / 2;
      list.insertBefore(dragging, shouldInsertBefore ? target : target.nextSibling);
    });

    list.addEventListener("drop", () => {
      if (typeof onDrop === "function") {
        onDrop(list);
      }
    });
  });
}

function setupTeamDragAndDrop() {
  if (!teamAListEl || !teamBListEl) return;

  setupSortableLists([teamAListEl, teamBListEl], (list) => {
    const teamName = list === teamBListEl ? "team_b" : "team_a";
    const ids = Array.from(list.querySelectorAll("li"))
      .map((li) => Number(li.dataset.playerId))
      .filter(Boolean);

    for (const id of ids) {
      state.teamAssignments[id] = teamName;
    }
    updateOrderFromTeamLists();
  });
}

function rebuildOrder() {
  const validSelection = new Set(state.selectedPlayerIds);
  const preservedOrder = state.orderedPlayerIds.filter((id) => validSelection.has(id));
  for (const id of validSelection) {
    if (!preservedOrder.includes(id)) {
      preservedOrder.push(id);
    }
  }
  state.orderedPlayerIds = preservedOrder;
  renderOrderList();
  renderTeamAssignment();
}

function renderOrderList() {
  orderListEl.innerHTML = "";
  const selectedPlayers = state.orderedPlayerIds
    .map((id) => state.players.find((p) => p.id === id))
    .filter(Boolean);

  selectedPlayers.forEach((player) => {
    const li = document.createElement("li");
    li.draggable = true;
    li.dataset.id = String(player.id);
    li.innerHTML = `<span>${player.name}</span><span>::</span>`;
    orderListEl.appendChild(li);
  });
}

function setupDragAndDrop() {
  setupSortableLists([orderListEl], (list) => {
    state.orderedPlayerIds = Array.from(list.querySelectorAll("li")).map((li) => Number(li.dataset.id));
    renderCricketRoleSelection();
  });
}

function groupPlayersByTeam(players) {
  return {
    team_a: players.filter((player) => player.team === "team_a"),
    team_b: players.filter((player) => player.team === "team_b"),
    unassigned: players.filter((player) => !player.team),
  };
}

function getCricketTeamInfo(game, teamKey, grouped, fallbackStart = 0) {
  const fallbackMembers = grouped.unassigned.slice(fallbackStart, fallbackStart + 1);
  const members = grouped[teamKey].length ? grouped[teamKey] : fallbackMembers;
  const teamName = teamDisplayName(teamKey, game.team_names);
  const memberNames = members.map((player) => player.name).join(", ") || "No players selected";
  const isTeamMode = game.team_mode === "teams";
  return {
    key: teamKey,
    teamName,
    members,
    memberNames,
    roleName: isTeamMode ? teamName : memberNames,
    title: isTeamMode ? memberNames : "",
    subtitle: "",
  };
}

function getCricketContext(game) {
  const cs = game.cricket_state || {};
  const grouped = groupPlayersByTeam(game.players);
  const battingTeam = cs.batting_team === "team_b" ? "team_b" : "team_a";
  const bowlingTeam = cs.bowling_team === "team_a" ? "team_a" : "team_b";
  const battingFallbackIndex = battingTeam === "team_b" ? 1 : 0;
  const bowlingFallbackIndex = bowlingTeam === "team_b" ? 1 : 0;
  const battingInfo = getCricketTeamInfo(game, battingTeam, grouped, battingFallbackIndex);
  const bowlingInfo = getCricketTeamInfo(game, bowlingTeam, grouped, bowlingFallbackIndex);
  const activePlayer = game.players.find((player) => player.id === game.active_player_id);
  const activeTeam = activePlayer?.team || battingTeam;
  return {
    cs,
    battingTeam,
    bowlingTeam,
    battingInfo,
    bowlingInfo,
    activePlayer,
    isBattingTurn: activeTeam === battingTeam && game.status === "active",
    isBowlingTurn: activeTeam === bowlingTeam && game.status === "active",
  };
}

function renderStandardScoreboard(game) {
  scoreboardEl.innerHTML = "";
  const players = [...game.players];
  if (game.team_mode === "teams") {
    const grouped = groupPlayersByTeam(players);
    for (const teamKey of ["team_a", "team_b"]) {
      const label = teamDisplayName(teamKey, game.team_names);
      const members = grouped[teamKey];
      if (!members.length) continue;
      const teamRow = document.createElement("tr");
      teamRow.className = "team-header-row";
      const teamTotal = members.reduce((sum, player) => sum + player.fives, 0);
      const teamRequired = Math.max((55 - teamTotal) * 5, 0);
      teamRow.innerHTML = `
        <td><strong>${label}</strong></td>
        <td><strong>${teamTotal}</strong></td>
        <td><strong>${teamRequired}</strong></td>
      `;
      scoreboardEl.appendChild(teamRow);

      for (const player of members) {
        const tr = document.createElement("tr");
        if (player.id === game.active_player_id && game.status === "active") {
          tr.classList.add("active-row");
        }
        const pointsRequired = Math.max((55 - player.fives) * 5, 0);
        tr.innerHTML = `
          <td class="scoreboard-member">${player.name}</td>
          <td>${player.fives}</td>
          <td>${pointsRequired}</td>
        `;
        scoreboardEl.appendChild(tr);
      }
    }
    return;
  }

  for (const player of players) {
    const tr = document.createElement("tr");
    if (player.id === game.active_player_id && game.status === "active") {
      tr.classList.add("active-row");
    }
    const pointsRequired = Math.max((55 - player.fives) * 5, 0);
    tr.innerHTML = `
      <td>${player.name}</td>
      <td>${player.fives}</td>
      <td>${pointsRequired}</td>
    `;
    scoreboardEl.appendChild(tr);
  }
}

function renderCricketDashboard(game) {
  if (!cricketDashboardEl || !cricketBowlingPanelEl || !cricketBattingPanelEl) return;

  const { cs, battingTeam, bowlingTeam, battingInfo, bowlingInfo, activePlayer, isBattingTurn, isBowlingTurn } = getCricketContext(game);
  const wickets = cs.wickets || {};
  const runs = cs.runs || {};
  const battingRuns = runs[battingTeam] || 0;
  const completedMarks = wickets[bowlingTeam] || 0;
  const targetRuns = cs.inning === 2 ? (runs[bowlingTeam] || 0) + 1 : null;
  const remainingRuns = targetRuns === null ? null : Math.max(targetRuns - battingRuns, 0);

  state.cricketSelectedMarks = (state.cricketSelectedMarks || []).filter(
    (slot) => Number.isFinite(slot) && slot > completedMarks && slot <= 10,
  );
  state.cricketPendingMarks = state.cricketSelectedMarks.length;

  const bullMarkup = Array.from({ length: 10 }, (_, index) => {
    const slot = index + 1;
    if (slot <= completedMarks) {
      return `<button type="button" class="bullseye-chip is-hit" disabled aria-label="Bullseye ${slot} already hit"></button>`;
    }

    const isSelected = state.cricketSelectedMarks.includes(slot);
    const interactive = isBowlingTurn;
    return `
      <button
        type="button"
        class="bullseye-chip${isSelected ? " is-selected" : ""}${interactive ? "" : " is-blocked"}"
        data-bowling-slot="${slot}"
        ${interactive ? "" : "disabled"}
        aria-label="Toggle wicket mark ${slot - completedMarks} for this throw"
      ></button>
    `;
  }).join("");

  cricketDashboardEl.classList.remove("hidden");
  cricketBowlingPanelEl.className = `cricket-side-panel${isBowlingTurn ? " is-active" : " is-inactive"}`;
  cricketBattingPanelEl.className = `cricket-side-panel${isBattingTurn ? " is-active" : " is-inactive"}`;

  cricketBowlingPanelEl.innerHTML = `
    <div class="cricket-panel-header">
      <div>
        <p class="cricket-role-tag"><span class="cricket-role-label">Bowling Side :</span> <span class="cricket-role-value">${bowlingInfo.roleName}</span></p>
        ${bowlingInfo.title ? `<h4>${bowlingInfo.title}</h4>` : ""}
        ${bowlingInfo.subtitle ? `<p class="hint">${bowlingInfo.subtitle}</p>` : ""}
      </div>
      <div class="cricket-score-pill">
        <span>Wickets</span>
        <strong>${completedMarks} / 10</strong>
      </div>
    </div>
    <div class="cricket-bull-grid" aria-label="Bowling wicket tracker">
      ${bullMarkup}
    </div>
    <div class="cricket-panel-actions">
      <button id="cricket-submit-bowling" type="button" ${isBowlingTurn ? "" : "disabled"}>Submit Bull Hits</button>
    </div>
  `;

  cricketBattingPanelEl.innerHTML = `
    <div class="cricket-panel-header">
      <div>
        <p class="cricket-role-tag"><span class="cricket-role-label">Batting Side :</span> <span class="cricket-role-value">${battingInfo.roleName}</span></p>
        ${battingInfo.title ? `<h4>${battingInfo.title}</h4>` : ""}
        ${battingInfo.subtitle ? `<p class="hint">${battingInfo.subtitle}</p>` : ""}
      </div>
      <div class="cricket-score-group">
        <div class="cricket-score-pill runs-pill">
          <span>Runs</span>
          <strong>${battingRuns}</strong>
        </div>
        ${targetRuns === null ? "" : `
          <div class="cricket-score-pill target-pill">
            <span>Target</span>
            <strong>${targetRuns}</strong>
          </div>
          <div class="cricket-score-pill remaining-pill">
            <span>Remaining Runs</span>
            <strong>${remainingRuns}</strong>
          </div>
        `}
      </div>
    </div>
    <div class="cricket-entry-stack">
      <label class="cricket-entry-field" for="cricket-batting-total">
        <span>Score</span>
        <input id="cricket-batting-total" type="number" inputmode="numeric" min="0" max="180" value="" ${isBattingTurn ? "" : "disabled"} />
      </label>
      <div
        id="cricket-batting-keypad"
        class="score-keypad cricket-score-keypad"
        data-keypad-target="cricket-batting-total"
        aria-label="Cricket batting keypad"
      >
        ${createScoreKeypadMarkup({
          submitButtonId: "cricket-submit-batting",
          noScoreButtonId: "cricket-no-score",
          disabled: !isBattingTurn,
          showUndo: false,
        })}
      </div>
    </div>
  `;

  cricketBowlingPanelEl.querySelectorAll("[data-bowling-slot]").forEach((button) => {
    button.addEventListener("click", () => {
      const slot = Number(button.getAttribute("data-bowling-slot"));
      if (!Number.isFinite(slot)) return;

      if (state.cricketSelectedMarks.includes(slot)) {
        state.cricketSelectedMarks = state.cricketSelectedMarks.filter((value) => value !== slot);
      } else {
        state.cricketSelectedMarks = [...state.cricketSelectedMarks, slot].sort((a, b) => a - b);
      }

      state.cricketPendingMarks = state.cricketSelectedMarks.length;
      const hiddenInput = document.getElementById("turn-total");
      if (hiddenInput) {
        hiddenInput.value = String(state.cricketPendingMarks);
      }
      renderCricketDashboard(game);
    });
  });

  const submitBowlingBtn = document.getElementById("cricket-submit-bowling");
  if (submitBowlingBtn) {
    submitBowlingBtn.addEventListener("click", async () => {
      if (state.cricketPendingMarks > 6) {
        showMessage("A bowling throw can score at most 6 wicket marks.", true);
        return;
      }
      await submitScore(state.cricketPendingMarks || 0);
    });
  }

  const battingInput = document.getElementById("cricket-batting-total");
  if (battingInput) {
    battingInput.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        await submitScore(Number(battingInput.value || 0));
      }
    });
  }
}

function renderNoughtsAndCrossesDashboard(game) {
  if (!noughtsDashboardEl) return;

  const noughtsState = game.noughts_and_crosses_state || { cells: [] };
  const cells = Array.isArray(noughtsState.cells) ? noughtsState.cells : [];
  const winningLine = new Set(Array.isArray(noughtsState.winning_line) ? noughtsState.winning_line : []);
  const xName = noughtsState.x_name || "X";
  const oName = noughtsState.o_name || "O";

  noughtsDashboardEl.classList.remove("hidden");
  noughtsDashboardEl.innerHTML = `
    <div class="noughts-status-card">
      <div class="noughts-side-pill noughts-side-pill-x">
        <strong>X</strong>
        <span>${xName}</span>
      </div>
      <div class="noughts-status-spacer" aria-hidden="true"></div>
      <div class="noughts-side-pill noughts-side-pill-o">
        <strong>O</strong>
        <span>${oName}</span>
      </div>
    </div>
    <div class="noughts-board" aria-label="Noughts and Crosses board">
      ${cells.map((cell, index) => {
        const mark = cell?.mark || "";
        const isClaimed = Boolean(mark);
        const isWinning = winningLine.has(index);
        return `
          <button
            type="button"
            class="noughts-cell${mark ? ` is-marked is-${mark.toLowerCase()}` : ""}${isWinning ? " is-winning" : ""}"
            data-board-index="${index}"
            ${game.status === "active" && !isClaimed ? "" : "disabled"}
            aria-label="${cell?.label || `Board square ${index + 1}`}${mark ? ` claimed by ${mark}` : ""}"
          >
            <span class="noughts-cell-label">${cell?.label || `Square ${index + 1}`}</span>
            <span class="noughts-cell-mark">${mark || "?"}</span>
          </button>
        `;
      }).join("")}
    </div>
  `;

  noughtsDashboardEl.querySelectorAll("[data-board-index]").forEach((button) => {
    button.addEventListener("click", () => {
      const cellIndex = Number(button.getAttribute("data-board-index"));
      const label = button.querySelector(".noughts-cell-label")?.textContent || `square ${cellIndex + 1}`;
      if (!Number.isFinite(cellIndex)) return;
      openNoughtsMarkOverlay(cellIndex, label);
    });
  });
}

function applyLayoutMode(game) {
  const activeMode = game && game.status === "active";

  updateHeroCopy(game);

  if (activeMode) {
    closeCricketStartOverlay();
    closeNoughtsMarkOverlay();
    if (gameSelectionPanelEl) {
      gameSelectionPanelEl.classList.add("hidden");
    }
    playersPanelEl.classList.add("hidden");
    setupPanelEl.classList.add("hidden");
    historyPanelEl.classList.add("hidden");
    livePanelEl.classList.remove("hidden");
    appShellEl.classList.add("game-mode");
    livePanelEl.classList.add("live-focus");
    return;
  }

  if (gameSelectionPanelEl) {
    gameSelectionPanelEl.classList.remove("hidden");
  }
  playersPanelEl.classList.remove("hidden");
  setupPanelEl.classList.remove("hidden");
  historyPanelEl.classList.remove("hidden");
  livePanelEl.classList.add("hidden");
  appShellEl.classList.remove("game-mode");
  livePanelEl.classList.remove("live-focus");

  if (selectedGameLabelEl) {
    if (!state.gameType || state.gameType === "english_cricket") {
      selectedGameLabelEl.textContent = "";
    } else {
      selectedGameLabelEl.textContent = `Selected game: ${selectedGameName()}.`;
    }
  }
}

function renderGame() {
  const game = state.game;
  applyLayoutMode(game);

  if (!game) {
    resetTeamNames();
    closeNoughtsMarkOverlay();
    if (cricketUndoTurnEl) {
      cricketUndoTurnEl.classList.add("hidden");
      cricketUndoTurnEl.disabled = true;
    }
    activeGameMetaEl.textContent = "No active game.";
    scoreboardEl.innerHTML = "";
    turnsListEl.innerHTML = "";
    turnInputEl.classList.add("hidden");
    if (standardTurnControlsEl) {
      standardTurnControlsEl.classList.remove("hidden");
    }
    if (cricketDashboardEl) {
      cricketDashboardEl.classList.add("hidden");
    }
    if (noughtsDashboardEl) {
      noughtsDashboardEl.classList.add("hidden");
    }
    if (scoreboardSectionEl) {
      scoreboardSectionEl.classList.remove("hidden");
    }
    return;
  }

  const isCricket = game.game_type === "english_cricket";
  const isNoughts = game.game_type === "noughts_and_crosses";
  const headers = Array.from(document.querySelectorAll("#scoreboard-table thead th"));
  if (headers.length >= 3) {
    headers[0].textContent = "Player";
    headers[1].textContent = "Score";
    headers[2].textContent = "Points Required";
  }

  if (standardTurnControlsEl) {
    standardTurnControlsEl.classList.toggle("hidden", isCricket || isNoughts || game.status !== "active");
  }
  if (sharedTurnActionsEl) {
    sharedTurnActionsEl.classList.toggle("hidden", game.status !== "active");
  }
  if (cricketUndoTurnEl) {
    const showUndo = game.status === "active";
    cricketUndoTurnEl.classList.toggle("hidden", !showUndo);
    cricketUndoTurnEl.disabled = !showUndo || !game.turns.length;
  }
  if (cricketDashboardEl) {
    cricketDashboardEl.classList.toggle("hidden", !isCricket);
  }
  if (noughtsDashboardEl) {
    noughtsDashboardEl.classList.toggle("hidden", !isNoughts);
  }
  if (scoreboardSectionEl) {
    scoreboardSectionEl.classList.toggle("hidden", isCricket || isNoughts);
  }

  const activePlayer = game.players.find((p) => p.id === game.active_player_id);
  if (game.status === "finished") {
    closeNoughtsMarkOverlay();
    const winnerName = game.winner_team_name || game.players.find((p) => p.id === game.winner_player_id)?.name || "Tie";
    activeGameMetaEl.innerHTML = `<strong>Winner: ${winnerName}</strong>`;
  } else if (isCricket) {
    activeGameMetaEl.innerHTML = `<strong class="current-player">${activePlayer?.name || "Unknown"} to Throw</strong>`;
  } else if (isNoughts) {
    activeGameMetaEl.innerHTML = "<strong>Noughts and Crosses</strong>";
  } else {
    activeGameMetaEl.innerHTML = `<strong class="current-player">${activePlayer?.name || "Unknown"} to Throw</strong>`;
  }

  if (isCricket) {
    renderCricketDashboard(game);
    scoreboardEl.innerHTML = "";
  } else if (isNoughts) {
    renderNoughtsAndCrossesDashboard(game);
    scoreboardEl.innerHTML = "";
  } else {
    renderStandardScoreboard(game);
  }

  turnsListEl.innerHTML = "";
  for (const turn of game.turns.slice().reverse()) {
    const li = document.createElement("li");
    const turnNote = isCricket
      ? (turn.counted
        ? `+${turn.fives_awarded} ${turn.total_points <= 6 ? "wicket marks" : "runs"}`
        : "no score")
      : isNoughts
        ? (turn.counted
          ? `${turn.noughts_marker || "Mark"} on ${turn.board_label || `square ${turn.board_index + 1}`}`
          : `${turn.board_label || "square"} already taken`)
        : turn.counted
          ? `+${turn.fives_awarded} fives`
          : turn.total_points % 5 === 0
            ? "bust"
            : "+0 fives";
    li.textContent = isNoughts
      ? `#${turn.turn_number} ${turn.player_name}: ${turnNote}`
      : `#${turn.turn_number} ${turn.player_name}: total ${turn.total_points} (${turnNote})`;
    turnsListEl.appendChild(li);
  }

  if (turnInputLabelEl && !isCricket) {
    turnInputLabelEl.textContent = "Total scored";
  }
  if (bullHitEl) {
    bullHitEl.classList.add("hidden");
  }

  const shouldShowTurnArea = isCricket || isNoughts || game.status === "active";
  turnInputEl.classList.toggle("hidden", !shouldShowTurnArea);
}

async function loadPlayers() {
  state.players = await api("/api/players");

  const validIds = new Set(state.players.map((p) => p.id));
  state.selectedPlayerIds = new Set(Array.from(state.selectedPlayerIds).filter((id) => validIds.has(id)));

  renderPlayers();
  rebuildOrder();
}

async function loadActiveGame() {
  const response = await api("/api/games/active");
  state.game = response.game;
  if (state.game) {
    syncStateFromGame(state.game);
  }
  renderGame();
}

async function loadHistory() {
  const games = await api("/api/games/history?limit=20");
  historyListEl.innerHTML = "";
  for (const game of games) {
    const li = document.createElement("li");
    const names = game.participants.map((p) => p.name).join(" -> ");
    const modeLabel = game.game_type === "english_cricket"
      ? "English Cricket"
      : game.game_type === "noughts_and_crosses"
        ? "Noughts and Crosses"
        : "55 by 5";
    const winner = game.winner_team_name || game.winner_name || "Unknown";
    li.textContent = `[${modeLabel}] Game #${game.id}: Winner ${winner}, ${game.turn_count} turns. Order: ${names}`;
    historyListEl.appendChild(li);
  }
}

async function loadAuthUser() {
  const user = await api("/api/auth/me");
  if (currentUserEl) {
    currentUserEl.textContent = `${user.username}${user.is_admin ? " (Admin)" : ""}`;
  }
  if (adminPanelEl) {
    const hidden = sessionStorage.getItem("adminPanelHidden") === "1";
    if (user.is_admin && !hidden) {
      adminPanelEl.classList.remove("hidden");
    } else {
      adminPanelEl.classList.add("hidden");
    }
  }
  const hideBtn = document.getElementById("hide-admin-panel");
  if (hideBtn) {
    hideBtn.addEventListener("click", () => {
      sessionStorage.setItem("adminPanelHidden", "1");
      adminPanelEl.classList.add("hidden");
    });
  }
  if (clearHistoryEl) {
    if (user.is_admin) {
      clearHistoryEl.classList.remove("hidden");
    } else {
      clearHistoryEl.classList.add("hidden");
    }
  }
  if (user.is_admin) {
    await loadAdminUsers();
  } else if (userAccountsListEl) {
    userAccountsListEl.innerHTML = "";
  }
}

async function startConfiguredGame() {
  if (!state.gameType) {
    showBustBanner("Choose a game mode first.");
    return;
  }
  if (state.orderedPlayerIds.length === 0) {
    showBustBanner("Select at least one player.");
    return;
  }

  state.teamMode = getTeamMode();
  let teamAssignments = undefined;
  if (state.teamMode === "teams") {
    syncTeamAssignments();
    updateOrderFromTeamLists();
    teamAssignments = {};
    for (const id of state.orderedPlayerIds) {
      teamAssignments[String(id)] = state.teamAssignments[id] || "team_a";
    }
  }

  if (state.gameType === "noughts_and_crosses" && state.teamMode === "solo" && state.orderedPlayerIds.length !== 2) {
    showBustBanner("Select exactly two players to play Noughts and Crosses.");
    return;
  }

  try {
    const response = await api("/api/games", {
      method: "POST",
      body: JSON.stringify({
        ordered_player_ids: state.orderedPlayerIds,
        game_type: state.gameType,
        team_mode: state.teamMode,
        team_assignments: teamAssignments,
        team_names: state.teamMode === "teams" ? normalizeTeamNames(state.teamNames) : undefined,
        starting_batting_team: state.gameType === "english_cricket" ? state.cricketStartingBattingTeam : undefined,
      }),
    });
    syncStateFromGame(response.game);
    renderGame();
    await loadHistory();
    showMessage("Game started.");
  } catch (err) {
    showBustBanner(err.message || "Unable to start game.");
    showMessage(err.message || "Unable to start game.", true);
  }
}

async function startRematch() {
  if (!state.game) {
    showMessage("No previous game to rematch.", true);
    return;
  }

  try {
    const finishedGame = state.game;
    const gameType = finishedGame.game_type;
    const teamMode = finishedGame.team_mode;
    const orderedPlayerIds = finishedGame.players.map((p) => p.id);
    
    // Determine new starting position
    let newOrderedPlayerIds = [...orderedPlayerIds];
    let newTeamAssignments = undefined;
    let newStartingBattingTeam = state.cricketStartingBattingTeam;

    if (teamMode === "teams") {
      // Swap team assignments for teams mode
      const swappedAssignments = {};
      finishedGame.players.forEach((player) => {
        const currentTeam = finishedGame.team_assignments?.[player.id] || "team_a";
        swappedAssignments[String(player.id)] = currentTeam === "team_a" ? "team_b" : "team_a";
      });
      newTeamAssignments = swappedAssignments;

      // For Cricket teams, also swap the batting team
      if (gameType === "english_cricket") {
        const currentBattingTeam = finishedGame.cricket_state?.starting_batting_team || "team_a";
        newStartingBattingTeam = currentBattingTeam === "team_a" ? "team_b" : "team_a";
      }
    } else {
      // For solo mode, rotate player order (move first to last)
      if (newOrderedPlayerIds.length > 1) {
        newOrderedPlayerIds = [...newOrderedPlayerIds.slice(1), newOrderedPlayerIds[0]];
      }
    }

    // Close winner overlay
    if (stopFireworks) { 
      stopFireworks(); 
      stopFireworks = null; 
    }
    if (winnerOverlayEl) {
      winnerOverlayEl.classList.remove("visible");
    }

    // Create rematch game
    const response = await api("/api/games", {
      method: "POST",
      body: JSON.stringify({
        ordered_player_ids: newOrderedPlayerIds,
        game_type: gameType,
        team_mode: teamMode,
        team_assignments: newTeamAssignments,
        team_names: teamMode === "teams" ? finishedGame.team_names : undefined,
        starting_batting_team: gameType === "english_cricket" ? newStartingBattingTeam : undefined,
      }),
    });

    syncStateFromGame(response.game);
    renderGame();
    await loadHistory();
    showMessage("Rematch started with swapped starting positions.");
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function init() {
  resetTeamNames();
  setupScoreKeypad();
  setupDragAndDrop();
  setupTeamDragAndDrop();
  await loadAuthUser();
  setHelpSection(activeHelpSection);
  resetInactivityTimer();

  ["click", "keydown", "mousedown", "mousemove", "scroll", "touchstart"].forEach((eventName) => {
    window.addEventListener(eventName, resetInactivityTimer, { passive: true });
  });

  const choose55Btn = document.getElementById("choose-55by5");
  const chooseCricketBtn = document.getElementById("choose-english-cricket");
  const chooseNoughtsBtn = document.getElementById("choose-noughts-and-crosses");
  const teamModeSoloEl = document.getElementById("team-mode-solo");
  const teamModeTeamsEl = document.getElementById("team-mode-teams");

  if (helpButtonEl) {
    helpButtonEl.addEventListener("click", () => {
      openHelpOverlay();
    });
  }

  if (helpCloseEl) {
    helpCloseEl.addEventListener("click", () => {
      closeHelpOverlay();
    });
  }

  if (helpNavEl) {
    helpNavEl.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      const sectionButton = target.closest("[data-help-section]");
      if (!(sectionButton instanceof HTMLElement)) return;
      setHelpSection(sectionButton.getAttribute("data-help-section") || activeHelpSection);
    });
  }

  if (helpPrevEl) {
    helpPrevEl.addEventListener("click", () => {
      stepHelpSection(-1);
    });
  }

  if (helpNextEl) {
    helpNextEl.addEventListener("click", () => {
      stepHelpSection(1);
    });
  }

  if (helpOverlayEl) {
    helpOverlayEl.addEventListener("click", (event) => {
      if (event.target === helpOverlayEl) {
        closeHelpOverlay();
      }
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (helpOverlayEl?.classList.contains("visible")) {
      closeHelpOverlay();
    }
    if (cricketStartOverlayEl?.classList.contains("visible")) {
      closeCricketStartOverlay();
    }
    if (noughtsMarkOverlayEl?.classList.contains("visible")) {
      closeNoughtsMarkOverlay();
    }
  });

  if (choose55Btn) {
    choose55Btn.addEventListener("click", async () => {
      closeCricketStartOverlay();
      state.gameType = "55by5";
      state.teamMode = getTeamMode();
      state.cricketStartingBattingTeam = "team_a";
      applyLayoutMode(state.game);
      renderTeamAssignment();
      try {
        await startConfiguredGame();
      } catch (err) {
        showMessage(err.message, true);
      }
    });
  }

  if (chooseCricketBtn) {
    chooseCricketBtn.addEventListener("click", () => {
      const wasSelected = state.gameType === "english_cricket";
      state.gameType = "english_cricket";
      state.teamMode = getTeamMode();
      if (!wasSelected) {
        state.cricketStartingBattingTeam = "team_a";
      }
      applyLayoutMode(state.game);
      renderTeamAssignment();
      openCricketStartOverlay();
    });
  }

  if (chooseNoughtsBtn) {
    chooseNoughtsBtn.addEventListener("click", async () => {
      closeCricketStartOverlay();
      closeNoughtsMarkOverlay();
      state.gameType = "noughts_and_crosses";
      state.teamMode = getTeamMode();
      applyLayoutMode(state.game);
      renderTeamAssignment();
      try {
        await startConfiguredGame();
      } catch (err) {
        showMessage(err.message, true);
      }
    });
  }

  if (cricketStartCancelEl) {
    cricketStartCancelEl.addEventListener("click", () => {
      closeCricketStartOverlay();
    });
  }

  if (cricketStartOverlayEl) {
    cricketStartOverlayEl.addEventListener("click", (event) => {
      if (event.target === cricketStartOverlayEl) {
        closeCricketStartOverlay();
      }
    });
  }

  if (noughtsMarkCancelEl) {
    noughtsMarkCancelEl.addEventListener("click", () => {
      closeNoughtsMarkOverlay();
    });
  }

  if (noughtsMarkOverlayEl) {
    noughtsMarkOverlayEl.addEventListener("click", (event) => {
      if (event.target === noughtsMarkOverlayEl) {
        closeNoughtsMarkOverlay();
      }
    });
  }

  if (cricketStartGameEl) {
    cricketStartGameEl.addEventListener("click", async () => {
      try {
        await startConfiguredGame();
      } catch (err) {
        showMessage(err.message, true);
      }
    });
  }

  for (const el of [teamModeSoloEl, teamModeTeamsEl]) {
    if (!(el instanceof HTMLInputElement)) continue;
    el.addEventListener("change", () => {
      state.teamMode = getTeamMode();
      renderTeamAssignment();
    });
  }

  for (const [inputEl, teamKey] of [[teamANameInputEl, "team_a"], [teamBNameInputEl, "team_b"]]) {
    if (!(inputEl instanceof HTMLInputElement)) continue;
    inputEl.addEventListener("input", () => {
      state.teamNames = {
        ...normalizeTeamNames(state.teamNames),
        [teamKey]: inputEl.value.trim().slice(0, 40) || teamDisplayName(teamKey),
      };
      renderCricketRoleSelection();
    });
    inputEl.addEventListener("blur", () => {
      state.teamNames = normalizeTeamNames({
        ...state.teamNames,
        [teamKey]: inputEl.value,
      });
      inputEl.value = teamDisplayName(teamKey);
      renderCricketRoleSelection();
    });
  }

  document.getElementById("player-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const nameInput = document.getElementById("player-name");
      const name = nameInput.value.trim();
      if (!name) return;
      await api("/api/players", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      nameInput.value = "";
      await loadPlayers();
      showMessage("Player added.");
    } catch (err) {
      showMessage(err.message, true);
    }
  });

  playersListEl.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const id = target.getAttribute("data-delete-id");
    if (!id) return;

    try {
      await api(`/api/players/${id}`, { method: "DELETE" });
      await loadPlayers();
      showMessage("Player deleted.");
    } catch (err) {
      showMessage(err.message, true);
    }
  });

  selectablePlayersEl.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    const id = Number(target.getAttribute("data-select-id"));
    if (!id) return;

    if (target.checked) {
      state.selectedPlayerIds.add(id);
    } else {
      state.selectedPlayerIds.delete(id);
    }
    rebuildOrder();
  });

  if (logoutFormEl) {
    logoutFormEl.addEventListener("submit", (event) => {
      if (confirmLogoutIfNeeded()) return;
      event.preventDefault();
    });
  }

  const createUserForm = document.getElementById("create-user-form");
  if (createUserForm) {
    createUserForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const username = document.getElementById("new-username").value.trim();
        const password = document.getElementById("new-password").value;
        const isAdmin = document.getElementById("new-is-admin").checked;
        await api("/api/auth/users", {
          method: "POST",
          body: JSON.stringify({ username, password, is_admin: isAdmin }),
        });
        createUserForm.reset();
        await loadAdminUsers();
        showMessage("User created.");
      } catch (err) {
        showMessage(err.message, true);
      }
    });
  }

  if (clearHistoryEl) {
    clearHistoryEl.addEventListener("click", async () => {
      const confirmed = window.confirm("Delete all recent finished game history?");
      if (!confirmed) return;
      try {
        const result = await api("/api/games/history", { method: "DELETE" });
        await loadHistory();
        showMessage(`Deleted ${result.deleted_games} game(s) from history.`);
      } catch (err) {
        showMessage(err.message, true);
      }
    });
  }

  if (userAccountsListEl) {
    userAccountsListEl.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;

      const userId = form.getAttribute("data-user-id");
      const passwordInput = form.querySelector('input[name="password"]');
      if (!userId || !(passwordInput instanceof HTMLInputElement)) return;

      try {
        await api(`/api/auth/users/${userId}/password`, {
          method: "PUT",
          body: JSON.stringify({ password: passwordInput.value }),
        });
        form.reset();
        showMessage("Password updated.");
      } catch (err) {
        showMessage(err.message, true);
      }
    });
  }

  if (bullHitEl) {
    bullHitEl.addEventListener("click", async () => {
      document.getElementById("turn-total").value = "1";
      await submitScore(1);
    });
  }

  if (cricketUndoTurnEl) {
    cricketUndoTurnEl.addEventListener("click", async () => {
      await undoLastTurn();
    });
  }

  document.getElementById("quit-game").addEventListener("click", async () => {
    if (!state.game || state.game.status !== "active") return;
    const confirmed = window.confirm("Quit this game? This will end the current game and cannot be undone.");
    if (!confirmed) return;

    try {
      await api(`/api/games/${state.game.id}`, { method: "DELETE" });
      if (stopFireworks) { stopFireworks(); stopFireworks = null; }
      if (winnerOverlayEl) {
        winnerOverlayEl.classList.remove("visible");
      }
      state.game = null;
      state.gameType = null;
      renderGame();
      await loadHistory();
      showMessage("Game quit.");
    } catch (err) {
      showMessage(err.message, true);
    }
  });

  const winnerContinueBtn = document.getElementById("winner-continue");
  if (winnerContinueBtn && winnerOverlayEl) {
    winnerContinueBtn.addEventListener("click", async () => {
      if (stopFireworks) { stopFireworks(); stopFireworks = null; }
      winnerOverlayEl.classList.remove("visible");
      state.game = null;
      state.gameType = null;
      renderGame();
      await loadHistory();
    });
  }

  const winnerRematchBtn = document.getElementById("winner-rematch");
  if (winnerRematchBtn) {
    winnerRematchBtn.addEventListener("click", async () => {
      await startRematch();
    });
  }

  await loadPlayers();
  await loadActiveGame();
  await loadHistory();
}

init().catch((err) => showMessage(err.message, true));
