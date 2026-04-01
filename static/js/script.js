const state = {
  players: [],
  selectedPlayerIds: new Set(),
  orderedPlayerIds: [],
  game: null,
  gameType: null,
  teamMode: "solo",
  teamAssignments: {},
};

const appShellEl = document.querySelector(".app-shell");
const playersPanelEl = document.getElementById("players-panel");
const gameSelectionPanelEl = document.getElementById("game-selection-panel");
const setupPanelEl = document.getElementById("setup-panel");
const livePanelEl = document.getElementById("live-panel");
const messageEl = document.getElementById("message");
const playersListEl = document.getElementById("players-list");
const selectablePlayersEl = document.getElementById("selectable-players");
const orderListEl = document.getElementById("order-list");
const activeGameMetaEl = document.getElementById("active-game-meta");
const scoreboardEl = document.getElementById("scoreboard");
const turnsListEl = document.getElementById("turns-list");
const historyListEl = document.getElementById("history-list");
const turnInputEl = document.getElementById("turn-input");
const quickBoardEl = document.getElementById("quick-board");
const selectedGameLabelEl = document.getElementById("selected-game-label");
const teamAssignmentEl = document.getElementById("team-assignment");
const teamAListEl = document.getElementById("team-a-list");
const teamBListEl = document.getElementById("team-b-list");
const turnInputLabelEl = document.getElementById("turn-input-label");
const historyPanelEl = document.getElementById("history-panel");
const winnerOverlayEl = document.getElementById("winner-overlay");
const bustBannerEl = document.getElementById("bust-banner");
const scoreWarningBannerEl = document.getElementById("score-warning-banner");
const currentUserEl = document.getElementById("current-user");
const adminPanelEl = document.getElementById("admin-panel");
const clearHistoryEl = document.getElementById("clear-history");

let bustBannerTimeoutId = null;
let scoreWarningTimeoutId = null;

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

async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) {
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
  if (state.gameType === "55by5") return "55 by 5";
  return "";
}

function getTeamMode() {
  const checked = document.querySelector("input[name='team-mode']:checked");
  if (!(checked instanceof HTMLInputElement)) {
    return "solo";
  }
  return checked.value === "teams" ? "teams" : "solo";
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

function renderTeamAssignment() {
  if (!teamAssignmentEl || !teamAListEl || !teamBListEl) return;
  const show = state.gameType && state.teamMode === "teams";
  teamAssignmentEl.classList.toggle("hidden", !show);
  if (!show) {
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
}

function setupTeamDragAndDrop() {
  if (!teamAListEl || !teamBListEl) return;
  let dragging = null;

  function attach(list, teamName) {
    list.addEventListener("dragstart", (event) => {
      if (!(event.target instanceof HTMLElement)) return;
      dragging = event.target;
      event.target.classList.add("dragging");
      event.target.dataset.teamTarget = teamName;
    });

    list.addEventListener("dragend", (event) => {
      if (!(event.target instanceof HTMLElement)) return;
      event.target.classList.remove("dragging");
      dragging = null;
    });

    list.addEventListener("dragover", (event) => {
      event.preventDefault();
      if (!dragging) return;
      list.appendChild(dragging);
    });

    list.addEventListener("drop", () => {
      const ids = Array.from(list.querySelectorAll("li"))
        .map((li) => Number(li.dataset.playerId))
        .filter(Boolean);
      for (const id of ids) {
        state.teamAssignments[id] = teamName;
      }
    });
  }

  attach(teamAListEl, "team_a");
  attach(teamBListEl, "team_b");
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
  let dragging = null;

  orderListEl.addEventListener("dragstart", (event) => {
    if (!(event.target instanceof HTMLElement)) return;
    dragging = event.target;
    event.target.classList.add("dragging");
  });

  orderListEl.addEventListener("dragend", (event) => {
    if (!(event.target instanceof HTMLElement)) return;
    event.target.classList.remove("dragging");
  });

  orderListEl.addEventListener("dragover", (event) => {
    event.preventDefault();
    const target = event.target.closest("li");
    if (!target || !dragging || target === dragging) return;

    const rect = target.getBoundingClientRect();
    const shouldInsertBefore = event.clientY < rect.top + rect.height / 2;
    orderListEl.insertBefore(dragging, shouldInsertBefore ? target : target.nextSibling);
  });

  orderListEl.addEventListener("drop", () => {
    const ids = Array.from(orderListEl.querySelectorAll("li")).map((li) => Number(li.dataset.id));
    state.orderedPlayerIds = ids;
  });
}

function renderQuickBoard() {
  const values = [0, 5, 10, 15, 20, 25, 30, 40, 45, 50, 60, 75, 100];
  quickBoardEl.innerHTML = "";
  values.forEach((value) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = String(value);
    button.addEventListener("click", () => {
      const input = document.getElementById("turn-total");
      input.value = String(value);
    });
    quickBoardEl.appendChild(button);
  });
}

function applyLayoutMode(game) {
  const activeMode = game && game.status === "active";

  if (activeMode) {
    gameSelectionPanelEl.classList.add("hidden");
    playersPanelEl.classList.add("hidden");
    setupPanelEl.classList.add("hidden");
    historyPanelEl.classList.add("hidden");
    livePanelEl.classList.remove("hidden");
    appShellEl.classList.add("game-mode");
    livePanelEl.classList.add("live-focus");
    return;
  }

  const choosingGame = !state.gameType;
  gameSelectionPanelEl.classList.toggle("hidden", !choosingGame);
  playersPanelEl.classList.toggle("hidden", choosingGame);
  setupPanelEl.classList.toggle("hidden", choosingGame);
  historyPanelEl.classList.remove("hidden");
  livePanelEl.classList.add("hidden");
  appShellEl.classList.remove("game-mode");
  livePanelEl.classList.remove("live-focus");

  if (selectedGameLabelEl) {
    selectedGameLabelEl.textContent = state.gameType
      ? `Selected game: ${selectedGameName()}`
      : "";
  }
}

function renderGame() {
  const game = state.game;
  applyLayoutMode(game);

  if (!game) {
    activeGameMetaEl.textContent = "No active game.";
    scoreboardEl.innerHTML = "";
    turnsListEl.innerHTML = "";
    turnInputEl.classList.add("hidden");
    return;
  }

  const headers = Array.from(document.querySelectorAll("thead th"));
  if (headers.length >= 3) {
    if (game.game_type === "english_cricket") {
      headers[0].textContent = "Player";
      headers[1].textContent = "Contribution";
      headers[2].textContent = "Team";
    } else {
      headers[0].textContent = "Player";
      headers[1].textContent = "Score";
      headers[2].textContent = "Points Required";
    }
  }

  const activePlayer = game.players.find((p) => p.id === game.active_player_id);
  if (game.status === "finished") {
    const winnerName = game.winner_team_name || game.players.find((p) => p.id === game.winner_player_id)?.name || "Tie";
    activeGameMetaEl.innerHTML = `<strong>Winner: ${winnerName}</strong>`;
  } else {
    if (game.game_type === "english_cricket") {
      const cs = game.cricket_state || {};
      const inning = cs.inning || 1;
      const battingTeam = cs.batting_team === "team_b" ? "Team B" : "Team A";
      const bowlingTeam = cs.bowling_team === "team_b" ? "Team B" : "Team A";
      const wickets = cs.wickets || {};
      const runs = cs.runs || {};
      activeGameMetaEl.innerHTML = `<strong class="current-player">${activePlayer?.name || "Unknown"} to Throw</strong><br/>Inning ${inning}: ${battingTeam} batting (${runs.team_a || 0}-${runs.team_b || 0} runs), ${bowlingTeam} bowling (${wickets.team_a || 0}/${wickets.team_b || 0} wicket marks)`;
    } else {
      activeGameMetaEl.innerHTML = `<strong class="current-player">${activePlayer?.name || "Unknown"} to Throw</strong>`;
    }
  }

  scoreboardEl.innerHTML = "";
  for (const player of game.players) {
    const tr = document.createElement("tr");
    if (player.id === game.active_player_id && game.status === "active") {
      tr.classList.add("active-row");
    }
    const pointsRequired = Math.max((55 - player.fives) * 5, 0);
    const teamName = player.team === "team_b" ? "Team B" : "Team A";
    tr.innerHTML = `
      <td>${player.name}</td>
      <td>${player.fives}</td>
      <td>${game.game_type === "english_cricket" ? teamName : pointsRequired}</td>
    `;
    scoreboardEl.appendChild(tr);
  }

  turnsListEl.innerHTML = "";
  for (const turn of game.turns.slice().reverse()) {
    const li = document.createElement("li");
    const turnNote = game.game_type === "english_cricket"
      ? (turn.counted ? `+${turn.fives_awarded}` : "no score")
      : turn.counted
        ? `+${turn.fives_awarded} fives`
        : turn.total_points % 5 === 0
          ? "bust"
          : "+0 fives";
    li.textContent = `#${turn.turn_number} ${turn.player_name}: total ${turn.total_points} (${turnNote})`;
    turnsListEl.appendChild(li);
  }

  if (game.status === "active") {
    turnInputEl.classList.remove("hidden");
    if (turnInputLabelEl) {
      if (game.game_type === "english_cricket") {
        const cs = game.cricket_state || {};
        const battingTeam = cs.batting_team || "team_a";
        const activeTeam = activePlayer?.team || "team_a";
        turnInputLabelEl.textContent = activeTeam === battingTeam
          ? "Batting Turn Total (runs from score above 40)"
          : "Bowling Bull Marks (0-10)";
      } else {
        turnInputLabelEl.textContent = "Total scored";
      }
    }
  } else {
    turnInputEl.classList.add("hidden");
  }
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
    state.gameType = state.game.game_type || "55by5";
    state.teamMode = state.game.team_mode || "solo";
    state.teamAssignments = state.game.team_assignments || {};
  }
  renderGame();
}

async function loadHistory() {
  const games = await api("/api/games/history?limit=20");
  historyListEl.innerHTML = "";
  for (const game of games) {
    const li = document.createElement("li");
    const names = game.participants.map((p) => p.name).join(" -> ");
    const modeLabel = game.game_type === "english_cricket" ? "English Cricket" : "55 by 5";
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
}

async function init() {
  renderQuickBoard();
  setupDragAndDrop();
  setupTeamDragAndDrop();
  await loadAuthUser();

  const choose55Btn = document.getElementById("choose-55by5");
  const chooseCricketBtn = document.getElementById("choose-english-cricket");
  const changeGameBtn = document.getElementById("change-game");
  const teamModeSoloEl = document.getElementById("team-mode-solo");
  const teamModeTeamsEl = document.getElementById("team-mode-teams");

  if (choose55Btn) {
    choose55Btn.addEventListener("click", () => {
      state.gameType = "55by5";
      state.teamMode = getTeamMode();
      applyLayoutMode(state.game);
      renderTeamAssignment();
    });
  }

  if (chooseCricketBtn) {
    chooseCricketBtn.addEventListener("click", () => {
      state.gameType = "english_cricket";
      state.teamMode = getTeamMode();
      applyLayoutMode(state.game);
      renderTeamAssignment();
    });
  }

  if (changeGameBtn) {
    changeGameBtn.addEventListener("click", () => {
      state.gameType = null;
      state.teamAssignments = {};
      applyLayoutMode(state.game);
    });
  }

  for (const el of [teamModeSoloEl, teamModeTeamsEl]) {
    if (!(el instanceof HTMLInputElement)) continue;
    el.addEventListener("change", () => {
      state.teamMode = getTeamMode();
      renderTeamAssignment();
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

  document.getElementById("start-game").addEventListener("click", async () => {
    try {
      if (!state.gameType) {
        showMessage("Choose a game mode first.", true);
        return;
      }
      if (state.orderedPlayerIds.length === 0) {
        showMessage("Select at least one player.", true);
        return;
      }

      state.teamMode = getTeamMode();
      let teamAssignments = undefined;
      if (state.teamMode === "teams") {
        syncTeamAssignments();
        teamAssignments = {};
        for (const id of state.orderedPlayerIds) {
          teamAssignments[String(id)] = state.teamAssignments[id] || "team_a";
        }
      }

      const response = await api("/api/games", {
        method: "POST",
        body: JSON.stringify({
          ordered_player_ids: state.orderedPlayerIds,
          game_type: state.gameType,
          team_mode: state.teamMode,
          team_assignments: teamAssignments,
        }),
      });
      state.game = response.game;
      state.gameType = response.game.game_type;
      state.teamMode = response.game.team_mode || "solo";
      renderGame();
      await loadHistory();
      showMessage("Game started.");
    } catch (err) {
      showMessage(err.message, true);
    }
  });

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

  async function submitScore(totalPoints) {
    if (!state.game || state.game.status !== "active") return;

    if (state.game.game_type !== "english_cricket" && totalPoints % 5 !== 0) {
      showScoreWarningBanner("Total scored must be divisible by 5.");
    }

    try {
      const response = await api(`/api/games/${state.game.id}/turn`, {
        method: "POST",
        body: JSON.stringify({
          player_id: state.game.active_player_id,
          total_points: totalPoints,
        }),
      });
      state.game = response.game;
      document.getElementById("turn-total").value = "";
      if (response.game.status === "finished") {
        const winnerName = response.game.winner_team_name || response.game.players.find((p) => p.id === response.game.winner_player_id)?.name || "Tie";
        showWinnerOverlay(winnerName);
      } else {
        renderGame();
        await loadHistory();
        const t = response.turn;
        const isBust = response.game.game_type !== "english_cricket" && !t.counted && t.total_points % 5 === 0;
        if (isBust) {
          const bustedPlayer = response.game.players.find((p) => p.id === t.player_id)?.name || "Player";
          showBustBanner(`${bustedPlayer} bust!`);
        }
        showMessage(
          t.counted
            ? `Turn counted: ${t.total_points} points = +${t.fives_awarded} fives.`
            : isBust
              ? `Bust: ${t.total_points} would exceed 55 and does not count.`
              : `Turn not counted: ${t.total_points} is not divisible by 5.`
        );
      }
    } catch (err) {
      showMessage(err.message, true);
    }
  }

  document.getElementById("submit-turn").addEventListener("click", async () => {
    const totalPoints = Number(document.getElementById("turn-total").value);
    await submitScore(totalPoints);
  });

  document.getElementById("no-score").addEventListener("click", async () => {
    document.getElementById("turn-total").value = "0";
    await submitScore(0);
  });

  document.getElementById("undo-turn").addEventListener("click", async () => {
    if (!state.game || state.game.status !== "active") return;
    try {
      const response = await api(`/api/games/${state.game.id}/turn`, { method: "DELETE" });
      state.game = response.game;
      renderGame();
      await loadHistory();
      showMessage("Last turn undone.");
    } catch (err) {
      showMessage(err.message, true);
    }
  });

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
      renderGame();
      await loadHistory();
    });
  }

  await loadPlayers();
  await loadActiveGame();
  await loadHistory();
}

init().catch((err) => showMessage(err.message, true));
