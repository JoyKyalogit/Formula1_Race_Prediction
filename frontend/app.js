const API_BASE = "/api";

const errorBox = document.getElementById("error");
const seasonSelect = document.getElementById("seasonSelect");
const roundSelect = document.getElementById("roundSelect");
const targetSelect = document.getElementById("targetSelect");
const predictBtn = document.getElementById("predictBtn");
const btnLabel = predictBtn.querySelector(".btn-label");

const summaryTbody = document.querySelector("#summaryTable tbody");
const predictionTbody = document.querySelector("#predictionTable tbody");
const predictionEmpty = document.getElementById("predictionEmpty");
const predictionResults = document.getElementById("predictionResults");
const resultsMeta = document.getElementById("resultsMeta");
const seasonRoundBadge = document.getElementById("seasonRoundBadge");

const statRound = document.getElementById("statRound");
const statTopDriver = document.getElementById("statTopDriver");
const statTopProb = document.getElementById("statTopProb");
const statBestForm = document.getElementById("statBestForm");

/** @type {Array<Record<string, unknown>>} */
let latestSummary = [];
/** @type {Array<Record<string, unknown>>} */
let latestPredictions = [];

const TEAM_COLORS = {
  mclaren: "#FF8000",
  mercedes: "#27F4D2",
  "red bull": "#3671C6",
  redbull: "#3671C6",
  ferrari: "#E8002D",
  alpine: "#FF87BC",
  "aston martin": "#229971",
  astonmartin: "#229971",
  williams: "#64C4FF",
  "haas f1 team": "#B6BABD",
  haas: "#B6BABD",
  "racing bulls": "#6692FF",
  "rb f1 team": "#6692FF",
  rb: "#6692FF",
  "kick sauber": "#52E252",
  sauber: "#52E252",
  "alfa romeo": "#52E252",
  alphatauri: "#6692FF",
  "alpha tauri": "#6692FF",
  "toro rosso": "#469BFF",
  renault: "#FFF500",
  "racing point": "#F596C8",
  "force india": "#F596C8",
};

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

function fillSelect(selectEl, values) {
  selectEl.innerHTML = "";
  values.forEach((v) => {
    const opt = document.createElement("option");
    opt.value = String(v);
    opt.textContent = String(v);
    selectEl.appendChild(opt);
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getInitials(name) {
  const parts = String(name || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function teamColor(constructorName) {
  const key = String(constructorName || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .trim();
  if (TEAM_COLORS[key]) return TEAM_COLORS[key];
  const compact = key.replace(/\s+/g, "");
  if (TEAM_COLORS[compact]) return TEAM_COLORS[compact];
  for (const [name, color] of Object.entries(TEAM_COLORS)) {
    if (key.includes(name) || name.includes(key)) return color;
  }
  return "#6B6B6B";
}

function confidenceFromProb(prob) {
  if (prob >= 0.7) return { label: "High Confidence", className: "high" };
  if (prob >= 0.4) return { label: "Medium Confidence", className: "medium" };
  return { label: "Low Confidence", className: "low" };
}

function formatPct(prob) {
  return `${Math.round(Number(prob) * 100)}%`;
}

function targetLabel(value) {
  return value === "is_winner" ? "Race Win" : "Top 3 Finish";
}

function updateSeasonRoundBadge() {
  const season = seasonSelect.value || "—";
  const round = roundSelect.value || "—";
  const valueEl = seasonRoundBadge.querySelector(".badge-value");
  valueEl.textContent = `${season} · R${round}`;
  statRound.textContent = roundSelect.value ? `Round ${roundSelect.value}` : "—";
}

function updateSummaryStats() {
  updateSeasonRoundBadge();

  if (latestPredictions.length > 0) {
    const top = latestPredictions[0];
    const prob = Number(top.pred_prob ?? 0);
    statTopDriver.textContent = top.driver_name || "—";
    statTopProb.textContent = formatPct(prob);
  } else {
    statTopDriver.textContent = "—";
    statTopProb.textContent = "—";
  }

  if (latestSummary.length > 0) {
    const best = [...latestSummary].sort(
      (a, b) => Number(a.avg_finish_last5 ?? 99) - Number(b.avg_finish_last5 ?? 99)
    )[0];
    const avg = Number(best.avg_finish_last5 ?? 0);
    statBestForm.textContent = `P${avg.toFixed(1)}`;
  } else {
    statBestForm.textContent = "—";
  }
}

function driverIdentityHtml(driverName, constructorName, subtext) {
  const color = teamColor(constructorName);
  const initials = getInitials(driverName);
  const sub = subtext
    ? `<span class="driver-sub">${escapeHtml(subtext)}</span>`
    : constructorName
      ? `<span class="driver-sub">${escapeHtml(constructorName)}</span>`
      : "";

  return `
    <div class="driver-cell">
      <span class="driver-accent" style="background:${color}"></span>
      <span class="driver-avatar" style="background:${color}33; color:${color}; border:1px solid ${color}55">${escapeHtml(initials)}</span>
      <span class="driver-meta">
        <span class="driver-name">${escapeHtml(driverName ?? "")}</span>
        ${sub}
      </span>
    </div>
  `;
}

function constructorLookup() {
  const map = new Map();
  latestPredictions.forEach((row) => {
    if (row.driver_name && row.constructor_name) {
      map.set(String(row.driver_name), String(row.constructor_name));
    }
  });
  return map;
}

function renderSummary(rows) {
  latestSummary = rows || [];
  summaryTbody.innerHTML = "";

  const maxPoints = Math.max(
    1,
    ...latestSummary.map((r) => Number(r.points_last5 ?? 0))
  );
  const constructors = constructorLookup();

  latestSummary.forEach((row) => {
    const avg = Number(row.avg_finish_last5 ?? 0);
    const points = Number(row.points_last5 ?? 0);
    const formPct = Math.round((points / maxPoints) * 100);
    const constructorName = constructors.get(String(row.driver_name)) || null;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${driverIdentityHtml(row.driver_name, constructorName)}</td>
      <td>
        <div class="form-metrics">
          <span class="form-metric-label">Average finish</span>
          <span class="form-metric-value">P${avg.toFixed(1)}</span>
        </div>
      </td>
      <td>
        <div class="form-metrics">
          <span class="form-metric-label">Last 5 races</span>
          <span class="form-metric-value">${points} pts</span>
        </div>
      </td>
      <td class="form-bar-cell">
        <div class="form-bar-track" aria-hidden="true">
          <div class="form-bar-fill" data-width="${formPct}"></div>
        </div>
      </td>
    `;
    summaryTbody.appendChild(tr);

    requestAnimationFrame(() => {
      const fill = tr.querySelector(".form-bar-fill");
      if (fill) fill.style.width = `${formPct}%`;
    });

    if (!constructorName) {
      const accent = tr.querySelector(".driver-accent");
      const avatar = tr.querySelector(".driver-avatar");
      if (accent && avatar) {
        const color = "#6B6B6B";
        accent.style.background = color;
        avatar.style.background = `${color}33`;
        avatar.style.color = "#C8C8C8";
        avatar.style.border = `1px solid ${color}55`;
      }
    }
  });

  updateSummaryStats();
}

function renderPredictions(rows) {
  latestPredictions = rows || [];
  predictionTbody.innerHTML = "";

  if (latestPredictions.length === 0) {
    predictionEmpty.classList.remove("hidden");
    predictionResults.classList.add("hidden");
    updateSummaryStats();
    return;
  }

  predictionEmpty.classList.add("hidden");
  predictionResults.classList.remove("hidden");
  predictionResults.classList.remove("animate-in");
  void predictionResults.offsetWidth;
  predictionResults.classList.add("animate-in");

  const season = seasonSelect.value;
  const round = roundSelect.value;
  resultsMeta.textContent = `${season} · Round ${round} · ${targetLabel(targetSelect.value)}`;

  latestPredictions.forEach((row, index) => {
    const prob = Number(row.pred_prob ?? 0);
    const pct = Math.round(prob * 100);
    const confidence = confidenceFromProb(prob);
    const tr = document.createElement("tr");
    if (index === 0) tr.classList.add("is-top");

    tr.innerHTML = `
      <td>${driverIdentityHtml(row.driver_name, row.constructor_name)}</td>
      <td class="constructor-cell">${escapeHtml(row.constructor_name ?? "")}</td>
      <td class="pos-cell">${escapeHtml(row.grid ?? "")}</td>
      <td class="pos-cell">${escapeHtml(row.qualifying_position ?? "")}</td>
      <td class="prob-cell">
        <div class="prob-top">
          <span class="prob-pct">${formatPct(prob)}</span>
          <span class="prob-confidence ${confidence.className}">${confidence.label}</span>
        </div>
        <div class="prob-track" aria-hidden="true">
          <div class="prob-fill" data-width="${pct}"></div>
        </div>
        <div class="prob-label">${targetLabel(targetSelect.value)} probability</div>
      </td>
    `;
    predictionTbody.appendChild(tr);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const fill = tr.querySelector(".prob-fill");
        if (fill) fill.style.width = `${pct}%`;
      });
    });
  });

  updateSummaryStats();
}

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  const raw = await res.text();
  let data = null;

  try {
    data = raw ? JSON.parse(raw) : {};
  } catch (err) {
    data = null;
  }

  if (!res.ok) {
    if (data && data.detail) {
      throw new Error(data.detail);
    }
    if (raw) {
      throw new Error(raw);
    }
    throw new Error(`Request failed with status ${res.status}.`);
  }

  if (data === null) {
    throw new Error("Backend returned non-JSON success response.");
  }

  return data;
}

async function loadSummary(season, round) {
  const params = new URLSearchParams();
  if (season !== undefined && season !== null && season !== "") {
    params.set("season", String(season));
  }
  if (round !== undefined && round !== null && round !== "") {
    params.set("round", String(round));
  }
  const query = params.toString();
  const data = await fetchJSON(`${API_BASE}/driver-summary${query ? `?${query}` : ""}`);
  renderSummary(data.rows || []);
}

async function loadSeasons() {
  const data = await fetchJSON(`${API_BASE}/seasons`);
  const seasons = data.seasons || [];
  fillSelect(seasonSelect, seasons);
  if (seasons.length > 0) {
    seasonSelect.value = String(seasons[seasons.length - 1]);
  }
}

async function loadRounds(season) {
  const data = await fetchJSON(`${API_BASE}/rounds?season=${season}`);
  const rounds = data.rounds || [];
  fillSelect(roundSelect, rounds);
  if (rounds.length > 0) {
    roundSelect.value = String(rounds[rounds.length - 1]);
  }
}

async function runPrediction() {
  clearError();
  predictBtn.disabled = true;
  predictBtn.classList.add("is-loading");
  btnLabel.textContent = "Running Prediction...";

  try {
    const payload = {
      season: Number(seasonSelect.value),
      round: Number(roundSelect.value),
      target: targetSelect.value
    };

    const data = await fetchJSON(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    renderPredictions(data.rows || []);
    // Refresh form accents with constructor colors when prediction data is available.
    renderSummary(latestSummary);
  } catch (err) {
    showError(err.message);
  } finally {
    predictBtn.disabled = false;
    predictBtn.classList.remove("is-loading");
    btnLabel.textContent = "Predict Results";
  }
}

async function init() {
  clearError();
  try {
    await loadSeasons();
    if (seasonSelect.value) {
      await loadRounds(seasonSelect.value);
    }
    updateSeasonRoundBadge();
    await loadSummary(seasonSelect.value, roundSelect.value);
  } catch (err) {
    showError(err.message);
  }
}

seasonSelect.addEventListener("change", async (e) => {
  clearError();
  try {
    await loadRounds(e.target.value);
    updateSeasonRoundBadge();
    latestPredictions = [];
    renderPredictions([]);
    await loadSummary(seasonSelect.value, roundSelect.value);
  } catch (err) {
    showError(err.message);
  }
});

roundSelect.addEventListener("change", async () => {
  clearError();
  try {
    updateSeasonRoundBadge();
    latestPredictions = [];
    renderPredictions([]);
    await loadSummary(seasonSelect.value, roundSelect.value);
  } catch (err) {
    showError(err.message);
  }
});

predictBtn.addEventListener("click", runPrediction);

init();
