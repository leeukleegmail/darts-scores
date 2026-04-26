const state = {
  players: [],
  currentUser: null,
  playerSelectionSearch: "",
  playerManagerSearch: "",
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
  x01StartingScore: 501,
  pendingNoughtsCellIndex: null,
  playerStats: null,
  loadingPlayerStatsId: null,
  expandedAdminUserIds: new Set(),
  x01CheckoutAnnouncementKey: null,
  audioMuted: true,
};

const appShellEl = document.querySelector(".app-shell");
const heroTitleEl = document.getElementById("hero-title");
const heroSubtitleEl = document.getElementById("hero-subtitle");
const gameSelectionPanelEl = document.getElementById("game-selection-panel");
const setupPanelEl = document.getElementById("setup-panel");
const livePanelEl = document.getElementById("live-panel");
const messageEl = document.getElementById("message");
const playersListEl = document.getElementById("players-list");
const playerManagerOverlayEl = document.getElementById("player-manager-overlay");
const playerManagerOpenEl = document.getElementById("player-manager-open");
const playerManagerCloseEl = document.getElementById("player-manager-close");
const playerStatsOverlayEl = document.getElementById("player-stats-overlay");
const playerStatsPanelEl = document.getElementById("player-stats-panel");
const playerSelectionSearchEl = document.getElementById("player-selection-search");
const playerManagerSearchEl = document.getElementById("player-manager-search");
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
const x01StartOverlayEl = document.getElementById("x01-start-overlay");
const x01StartGameEl = document.getElementById("x01-start-game");
const x01StartCancelEl = document.getElementById("x01-start-cancel");
const x01TurnPanelEl = document.getElementById("x01-turn-panel");
const x01ActiveRemainingEl = document.getElementById("x01-active-remaining");
const x01CheckoutHintEl = document.getElementById("x01-checkout-hint");
const turnPlayerPanelEl = document.getElementById("turn-player-panel");
const turnPlayerNameEl = document.getElementById("turn-player-name");
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
const muteButtonEl = document.getElementById("mute-button");
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
const LOBBY_AVAILABILITY_REFRESH_MS = 2500;
const MAX_SCOREPAD_TOTAL = 180;

let bustBannerTimeoutId = null;
let scoreWarningTimeoutId = null;
let pendingTurnSubmission = Promise.resolve();
let activeHelpSection = helpSectionOrder[0] || "quick-start";
let inactivityLogoutTimeoutId = null;
let idleLogoutInProgress = false;
let lobbyAvailabilityIntervalId = null;
let lobbyAvailabilityRefreshInFlight = false;
let preferredSpeechVoice = null;
let speechContextUnlocked = false;
let sfxAudioContext = null;
const BUST_SOUND_FILE_URL = "/static/assets/sfx/bust.mp3";
const BUST_POST_SOUND_DELAY_MS = 150;
let bustSoundFilePlayable = null;
let bustSoundFileChecked = false;

const SPEECH_PREFERRED_UK_PATTERNS = [
  /yorkshire/i,
  /uk english/i,
  /google uk english/i,
  /en-gb/i,
];

const SPEECH_PREFERRED_MALE_PATTERNS = [
  /male/i,
  /man/i,
  /daniel/i,
  /arthur/i,
  /thomas/i,
  /george/i,
  /fred/i,
  /gordon/i,
  /lee/i,
];

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

function playGeneratedBustSound() {
  const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextCtor) return 0;

  try {
    if (!sfxAudioContext) {
      sfxAudioContext = new AudioContextCtor();
    }
    if (sfxAudioContext.state === "suspended") {
      sfxAudioContext.resume();
    }

    const now = sfxAudioContext.currentTime + 0.01;
    const notes = [230, 185, 145];
    notes.forEach((freq, index) => {
      const start = now + (index * 0.13);
      const end = start + 0.16;
      const osc = sfxAudioContext.createOscillator();
      const gain = sfxAudioContext.createGain();

      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(freq, start);
      osc.frequency.exponentialRampToValueAtTime(Math.max(95, freq * 0.7), end);

      gain.gain.setValueAtTime(0.0001, start);
      gain.gain.exponentialRampToValueAtTime(0.18, start + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, end);

      osc.connect(gain);
      gain.connect(sfxAudioContext.destination);
      osc.start(start);
      osc.stop(end + 0.01);
    });
    return 460;
  } catch (_err) {
    // Ignore audio errors and continue without SFX.
    return 0;
  }
}

function ensureBustSoundFile() {
  if (bustSoundFileChecked) {
    return bustSoundFilePlayable;
  }

  bustSoundFileChecked = true;
  try {
    const candidate = new Audio(BUST_SOUND_FILE_URL);
    candidate.preload = "auto";
    const canPlay = candidate.canPlayType("audio/wav") || candidate.canPlayType("audio/mpeg") || candidate.canPlayType("audio/ogg");
    if (canPlay) {
      bustSoundFilePlayable = candidate;
    }
  } catch (_err) {
    bustSoundFilePlayable = null;
  }

  return bustSoundFilePlayable;
}

function playBustSound() {
  if (state.audioMuted) {
    return Promise.resolve();
  }

  const audio = ensureBustSoundFile();
  if (audio) {
    return new Promise((resolve) => {
      let finished = false;
      const resolveOnce = () => {
        if (finished) return;
        finished = true;
        audio.removeEventListener("ended", onEnded);
        audio.removeEventListener("error", onError);
        resolve();
      };
      const onEnded = () => {
        resolveOnce();
      };
      const onError = () => {
        const fallbackMs = playGeneratedBustSound();
        if (fallbackMs > 0) {
          window.setTimeout(resolveOnce, fallbackMs);
          return;
        }
        resolveOnce();
      };

      audio.addEventListener("ended", onEnded, { once: true });
      audio.addEventListener("error", onError, { once: true });

      try {
        audio.currentTime = 0;
        const playAttempt = audio.play();
        if (playAttempt && typeof playAttempt.catch === "function") {
          playAttempt.catch(() => {
            onError();
          });
        }
      } catch (_err) {
        onError();
      }
    });
  }

  const fallbackMs = playGeneratedBustSound();
  return new Promise((resolve) => {
    if (fallbackMs > 0) {
      window.setTimeout(resolve, fallbackMs);
      return;
    }
    resolve();
  });
}

function delay(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
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

function updateMuteButtonLabel() {
  if (!muteButtonEl) return;
  const muted = Boolean(state.audioMuted);
  muteButtonEl.textContent = muted ? "Unmute" : "Mute";
  muteButtonEl.setAttribute("aria-pressed", muted ? "true" : "false");
}

function primeSpeechSynthesisIfNeeded() {
  // iOS (Safari and Chrome/WKWebView) blocks speechSynthesis.speak() from async
  // callbacks unless the context has been unlocked by a synchronous user-gesture
  // call. Speaking a silent utterance inside a touch/click handler primes it.
  if (speechContextUnlocked || typeof window.speechSynthesis === "undefined") return;
  try {
    const primer = new SpeechSynthesisUtterance("");
    primer.volume = 0;
    window.speechSynthesis.speak(primer);
    speechContextUnlocked = true;
  } catch (_err) {
    // Ignore — best-effort unlock only.
  }
}

function applyAudioMuted(muted) {
  state.audioMuted = Boolean(muted);
  if (!state.audioMuted) {
    primeSpeechSynthesisIfNeeded();
  }
  if (state.audioMuted) {
    if (typeof window.speechSynthesis !== "undefined") {
      window.speechSynthesis.cancel();
    }
    if (bustSoundFilePlayable) {
      try {
        bustSoundFilePlayable.pause();
        bustSoundFilePlayable.currentTime = 0;
      } catch (_err) {
        // Ignore playback reset errors while muting.
      }
    }
  }
  updateMuteButtonLabel();
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
}

function isOverScorepadLimit(input) {
  if (!(input instanceof HTMLInputElement)) return false;
  const raw = input.value.trim();
  if (!raw) return false;
  const numeric = Number(raw);
  return Number.isFinite(numeric) && numeric > MAX_SCOREPAD_TOTAL;
}

function refreshScorepadSubmitDisabled(keypad, input) {
  if (!(keypad instanceof HTMLElement)) return;
  const submitButton = keypad.querySelector('[data-keypad-action="submit"]');
  if (!(submitButton instanceof HTMLButtonElement)) return;
  if (submitButton.dataset.baseDisabled === "true") {
    submitButton.disabled = true;
    return;
  }
  submitButton.disabled = isOverScorepadLimit(input);
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
      refreshScorepadSubmitDisabled(keypad, input);
      return;
    }

    const action = button.getAttribute("data-keypad-action");
    if (action === "backspace") {
      if (input instanceof HTMLInputElement) {
        input.value = input.value.slice(0, -1);
      }
      refreshScorepadSubmitDisabled(keypad, input);
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
      refreshScorepadSubmitDisabled(keypad, input);
      primeSpeechSynthesisIfNeeded();
      await submitScore(0);
      return;
    }

    if (action === "submit") {
      if (isOverScorepadLimit(input)) {
        refreshScorepadSubmitDisabled(keypad, input);
        return;
      }
      const total = Number(input instanceof HTMLInputElement ? input.value : 0);
      primeSpeechSynthesisIfNeeded();
      await submitScore(total);
    }
  });

  document.querySelectorAll(".score-keypad").forEach((keypad) => {
    if (!(keypad instanceof HTMLElement)) return;
    const submitButton = keypad.querySelector('[data-keypad-action="submit"]');
    if (!(submitButton instanceof HTMLButtonElement)) return;
    submitButton.dataset.baseDisabled = submitButton.disabled ? "true" : "false";

    const targetId = keypad.getAttribute("data-keypad-target");
    const input = targetId ? document.getElementById(targetId) : null;
    if (input instanceof HTMLInputElement) {
      const update = () => refreshScorepadSubmitDisabled(keypad, input);
      input.addEventListener("input", update);
      input.addEventListener("change", update);
      update();
    }
  });

  const turnTotalInput = document.getElementById("turn-total");
  if (turnTotalInput) {
    turnTotalInput.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        if (isOverScorepadLimit(turnTotalInput)) return;
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

function openPlayerManager() {
  if (!playerManagerOverlayEl) return;
  playerManagerOverlayEl.classList.add("visible");
}

function closePlayerManager() {
  if (!playerManagerOverlayEl) return;
  playerManagerOverlayEl.classList.remove("visible");
}

function closeHelpOverlay() {
  if (!helpOverlayEl) return;
  helpOverlayEl.classList.remove("visible");
}

function closePlayerStats() {
  state.playerStats = null;
  state.loadingPlayerStatsId = null;
  if (playerStatsOverlayEl) {
    playerStatsOverlayEl.classList.remove("visible");
  }
  renderPlayers();
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
        <button
          type="button"
          class="admin-user-toggle"
          data-admin-user-toggle="${user.id}"
          aria-expanded="${state.expandedAdminUserIds.has(user.id) ? "true" : "false"}"
        >
          <span class="admin-user-meta">
            <strong>${user.username}</strong>
            <span class="admin-user-badges">
              ${user.is_admin ? '<span class="chip chip-static">Admin</span>' : '<span class="chip chip-static">User</span>'}
            </span>
          </span>
          <span class="admin-user-toggle-icon" aria-hidden="true">${state.expandedAdminUserIds.has(user.id) ? "−" : "+"}</span>
        </button>
        <div class="admin-user-details${state.expandedAdminUserIds.has(user.id) ? "" : " hidden"}">
          <form class="admin-user-password-form" data-user-id="${user.id}">
            <input type="password" name="password" minlength="8" placeholder="New password" required />
            <button type="submit">Update Password</button>
          </form>
        </div>
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
      resetX01TurnFlags();

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
      const t = response.turn;
      const is55By5Bust = response.game.game_type === "55by5" && !t.counted && t.total_points % 5 === 0;
      const isX01Bust = response.game.game_type === "x01"
        && (t.x01_result === "bust_overshoot" || t.x01_result === "bust_leave_one");

      if (is55By5Bust || isX01Bust) {
        showBustBanner("Bust");
        if (isX01Bust) {
          resetX01TurnFlags();
        }
        await playBustSound();
        await delay(BUST_POST_SOUND_DELAY_MS);
      }

      renderGame();
      await loadHistory();

      if (response.game.status === "finished") {
        const winnerName = winnerDisplayName(response.game, "Tie");
        showWinnerOverlay(winnerName);
        return;
      }

      if (is55By5Bust || isX01Bust) {
        return;
      }

      if (response.game.game_type === "x01") {
        const activePlayer = response.game.players.find((player) => player.id === t.player_id);
        const remaining = activePlayer?.x01_remaining ?? activePlayer?.fives ?? 0;
        announceX01TurnResult(t, response.game);
        resetX01TurnFlags();
        announceX01CheckoutIfNeeded(response.game);
        showMessage(
          t.counted
            ? `Turn saved: ${t.total_points} scored, ${remaining} remaining.`
            : `Turn saved: ${t.total_points} with no change.`,
        );
        return;
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
        const winnerName = winnerDisplayName(response.game, "Tie");
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
  if (state.playerStats && !state.players.some((player) => player.id === state.playerStats.player.id)) {
    state.playerStats = null;
  }

  const availablePlayerIds = new Set(
    state.players.filter((player) => !player.is_busy).map((player) => player.id)
  );
  state.selectedPlayerIds = new Set(
    [...state.selectedPlayerIds].filter((playerId) => availablePlayerIds.has(playerId))
  );
  state.orderedPlayerIds = state.orderedPlayerIds.filter((playerId) => availablePlayerIds.has(playerId));
  Object.keys(state.teamAssignments).forEach((playerId) => {
    if (!availablePlayerIds.has(Number(playerId))) {
      delete state.teamAssignments[playerId];
    }
  });

  playersListEl.innerHTML = "";
  selectablePlayersEl.innerHTML = "";
  const selectedStatsId = state.playerStats?.player?.id ?? state.loadingPlayerStatsId;
  const managerSearch = state.playerManagerSearch.trim().toLowerCase();

  const filteredSelectablePlayers = state.players
    .filter((player) => {
      const search = state.playerSelectionSearch.trim().toLowerCase();
      if (!search) return true;
      return player.name.toLowerCase().includes(search);
    })
    .sort((left, right) => {
      const leftName = left.name.toLowerCase();
      const rightName = right.name.toLowerCase();
      if (left.is_busy !== right.is_busy) {
        return Number(left.is_busy) - Number(right.is_busy);
      }
      return leftName.localeCompare(rightName);
    });

  const showDeleteButton = Boolean(state.currentUser?.is_admin);

  const filteredManagerPlayers = state.players.filter((player) => {
    if (!managerSearch) return true;
    return player.name.toLowerCase().includes(managerSearch);
  });

  if (!filteredManagerPlayers.length) {
    playersListEl.innerHTML = '<li class="hint">No players match the current search.</li>';
  }

  for (const player of filteredManagerPlayers) {
    const li = document.createElement("li");
    if (selectedStatsId === player.id) {
      li.classList.add("player-selected");
    }
    li.innerHTML = `
      <div class="player-row-main">
        <button type="button" class="player-name-btn" data-stats-id="${player.id}" aria-label="Show stats for ${player.name}">${player.name}</button>
      </div>
      ${showDeleteButton ? `<button type="button" data-delete-id="${player.id}" aria-label="Delete ${player.name}">Delete</button>` : ""}
    `;
    playersListEl.appendChild(li);

  }

  if (!filteredSelectablePlayers.length) {
    selectablePlayersEl.innerHTML = '<p class="hint selectable-players-empty">No players match the current search.</p>';
  }

  for (const player of filteredSelectablePlayers) {
    const chip = document.createElement("label");
    chip.className = `chip${player.is_busy ? " chip-busy" : ""}`;
    chip.innerHTML = `
      <input type="checkbox" data-select-id="${player.id}" ${
      state.selectedPlayerIds.has(player.id) ? "checked" : ""
    } ${player.is_busy ? "disabled" : ""} />
      <span>${player.name}</span>
      ${player.is_busy ? '<span class="mode-btn-sticker chip-busy-sticker">Busy</span>' : ""}
    `;
    selectablePlayersEl.appendChild(chip);
  }

  renderTeamAssignment();
  renderPlayerStats();
}

function labelForGameType(gameType) {
  if (gameType === "x01") return "X01";
  if (gameType === "english_cricket") return "English Cricket";
  if (gameType === "noughts_and_crosses") return "Noughts and Crosses";
  if (gameType === "55by5") return "55 by 5";
  return "55 by 5";
}

function playerStatsTitle(name) {
  const safeName = typeof name === "string" && name.trim() ? name.trim() : "Player";
  return `${safeName}'s Stats`;
}

function renderPlayerStats() {
  if (!playerStatsPanelEl || !playerStatsOverlayEl) return;

  const loadingPlayer = state.players.find((player) => player.id === state.loadingPlayerStatsId);
  if (state.loadingPlayerStatsId) {
    playerStatsOverlayEl.classList.add("visible");
    playerStatsPanelEl.innerHTML = `
      <div class="panel-header">
        <h3 id="player-stats-title">${playerStatsTitle(loadingPlayer?.name)}</h3>
        <button type="button" class="btn-ghost" data-close-player-stats aria-label="Close player stats">Close</button>
      </div>
      <div class="player-stats-body">
        <p class="hint">Loading stats...</p>
      </div>
    `;
    return;
  }

  if (!state.playerStats) {
    playerStatsOverlayEl.classList.remove("visible");
    playerStatsPanelEl.innerHTML = "";
    return;
  }

  const { player, stats } = state.playerStats;
  const winRate = Number(stats.win_rate || 0).toFixed(1);
  const breakdown = Array.isArray(stats.by_game_type)
    ? stats.by_game_type.map((item) => {
        const itemRate = item.played ? ((item.won / item.played) * 100).toFixed(1) : "0.0";
        return `
          <li class="player-stats-breakdown-row">
            <strong>${item.label}</strong>
            <span>${item.played}</span>
            <span>${item.won}</span>
            <span>${item.lost}</span>
            <span>${itemRate}%</span>
          </li>
        `;
      }).join("")
    : "";

  playerStatsOverlayEl.classList.add("visible");
  playerStatsPanelEl.innerHTML = `
    <div class="panel-header">
      <h3 id="player-stats-title">${playerStatsTitle(player.name)}</h3>
      <button type="button" class="btn-ghost" data-close-player-stats aria-label="Close player stats">Close</button>
    </div>
    <div class="player-stats-body">
      <div class="player-stats-summary player-stats-summary-header" aria-label="Player win loss summary">
        <div class="player-stat-tile"><strong>${stats.games_played}</strong><span>Played</span></div>
        <div class="player-stat-tile"><strong>${stats.games_won}</strong><span>Won</span></div>
        <div class="player-stat-tile"><strong>${stats.games_lost}</strong><span>Lost</span></div>
        <div class="player-stat-tile"><strong>${winRate}%</strong><span>Win %</span></div>
      </div>
      <div>
        <p class="hint">${stats.games_played ? "Results by game type" : "No completed games recorded for this player yet."}</p>
        <div class="player-stats-breakdown-wrap">
          ${stats.games_played ? `
            <div class="player-stats-breakdown-head" aria-hidden="true">
              <span>Game</span>
              <span>Played</span>
              <span>Won</span>
              <span>Lost</span>
              <span>%</span>
            </div>
          ` : ""}
          <ul class="player-stats-breakdown">${breakdown}</ul>
        </div>
      </div>
    </div>
  `;
}

async function loadPlayerStats(playerId) {
  state.loadingPlayerStatsId = playerId;
  renderPlayers();

  try {
    state.playerStats = await api(`/api/players/${playerId}/stats`);
  } catch (err) {
    state.playerStats = null;
    showMessage(err.message, true);
  } finally {
    state.loadingPlayerStatsId = null;
    renderPlayers();
  }
}

function selectedGameName() {
  return state.gameType ? labelForGameType(state.gameType) : "";
}

function updateHeroCopy(game) {
  if (!heroTitleEl || !heroSubtitleEl) return;

  const activeGameType = game && game.status === "active" ? game.game_type : null;
  if (activeGameType === "x01") {
    heroTitleEl.textContent = "X01";
    heroSubtitleEl.textContent = "Count down to exactly zero and avoid busts from overshooting or leaving 1.";
    return;
  }

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

function normalizeEditingTeamName(teamKey, rawValue) {
  const defaultName = teamKey === "team_b" ? "Team B" : "Team A";
  const currentName = normalizeTeamNames(state.teamNames)[teamKey];
  let nextValue = rawValue.slice(0, 40);

  if (currentName === defaultName && nextValue.startsWith(defaultName) && nextValue.length > defaultName.length) {
    nextValue = nextValue.slice(defaultName.length).trimStart();
  }

  return nextValue;
}

function syncStateFromGame(game) {
  state.game = game;
  state.pendingNoughtsCellIndex = null;
  if (!game) {
    resetX01TurnFlags();
    return;
  }

  state.gameType = game.game_type || "55by5";
  state.teamMode = game.team_mode || "solo";
  state.teamAssignments = game.team_assignments || {};
  setTeamNames(game.team_names || {}, { syncInputs: true });
  state.cricketStartingBattingTeam = game.cricket_state?.starting_batting_team || game.cricket_state?.batting_team || "team_a";
  state.x01StartingScore = game.x01_state?.starting_score || 501;
}

function restoreLobbyStateFromGame(game) {
  if (!game) return;

  const orderedPlayerIds = Array.isArray(game.players)
    ? game.players.map((player) => player.id).filter(Boolean)
    : [];

  state.selectedPlayerIds = new Set(orderedPlayerIds);
  state.orderedPlayerIds = [...orderedPlayerIds];
  state.teamMode = game.team_mode || "solo";
  state.teamAssignments = { ...(game.team_assignments || {}) };
  setTeamNames(game.team_names || {}, { syncInputs: true });
  state.cricketStartingBattingTeam = game.cricket_state?.starting_batting_team || game.cricket_state?.batting_team || "team_a";
  state.x01StartingScore = game.x01_state?.starting_score || 501;

  const teamModeSoloEl = document.getElementById("team-mode-solo");
  const teamModeTeamsEl = document.getElementById("team-mode-teams");
  if (teamModeSoloEl instanceof HTMLInputElement) {
    teamModeSoloEl.checked = state.teamMode !== "teams";
  }
  if (teamModeTeamsEl instanceof HTMLInputElement) {
    teamModeTeamsEl.checked = state.teamMode === "teams";
  }
}

function teamDisplayName(teamKey, rawNames = state.teamNames) {
  const names = normalizeTeamNames(rawNames);
  return teamKey === "team_b" ? names.team_b : names.team_a;
}

function teamInitialsLabel(teamName, members) {
  if (teamName !== "Team A" && teamName !== "Team B") return teamName;
  if (!members || !members.length) return teamName;
  const initials = members.map((p) => (p.name || "?")[0].toUpperCase()).join(" & ");
  return `${teamName} (${initials})`;
}

function winnerDisplayName(game, fallback = "Tie") {
  if (!game) return fallback;
  const baseWinnerName = game.winner_team_name || game.players.find((p) => p.id === game.winner_player_id)?.name || fallback;
  if (game.game_type !== "noughts_and_crosses" || game.team_mode !== "teams" || !game.winner_team) {
    return baseWinnerName;
  }

  const grouped = groupPlayersByTeam([...(game.players || [])]);
  const members = game.winner_team === "team_b" ? grouped.team_b : grouped.team_a;
  return teamInitialsLabel(baseWinnerName, members);
}

function inferHistoryTeamMembers(game, teamKey) {
  if (!game || game.team_mode !== "teams") return [];
  const ordered = [...(game.participants || [])].sort((a, b) => (a.position || 0) - (b.position || 0));
  return ordered.filter((_, index) => (teamKey === "team_b" ? index % 2 === 1 : index % 2 === 0));
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

    const teamALabel = teamInitialsLabel(teamDisplayName("team_a"), teamAPlayers);
    const teamBLabel = teamInitialsLabel(teamDisplayName("team_b"), teamBPlayers);
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

function closeX01StartOverlay() {
  if (x01StartOverlayEl) {
    x01StartOverlayEl.classList.remove("visible");
  }
}

function resetX01TurnFlags() {
  state.x01CheckoutAnnouncementKey = null;
}

function choosePreferredSpeechVoice() {
  if (typeof window.speechSynthesis === "undefined") return null;

  const voices = window.speechSynthesis.getVoices();
  if (!Array.isArray(voices) || !voices.length) return null;

  const ukVoices = voices.filter((voice) => typeof voice.lang === "string" && voice.lang.toLowerCase().startsWith("en-gb"));
  const maleUkVoices = ukVoices.filter((voice) => SPEECH_PREFERRED_MALE_PATTERNS.some((pattern) => pattern.test(voice.name)));

  for (const pattern of SPEECH_PREFERRED_UK_PATTERNS) {
    const matchedMaleUk = maleUkVoices.find((voice) => pattern.test(voice.name) || pattern.test(voice.lang));
    if (matchedMaleUk) return matchedMaleUk;
  }

  if (maleUkVoices.length) {
    return maleUkVoices[0];
  }

  for (const pattern of SPEECH_PREFERRED_UK_PATTERNS) {
    const matchedUk = ukVoices.find((voice) => pattern.test(voice.name) || pattern.test(voice.lang));
    if (matchedUk) return matchedUk;
  }

  if (ukVoices.length) {
    return ukVoices[0];
  }

  return voices.find((voice) => typeof voice.lang === "string" && voice.lang.toLowerCase().startsWith("en")) || voices[0] || null;
}

function ensurePreferredSpeechVoice() {
  if (preferredSpeechVoice) return preferredSpeechVoice;
  preferredSpeechVoice = choosePreferredSpeechVoice();
  return preferredSpeechVoice;
}

function speakText(text, { interrupt = true } = {}) {
  if (!text || state.audioMuted || typeof window.speechSynthesis === "undefined") return;

  try {
    // On iOS (Safari and Chrome/WKWebView) the synthesis engine can silently
    // pause after the tab loses focus or after cancel(). Always call resume()
    // before speak() to unblock it.
    window.speechSynthesis.resume();
    // Retry voice selection if getVoices() was empty at init time (common on
    // iOS Chrome where voiceschanged fires late or not at all).
    const voice = ensurePreferredSpeechVoice();
    const utterance = new SpeechSynthesisUtterance(text);
    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang || "en-GB";
    } else {
      utterance.lang = "en-GB";
    }
    utterance.rate = 0.94;
    utterance.pitch = 1;
    utterance.volume = 1;
    if (interrupt) {
      window.speechSynthesis.cancel();
      // After cancel(), iOS needs another resume() before speak() will fire.
      window.speechSynthesis.resume();
    }
    window.speechSynthesis.speak(utterance);
  } catch (_err) {
    // Ignore speech synthesis errors; checkout text remains visible in the UI.
  }
}

function buildX01CheckoutAnnouncement(game) {
  if (!game || game.game_type !== "x01" || game.status !== "active") return null;

  const x01State = game.x01_state || {};
  const checkout = x01State.active_checkout;
  const remaining = Number(x01State.active_remaining);
  const activePlayer = game.players.find((player) => player.id === game.active_player_id);
  const shouldAnnounce = Boolean(checkout) || (Number.isFinite(remaining) && remaining >= 2 && remaining <= 40);

  if (!activePlayer || !shouldAnnounce) {
    return null;
  }

  return {
    key: `${game.id}:${game.turns.length}:${activePlayer.id}:${remaining}`,
    text: `${activePlayer.name}, you require ${remaining}`,
  };
}

function announceX01CheckoutIfNeeded(game) {
  const announcement = buildX01CheckoutAnnouncement(game);
  if (!announcement) return;
  if (announcement.key === state.x01CheckoutAnnouncementKey) return;

  state.x01CheckoutAnnouncementKey = announcement.key;
  speakText(announcement.text, { interrupt: false });
}

function announceX01TurnResult(turn, game) {
  if (!turn || !game || game.game_type !== "x01") return;

  const playerName = game.players.find((player) => player.id === turn.player_id)?.name || "Player";
  if (turn.x01_result === "bust_overshoot") {
    speakText(`${playerName} bust. ${turn.total_points} scored does not count.`);
    return;
  }
  if (turn.x01_result === "bust_leave_one") {
    speakText(`${playerName} bust. Leaving 1 is not allowed.`);
    return;
  }

  speakText(String(turn.total_points));
}

function renderX01StartSelection() {
  const selectedScore = String(state.x01StartingScore || 501);
  document.querySelectorAll('input[name="x01-starting-score"]').forEach((input) => {
    if (input instanceof HTMLInputElement) {
      input.checked = input.value === selectedScore;
    }
  });
}

function openX01StartOverlay() {
  renderX01StartSelection();
  if (x01StartOverlayEl) {
    x01StartOverlayEl.classList.add("visible");
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
        <strong>Bat (Score)</strong>
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
        <strong>Bowl (Bulls)</strong>
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
    const team = state.teamAssignments[id] || "team_a";
    const li = document.createElement("li");
    li.draggable = true;
    li.dataset.playerId = String(id);
    li.innerHTML = `
      <span class="sortable-player-name">${player.name}</span>
      <span class="sortable-controls" aria-label="Reorder controls for ${player.name}">
        <button type="button" class="sortable-btn" data-team-action="up" aria-label="Move ${player.name} up">↑</button>
        <button type="button" class="sortable-btn" data-team-action="down" aria-label="Move ${player.name} down">↓</button>
        <button
          type="button"
          class="sortable-btn"
          data-team-action="swap"
          data-team-target="${team === "team_b" ? "team_a" : "team_b"}"
          aria-label="Move ${player.name} to ${team === "team_b" ? "Team A" : "Team B"}"
        >⇄</button>
      </span>
    `;
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

function setupTeamTouchOrderingControls() {
  const moveWithinList = (list, item, direction) => {
    if (!(list instanceof HTMLElement) || !(item instanceof HTMLElement)) return;

    if (direction < 0) {
      const previous = item.previousElementSibling;
      if (previous) {
        list.insertBefore(item, previous);
      }
      return;
    }

    const next = item.nextElementSibling;
    if (next) {
      list.insertBefore(next, item);
    }
  };

  [teamAListEl, teamBListEl].forEach((list) => {
    if (!(list instanceof HTMLElement)) return;

    list.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;

      const button = target.closest("[data-team-action]");
      if (!(button instanceof HTMLButtonElement)) return;

      event.preventDefault();
      event.stopPropagation();

      const listItem = button.closest("li");
      if (!(listItem instanceof HTMLLIElement)) return;

      const action = button.getAttribute("data-team-action");
      if (action === "up") {
        moveWithinList(list, listItem, -1);
      } else if (action === "down") {
        moveWithinList(list, listItem, 1);
      } else if (action === "swap") {
        const targetTeam = button.getAttribute("data-team-target") === "team_b" ? teamBListEl : teamAListEl;
        if (targetTeam instanceof HTMLElement && targetTeam !== list) {
          targetTeam.appendChild(listItem);
        }
      }

      updateOrderFromTeamLists();
    });
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
    li.innerHTML = `
      <span class="sortable-player-name">${player.name}</span>
      <span class="sortable-controls" aria-label="Reorder controls for ${player.name}">
        <button type="button" class="sortable-btn" data-order-action="up" aria-label="Move ${player.name} up">↑</button>
        <button type="button" class="sortable-btn" data-order-action="down" aria-label="Move ${player.name} down">↓</button>
      </span>
    `;
    orderListEl.appendChild(li);
  });
}

function setupOrderTouchControls() {
  if (!orderListEl) return;

  orderListEl.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const button = target.closest("[data-order-action]");
    if (!(button instanceof HTMLButtonElement)) return;

    event.preventDefault();
    event.stopPropagation();

    const listItem = button.closest("li");
    if (!(listItem instanceof HTMLLIElement)) return;

    const playerId = Number(listItem.dataset.id);
    if (!playerId) return;

    const currentIndex = state.orderedPlayerIds.indexOf(playerId);
    if (currentIndex < 0) return;

    const action = button.getAttribute("data-order-action");
    const targetIndex = action === "up" ? currentIndex - 1 : currentIndex + 1;
    if (targetIndex < 0 || targetIndex >= state.orderedPlayerIds.length) return;

    const reordered = [...state.orderedPlayerIds];
    const [moved] = reordered.splice(currentIndex, 1);
    reordered.splice(targetIndex, 0, moved);
    state.orderedPlayerIds = reordered;

    renderOrderList();
    renderCricketRoleSelection();
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
  const teamName = teamInitialsLabel(teamDisplayName(teamKey, game.team_names), members);
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
      const members = grouped[teamKey];
      if (!members.length) continue;
      const label = teamInitialsLabel(teamDisplayName(teamKey, game.team_names), members);
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

function renderX01TurnPanel(game) {
  if (!x01TurnPanelEl || !x01ActiveRemainingEl || !x01CheckoutHintEl) return;

  const x01State = game.x01_state || {};
  const remaining = x01State.active_remaining ?? x01State.starting_score ?? 501;

  x01TurnPanelEl.classList.toggle("hidden", game.game_type !== "x01");
  x01ActiveRemainingEl.textContent = String(remaining);
  x01CheckoutHintEl.textContent = x01State.active_checkout || "No checkout";
}

function renderX01Scoreboard(game) {
  scoreboardEl.innerHTML = "";
  const x01State = game.x01_state || {};
  const players = [...game.players];

  if (game.team_mode === "teams") {
    const grouped = groupPlayersByTeam(players);
    for (const teamKey of ["team_a", "team_b"]) {
      const members = grouped[teamKey];
      if (!members.length) continue;
      const label = teamInitialsLabel(teamDisplayName(teamKey, game.team_names), members);
      const teamRemaining = members[0]?.x01_remaining ?? x01State.starting_score ?? 501;
      const teamRow = document.createElement("tr");
      teamRow.className = "team-header-row";
      teamRow.innerHTML = `
        <td><strong>${label}</strong></td>
        <td><strong>${teamRemaining}</strong></td>
      `;
      scoreboardEl.appendChild(teamRow);

      for (const player of members) {
        const tr = document.createElement("tr");
        if (player.id === game.active_player_id && game.status === "active") {
          tr.classList.add("active-row");
        }
        tr.innerHTML = `
          <td class="scoreboard-member">${player.name}</td>
          <td>${player.x01_remaining ?? teamRemaining}</td>
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
    tr.innerHTML = `
      <td>${player.name}</td>
      <td>${player.x01_remaining ?? x01State.starting_score ?? 501}</td>
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
        <input id="cricket-batting-total" type="number" inputmode="none" min="0" max="180" value="" readonly ${isBattingTurn ? "" : "disabled"} />
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
      primeSpeechSynthesisIfNeeded();
      await submitScore(state.cricketPendingMarks || 0);
    });
  }

  const battingInput = document.getElementById("cricket-batting-total");
  if (battingInput) {
    battingInput.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        if (isOverScorepadLimit(battingInput)) return;
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
  const grouped = game.team_mode === "teams" ? groupPlayersByTeam([...game.players]) : null;
  const xName = grouped ? teamInitialsLabel(noughtsState.x_name || "X", grouped.team_a) : (noughtsState.x_name || "X");
  const oName = grouped ? teamInitialsLabel(noughtsState.o_name || "O", grouped.team_b) : (noughtsState.o_name || "O");

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
        const targetLabel = cell?.label || `Square ${index + 1}`;
        return `
          <button
            type="button"
            class="noughts-cell${mark ? ` is-marked is-${mark.toLowerCase()}` : ""}${isWinning ? " is-winning" : ""}"
            data-board-index="${index}"
            ${game.status === "active" && !isClaimed ? "" : "disabled"}
            aria-label="${targetLabel}${mark ? ` claimed by ${mark}` : ""}"
          >
            <span class="noughts-cell-label">${targetLabel}</span>
            <span class="noughts-cell-mark${isClaimed ? "" : " is-target"}">${mark || targetLabel}</span>
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
    closePlayerManager();
    closeCricketStartOverlay();
    closeX01StartOverlay();
    closeNoughtsMarkOverlay();
    if (gameSelectionPanelEl) {
      gameSelectionPanelEl.classList.add("hidden");
    }
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
      standardTurnControlsEl.classList.remove("is-x01-layout");
    }
    if (x01TurnPanelEl) {
      x01TurnPanelEl.classList.add("hidden");
    }
    if (turnPlayerPanelEl) {
      turnPlayerPanelEl.classList.add("hidden");
    }
    if (turnPlayerNameEl) {
      turnPlayerNameEl.textContent = "-";
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
  const isX01 = game.game_type === "x01";
  const isNoughts = game.game_type === "noughts_and_crosses";
  const activePlayer = game.players.find((p) => p.id === game.active_player_id);
  const headers = Array.from(document.querySelectorAll("#scoreboard-table thead th"));
  if (headers.length >= 3) {
    headers[0].textContent = "Player";
    headers[1].textContent = isX01 ? "Remaining" : "Score";
    headers[2].textContent = "Points Required";
    headers[2].hidden = isX01;
  }

  if (standardTurnControlsEl) {
    standardTurnControlsEl.classList.toggle("hidden", isCricket || isNoughts || game.status !== "active");
    standardTurnControlsEl.classList.toggle("is-x01-layout", isX01 && game.status === "active");
  }
  if (turnPlayerPanelEl) {
    const showTurnPlayerPanel = isX01 && game.status === "active";
    turnPlayerPanelEl.classList.toggle("hidden", !showTurnPlayerPanel);
  }
  if (turnPlayerNameEl) {
    turnPlayerNameEl.textContent = activePlayer?.name || "Unknown";
  }
  if (sharedTurnActionsEl) {
    sharedTurnActionsEl.classList.toggle("hidden", game.status !== "active");
  }
  if (cricketUndoTurnEl) {
    const showUndo = (isCricket || isNoughts) && game.status === "active";
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

  if (game.status === "finished") {
    closeNoughtsMarkOverlay();
    const winnerName = winnerDisplayName(game, "Tie");
    activeGameMetaEl.innerHTML = `<strong>Winner: ${winnerName}</strong>`;
  } else if (isCricket) {
    activeGameMetaEl.innerHTML = `<strong class="current-player">${activePlayer?.name || "Unknown"} to Throw</strong>`;
  } else if (isNoughts) {
    activeGameMetaEl.innerHTML = "<strong>Noughts and Crosses</strong>";
  } else if (isX01) {
    const checkoutText = game.x01_state?.active_checkout ? `<span class="hint">Checkout: ${game.x01_state.active_checkout}</span>` : "";
    activeGameMetaEl.innerHTML = checkoutText;
  } else {
    activeGameMetaEl.innerHTML = `<strong class="current-player">${activePlayer?.name || "Unknown"} to Throw</strong>`;
  }

  announceX01CheckoutIfNeeded(game);

  if (isCricket) {
    renderCricketDashboard(game);
    scoreboardEl.innerHTML = "";
  } else if (isNoughts) {
    renderNoughtsAndCrossesDashboard(game);
    scoreboardEl.innerHTML = "";
  } else if (isX01) {
    renderX01TurnPanel(game);
    renderX01Scoreboard(game);
  } else {
    renderX01TurnPanel({ game_type: null });
    renderStandardScoreboard(game);
  }

  turnsListEl.innerHTML = "";
  for (const turn of game.turns.slice().reverse()) {
    const li = document.createElement("li");
    const turnNote = isCricket
      ? (turn.counted
        ? `+${turn.fives_awarded} ${turn.total_points <= 6 ? "wicket marks" : "runs"}`
        : "no score")
      : isX01
        ? (turn.x01_result === "bust_overshoot"
          ? "bust below zero"
          : turn.x01_result === "bust_leave_one"
            ? "bust on 1 remaining"
                : `${turn.total_points} scored`)
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
    turnInputLabelEl.textContent = isX01 ? "Turn total" : "Total scored";
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

function shouldRefreshLobbyAvailability() {
  return document.visibilityState === "visible" && (!state.game || state.game.status !== "active");
}

async function refreshLobbyAvailability() {
  if (!shouldRefreshLobbyAvailability() || lobbyAvailabilityRefreshInFlight) {
    return;
  }

  lobbyAvailabilityRefreshInFlight = true;
  try {
    await loadPlayers();
  } catch (_err) {
    // Ignore background refresh failures; foreground actions still surface errors.
  } finally {
    lobbyAvailabilityRefreshInFlight = false;
  }
}

function startLobbyAvailabilityPolling() {
  if (lobbyAvailabilityIntervalId) {
    window.clearInterval(lobbyAvailabilityIntervalId);
  }
  lobbyAvailabilityIntervalId = window.setInterval(() => {
    void refreshLobbyAvailability();
  }, LOBBY_AVAILABILITY_REFRESH_MS);
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
    const modeLabel = game.game_type === "x01"
      ? "X01"
      : game.game_type === "english_cricket"
      ? "English Cricket"
      : game.game_type === "noughts_and_crosses"
        ? "Noughts and Crosses"
        : "55 by 5";
    const winner = game.team_mode === "teams"
      ? teamInitialsLabel(
        game.winner_team_name || game.winner_name || "Unknown",
        inferHistoryTeamMembers(game, game.winner_team || "team_a")
      )
      : (game.winner_team_name || game.winner_name || "Unknown");
    li.textContent = `[${modeLabel}] Game #${game.id}: Winner ${winner}, ${game.turn_count} turns. Order: ${names}`;
    historyListEl.appendChild(li);
  }
}

async function loadAuthUser() {
  const user = await api("/api/auth/me");
  state.currentUser = user;
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
  await loadPlayers();

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
        x01_starting_score: state.gameType === "x01" ? state.x01StartingScore : undefined,
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
        x01_starting_score: gameType === "x01" ? finishedGame.x01_state?.starting_score : undefined,
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
  applyAudioMuted(true);
  setupScoreKeypad();
  setupDragAndDrop();
  setupTeamDragAndDrop();
  setupOrderTouchControls();
  setupTeamTouchOrderingControls();
  await loadAuthUser();
  setHelpSection(activeHelpSection);
  resetInactivityTimer();

  ["click", "keydown", "mousedown", "mousemove", "scroll", "touchstart"].forEach((eventName) => {
    window.addEventListener(eventName, resetInactivityTimer, { passive: true });
  });

  const choose55Btn = document.getElementById("choose-55by5");
  const chooseX01Btn = document.getElementById("choose-x01");
  const chooseCricketBtn = document.getElementById("choose-english-cricket");
  const chooseNoughtsBtn = document.getElementById("choose-noughts-and-crosses");
  const teamModeSoloEl = document.getElementById("team-mode-solo");
  const teamModeTeamsEl = document.getElementById("team-mode-teams");

  if (muteButtonEl) {
    muteButtonEl.addEventListener("click", () => {
      applyAudioMuted(!state.audioMuted);
    });
  }

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

  if (playerManagerOpenEl) {
    playerManagerOpenEl.addEventListener("click", () => {
      openPlayerManager();
    });
  }

  if (playerManagerCloseEl) {
    playerManagerCloseEl.addEventListener("click", () => {
      closePlayerManager();
    });
  }

  if (playerManagerOverlayEl) {
    playerManagerOverlayEl.addEventListener("click", (event) => {
      if (event.target === playerManagerOverlayEl) {
        closePlayerManager();
      }
    });
  }

  if (playerSelectionSearchEl) {
    playerSelectionSearchEl.addEventListener("input", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) return;
      state.playerSelectionSearch = target.value;
      renderPlayers();
    });
  }

  if (playerStatsOverlayEl) {
    playerStatsOverlayEl.addEventListener("click", (event) => {
      if (event.target === playerStatsOverlayEl) {
        closePlayerStats();
      }
    });
  }

  if (playerManagerSearchEl) {
    playerManagerSearchEl.addEventListener("input", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) return;
      state.playerManagerSearch = target.value;
      renderPlayers();
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (helpOverlayEl?.classList.contains("visible")) {
      closeHelpOverlay();
      return;
    }
    if (playerStatsOverlayEl?.classList.contains("visible")) {
      closePlayerStats();
      return;
    }
    if (playerManagerOverlayEl?.classList.contains("visible")) {
      closePlayerManager();
      return;
    }
    if (cricketStartOverlayEl?.classList.contains("visible")) {
      closeCricketStartOverlay();
      return;
    }
    if (x01StartOverlayEl?.classList.contains("visible")) {
      closeX01StartOverlay();
      return;
    }
    if (noughtsMarkOverlayEl?.classList.contains("visible")) {
      closeNoughtsMarkOverlay();
    }
  });

  document.addEventListener("visibilitychange", () => {
    void refreshLobbyAvailability();
  });

  window.addEventListener("focus", () => {
    void refreshLobbyAvailability();
  });

  if (typeof window.speechSynthesis !== "undefined") {
    ensurePreferredSpeechVoice();
    window.speechSynthesis.addEventListener("voiceschanged", () => {
      preferredSpeechVoice = choosePreferredSpeechVoice();
    });
    // iOS Chrome (WKWebView) sometimes doesn't fire voiceschanged and doesn't
    // unlock the synthesis context via click alone. Primer on first touchstart
    // ensures the context is unlocked before the first async speak() attempt.
    document.addEventListener("touchstart", () => {
      primeSpeechSynthesisIfNeeded();
    }, { once: true, passive: true });
  }

  document.querySelectorAll('input[name="x01-starting-score"]').forEach((input) => {
    input.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) return;
      state.x01StartingScore = Number(target.value) || 501;
    });
  });

  if (chooseX01Btn) {
    chooseX01Btn.addEventListener("click", () => {
      closeCricketStartOverlay();
      closeNoughtsMarkOverlay();
      closePlayerStats();
      state.gameType = "x01";
      state.teamMode = getTeamMode();
      state.x01StartingScore = 501;
      resetX01TurnFlags();
      applyLayoutMode(state.game);
      renderTeamAssignment();
      openX01StartOverlay();
    });
  }

  if (choose55Btn) {
    choose55Btn.addEventListener("click", async () => {
      closeCricketStartOverlay();
      closeX01StartOverlay();
      closePlayerStats();
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
      closeX01StartOverlay();
      closePlayerStats();
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
      closeX01StartOverlay();
      closeNoughtsMarkOverlay();
      closePlayerStats();
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

  if (x01StartCancelEl) {
    x01StartCancelEl.addEventListener("click", () => {
      closeX01StartOverlay();
    });
  }

  if (x01StartGameEl) {
    x01StartGameEl.addEventListener("click", async () => {
      closeX01StartOverlay();
      try {
        await startConfiguredGame();
      } catch (err) {
        showMessage(err.message, true);
      }
    });
  }

  if (cricketStartOverlayEl) {
    cricketStartOverlayEl.addEventListener("click", (event) => {
      if (event.target === cricketStartOverlayEl) {
        closeCricketStartOverlay();
      }
    });
  }

  if (x01StartOverlayEl) {
    x01StartOverlayEl.addEventListener("click", (event) => {
      if (event.target === x01StartOverlayEl) {
        closeX01StartOverlay();
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
      const nextValue = normalizeEditingTeamName(teamKey, inputEl.value);
      if (inputEl.value !== nextValue) {
        inputEl.value = nextValue;
      }
      state.teamNames = {
        ...state.teamNames,
        [teamKey]: nextValue,
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

    const statsTrigger = target.closest("[data-stats-id]");
    if (statsTrigger instanceof HTMLElement) {
      const statsId = Number(statsTrigger.getAttribute("data-stats-id"));
      if (statsId) {
        await loadPlayerStats(statsId);
      }
      return;
    }

    const deleteTrigger = target.closest("[data-delete-id]");
    const id = deleteTrigger instanceof HTMLElement ? deleteTrigger.getAttribute("data-delete-id") : null;
    if (!id) return;

    try {
      await api(`/api/players/${id}`, { method: "DELETE" });
      await loadPlayers();
      showMessage("Player deleted.");
    } catch (err) {
      showMessage(err.message, true);
    }
  });

  if (playerStatsPanelEl) {
    playerStatsPanelEl.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      const closeTrigger = target.closest("[data-close-player-stats]");
      if (!(closeTrigger instanceof HTMLElement)) return;

      closePlayerStats();
    });
  }

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
        await loadPlayers();
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
    userAccountsListEl.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;

      const toggle = target.closest("[data-admin-user-toggle]");
      if (!(toggle instanceof HTMLElement)) return;

      const userId = Number(toggle.getAttribute("data-admin-user-toggle"));
      if (!userId) return;

      if (state.expandedAdminUserIds.has(userId)) {
        state.expandedAdminUserIds.delete(userId);
      } else {
        state.expandedAdminUserIds.add(userId);
      }
      loadAdminUsers().catch((err) => {
        showMessage(err.message, true);
      });
    });

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
        state.expandedAdminUserIds.add(Number(userId));
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
      const previousGame = state.game;
      await api(`/api/games/${state.game.id}`, { method: "DELETE" });
      if (stopFireworks) { stopFireworks(); stopFireworks = null; }
      if (winnerOverlayEl) {
        winnerOverlayEl.classList.remove("visible");
      }
      state.game = null;
      state.gameType = null;
      renderGame();
      restoreLobbyStateFromGame(previousGame);
      await loadPlayers();
      await loadHistory();
      showMessage("Game quit.");
    } catch (err) {
      showMessage(err.message, true);
    }
  });

  const winnerContinueBtn = document.getElementById("winner-continue");
  if (winnerContinueBtn && winnerOverlayEl) {
    winnerContinueBtn.addEventListener("click", async () => {
      const previousGame = state.game;
      if (stopFireworks) { stopFireworks(); stopFireworks = null; }
      winnerOverlayEl.classList.remove("visible");
      state.game = null;
      state.gameType = null;
      renderGame();
      restoreLobbyStateFromGame(previousGame);
      await loadPlayers();
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
  startLobbyAvailabilityPolling();
}

init().catch((err) => showMessage(err.message, true));
