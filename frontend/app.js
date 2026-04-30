const API_BASE = "/api";

const errorBox = document.getElementById("error");
const seasonSelect = document.getElementById("seasonSelect");
const roundSelect = document.getElementById("roundSelect");
const targetSelect = document.getElementById("targetSelect");
const predictBtn = document.getElementById("predictBtn");

const summaryTbody = document.querySelector("#summaryTable tbody");
const predictionTbody = document.querySelector("#predictionTable tbody");

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

function renderSummary(rows) {
  summaryTbody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.driver_name ?? ""}</td>
      <td>${Number(row.avg_finish_last5 ?? 0).toFixed(2)}</td>
      <td>${row.points_last5 ?? ""}</td>
    `;
    summaryTbody.appendChild(tr);
  });
}

function renderPredictions(rows) {
  predictionTbody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.driver_name ?? ""}</td>
      <td>${row.constructor_name ?? ""}</td>
      <td>${row.grid ?? ""}</td>
      <td>${row.qualifying_position ?? ""}</td>
      <td>${Number(row.pred_prob ?? 0).toFixed(4)}</td>
    `;
    predictionTbody.appendChild(tr);
  });
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
  predictBtn.textContent = "Running Prediction...";

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
  } catch (err) {
    showError(err.message);
  } finally {
    predictBtn.disabled = false;
    predictBtn.textContent = "Predict Results";
  }
}

async function init() {
  clearError();
  try {
    await loadSeasons();
    if (seasonSelect.value) {
      await loadRounds(seasonSelect.value);
    }
    await loadSummary(seasonSelect.value, roundSelect.value);
  } catch (err) {
    showError(err.message);
  }
}

seasonSelect.addEventListener("change", async (e) => {
  clearError();
  try {
    await loadRounds(e.target.value);
    await loadSummary(seasonSelect.value, roundSelect.value);
  } catch (err) {
    showError(err.message);
  }
});

roundSelect.addEventListener("change", async () => {
  clearError();
  try {
    await loadSummary(seasonSelect.value, roundSelect.value);
  } catch (err) {
    showError(err.message);
  }
});

predictBtn.addEventListener("click", runPrediction);

init();