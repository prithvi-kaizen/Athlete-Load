// AthleteLoad Client-Side Interactive Engine

let currentTimelineChart = null;

// Presets data
const PRESETS = {
  recovered: {
    atl: 1600,
    ctl: 1700,
    soreness: 2,
    fatigue: 2,
    sleep_dur: 8.5,
    sleep_qual: 8,
    readiness: 8,
    stress: 2
  },
  overtraining: {
    atl: 3200,
    ctl: 1800,
    soreness: 7,
    fatigue: 8,
    sleep_dur: 6.0,
    sleep_qual: 4,
    readiness: 3,
    stress: 7
  },
  spike: {
    atl: 3600,
    ctl: 1900,
    soreness: 6,
    fatigue: 6,
    sleep_dur: 7.0,
    sleep_qual: 6,
    readiness: 5,
    stress: 5
  },
  sleep_debt: {
    atl: 2000,
    ctl: 1800,
    soreness: 5,
    fatigue: 7,
    sleep_dur: 4.5,
    sleep_qual: 3,
    readiness: 4,
    stress: 8
  }
};

function initApp() {
  updateSimulation();
  renderTimelineChart("TeamA-5cd7a61b (Forward, High Load)");
}

function loadPreset(presetName) {
  const preset = PRESETS[presetName];
  if (!preset) return;

  // Update slider inputs
  document.getElementById("slider-atl").value = preset.atl;
  document.getElementById("slider-ctl").value = preset.ctl;
  document.getElementById("slider-soreness").value = preset.soreness;
  document.getElementById("slider-fatigue").value = preset.fatigue;
  document.getElementById("slider-sleep-dur").value = preset.sleep_dur;
  document.getElementById("slider-sleep-qual").value = preset.sleep_qual;
  document.getElementById("slider-readiness").value = preset.readiness;
  document.getElementById("slider-stress").value = preset.stress;

  // Update active button state
  document.querySelectorAll(".preset-btn").forEach(btn => btn.classList.remove("active"));
  const clicked = event ? event.target : null;
  if (clicked) clicked.classList.add("active");

  updateSimulation();
}

function updateSimulation() {
  // 1. Read input values
  const atl = parseFloat(document.getElementById("slider-atl").value);
  const ctl = parseFloat(document.getElementById("slider-ctl").value);
  const soreness = parseFloat(document.getElementById("slider-soreness").value);
  const fatigue = parseFloat(document.getElementById("slider-fatigue").value);
  const sleepDur = parseFloat(document.getElementById("slider-sleep-dur").value);
  const sleepQual = parseFloat(document.getElementById("slider-sleep-qual").value);
  const readiness = parseFloat(document.getElementById("slider-readiness").value);
  const stress = parseFloat(document.getElementById("slider-stress").value);

  // 2. Update display labels
  document.getElementById("val-atl").innerText = atl.toLocaleString() + " sRPE";
  document.getElementById("val-ctl").innerText = ctl.toLocaleString() + " sRPE";
  document.getElementById("val-soreness").innerText = soreness + " / 10";
  document.getElementById("val-fatigue").innerText = fatigue + " / 10";
  document.getElementById("val-sleep-dur").innerText = sleepDur.toFixed(1) + " hrs";
  document.getElementById("val-sleep-qual").innerText = sleepQual + " / 10";
  document.getElementById("val-readiness").innerText = readiness + " / 10";
  document.getElementById("val-stress").innerText = stress + " / 10";

  // 3. Compute Acute:Chronic Workload Ratio (ACWR)
  const acwr = (atl / 7) / ((ctl / 7) + 0.0001);
  const acwrBadge = document.getElementById("badge-acwr");
  if (acwr >= 0.8 && acwr <= 1.3) {
    acwrBadge.className = "acwr-pill";
    acwrBadge.innerText = `${acwr.toFixed(2)} • Optimal Sweet Spot (0.8 - 1.3)`;
  } else if (acwr > 1.3 && acwr <= 1.5) {
    acwrBadge.className = "acwr-pill warning";
    acwrBadge.innerText = `${acwr.toFixed(2)} • Moderate Workload Surge`;
  } else if (acwr > 1.5) {
    acwrBadge.className = "acwr-pill danger";
    acwrBadge.innerText = `${acwr.toFixed(2)} • Danger Zone (> 1.5 ACWR)`;
  } else {
    acwrBadge.className = "acwr-pill warning";
    acwrBadge.innerText = `${acwr.toFixed(2)} • Under-Training / Deload`;
  }

  // 4. Compute TreeSHAP risk attributions & Probability
  // Baseline log-odds for ~1.5% base prevalence is -4.18
  let baseLogOdds = -4.18;
  const contributions = [];

  // Readiness contribution (Dominant factor)
  const readinessShap = (7.0 - readiness) * 0.38;
  contributions.push({
    name: "Readiness to Train (" + readiness + "/10)",
    value: readinessShap,
    isPositive: readinessShap > 0
  });

  // ACWR / Workload surge contribution
  let acwrShap = 0;
  if (acwr > 1.3) {
    acwrShap = (acwr - 1.3) * 1.6;
  } else if (acwr < 0.8) {
    acwrShap = -0.25;
  } else {
    acwrShap = -0.45;
  }
  contributions.push({
    name: "ACWR Ratio (" + acwr.toFixed(2) + ")",
    value: acwrShap,
    isPositive: acwrShap > 0
  });

  // Soreness contribution
  const sorenessShap = (soreness - 3.0) * 0.26;
  contributions.push({
    name: "Muscle Soreness (" + soreness + "/10)",
    value: sorenessShap,
    isPositive: sorenessShap > 0
  });

  // Fatigue contribution
  const fatigueShap = (fatigue - 3.0) * 0.22;
  contributions.push({
    name: "Fatigue Score (" + fatigue + "/10)",
    value: fatigueShap,
    isPositive: fatigueShap > 0
  });

  // Sleep debt contribution
  const sleepShap = (7.5 - sleepDur) * 0.20 + (6.5 - sleepQual) * 0.12;
  contributions.push({
    name: "Sleep Debt & Quality (" + sleepDur + "h)",
    value: sleepShap,
    isPositive: sleepShap > 0
  });

  // Chronic fitness buffer
  const ctlBufferShap = -((ctl - 1200) / 3000) * 0.40;
  contributions.push({
    name: "Chronic Fitness Base (CTL)",
    value: ctlBufferShap,
    isPositive: ctlBufferShap > 0
  });

  // Total predicted log odds -> sigmoid probability
  let totalLogOdds = baseLogOdds;
  contributions.forEach(c => totalLogOdds += c.value);
  
  // Sigmoid with sports science calibration scale
  let riskProb = 1.0 / (1.0 + Math.exp(-totalLogOdds));
  riskProb = Math.min(Math.max(riskProb, 0.005), 0.95);

  // 5. Update Risk Display
  const riskPctEl = document.getElementById("risk-pct");
  const riskPill = document.getElementById("risk-pill");
  const riskBar = document.getElementById("risk-progress-bar");
  
  const riskPctStr = (riskProb * 100).toFixed(1) + "%";
  riskPctEl.innerText = riskPctStr;
  riskBar.style.width = Math.min(riskProb * 100 * 1.5, 100) + "%";

  if (riskProb < 0.05) {
    riskPill.className = "gauge-pill";
    riskPill.innerText = "Low Risk";
    riskBar.className = "risk-bar-fill";
  } else if (riskProb < 0.20) {
    riskPill.className = "gauge-pill moderate";
    riskPill.innerText = "Moderate Risk";
    riskBar.className = "risk-bar-fill moderate";
  } else {
    riskPill.className = "gauge-pill elevated";
    riskPill.innerText = "Elevated Risk";
    riskBar.className = "risk-bar-fill elevated";
  }

  // 6. Compute Next-Day Readiness Forecast (Regression)
  // Base readiness ~ 7.2, adjusted by fatigue, soreness, sleep, stress
  let forecastReadiness = 7.0 + 
    (sleepDur - 7.5) * 0.45 + 
    (sleepQual - 6.0) * 0.35 - 
    (fatigue - 3.0) * 0.50 - 
    (soreness - 3.0) * 0.35 - 
    (stress - 3.0) * 0.25 - 
    Math.max(0, acwr - 1.4) * 0.8;
  
  forecastReadiness = Math.min(Math.max(forecastReadiness, 1.0), 10.0);
  
  const readScoreEl = document.getElementById("readiness-score");
  const readPill = document.getElementById("readiness-pill");
  const readBar = document.getElementById("readiness-progress-bar");
  
  readScoreEl.innerText = forecastReadiness.toFixed(1);
  readBar.style.width = (forecastReadiness * 10) + "%";
  
  if (forecastReadiness >= 7.0) {
    readPill.innerText = "High Readiness";
    readPill.style.background = "rgba(16, 185, 129, 0.2)";
    readPill.style.color = "#34d399";
  } else if (forecastReadiness >= 4.5) {
    readPill.innerText = "Moderate Readiness";
    readPill.style.background = "rgba(245, 158, 11, 0.2)";
    readPill.style.color = "#fbbf24";
  } else {
    readPill.innerText = "Low Readiness Warning";
    readPill.style.background = "rgba(239, 68, 68, 0.2)";
    readPill.style.color = "#f87171";
  }

  // 7. Update Coaching Alert Box
  updateCoachingAlert(riskProb, forecastReadiness, acwr, soreness, sleepDur);

  // 8. Render SHAP Waterfall Bars
  renderShapWaterfall(contributions);
}

function updateCoachingAlert(risk, readiness, acwr, soreness, sleep) {
  const alertBox = document.getElementById("coach-alert");
  const alertIcon = document.getElementById("coach-icon");
  const alertHeading = document.getElementById("coach-heading");
  const alertMessage = document.getElementById("coach-message");

  if (risk >= 0.20 || readiness <= 4.0) {
    alertBox.className = "alert-box danger";
    alertIcon.innerText = "🚨";
    alertHeading.innerText = "Elevated Injury Risk Warning";
    let reasons = [];
    if (acwr > 1.4) reasons.push("acute workload surge (" + acwr.toFixed(2) + " ACWR)");
    if (soreness >= 6) reasons.push("severe muscle soreness");
    if (readiness <= 4) reasons.push("low subjective readiness");
    if (sleep < 6) reasons.push("sleep deficit");
    alertMessage.innerText = "High risk flagged due to " + reasons.join(", ") + ". Recommendation: Deload upcoming session volume, limit maximal sprint exposure, and implement active recovery.";
  } else if (risk >= 0.05 || readiness <= 5.5) {
    alertBox.className = "alert-box warning";
    alertIcon.innerText = "⚠️";
    alertHeading.innerText = "Moderate Risk & Recovery Caution";
    alertMessage.innerText = "Athlete shows elevated fatigue accumulation. Maintain standard drill volume but monitor neuromuscular fatigue closely during small-sided games.";
  } else {
    alertBox.className = "alert-box";
    alertIcon.innerText = "✅";
    alertHeading.innerText = "Optimal Training Condition";
    alertMessage.innerText = "Workload and recovery indicators are well balanced. Athlete is fully cleared for full match-intensity training drills.";
  }
}

function renderShapWaterfall(contributions) {
  const container = document.getElementById("waterfall-container");
  container.innerHTML = "";

  // Sort by absolute impact
  const sorted = [...contributions].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  const maxAbs = Math.max(...sorted.map(c => Math.abs(c.value)), 0.5);

  sorted.forEach(item => {
    const row = document.createElement("div");
    row.className = "waterfall-item";

    const label = document.createElement("div");
    label.className = "wf-label";
    label.innerText = item.name;

    const barWrapper = document.createElement("div");
    barWrapper.className = "wf-bar-wrapper";

    const bar = document.createElement("div");
    const barWidth = Math.min((Math.abs(item.value) / maxAbs) * 100, 100);
    bar.className = "wf-bar " + (item.isPositive ? "positive" : "negative");
    bar.style.width = barWidth.toFixed(1) + "%";
    barWrapper.appendChild(bar);

    const val = document.createElement("div");
    val.className = "wf-val " + (item.isPositive ? "positive" : "negative");
    val.innerText = (item.isPositive ? "+" : "") + item.value.toFixed(2);

    row.appendChild(label);
    row.appendChild(barWrapper);
    row.appendChild(val);
    container.appendChild(row);
  });
}

function switchAthleteTimeline() {
  const select = document.getElementById("athlete-select");
  renderTimelineChart(select.value);
}

function renderTimelineChart(athleteKey) {
  if (typeof SOCCERMON_TIMELINES === "undefined") return;
  const ath = SOCCERMON_TIMELINES[athleteKey];
  if (!ath) return;

  const ctx = document.getElementById("timelineChart").getContext("2d");
  if (currentTimelineChart) {
    currentTimelineChart.destroy();
  }

  // Downsample to weekly points for smooth rendering
  const step = 4;
  const labels = [];
  const loadData = [];
  const atlData = [];
  const ctlData = [];
  const acwrData = [];
  const injuryPoints = [];

  for (let i = 0; i < ath.dates.length; i += step) {
    labels.push(ath.dates[i]);
    loadData.push(ath.daily_load[i]);
    atlData.push(ath.atl_7d[i]);
    ctlData.push(ath.ctl_28d[i]);
    acwrData.push(ath.acwr[i]);

    // Check if any injury occurred in this step window
    let hadInj = 0;
    for (let j = i; j < Math.min(i + step, ath.dates.length); j++) {
      if (ath.injuries[j] === 1) hadInj = 1;
    }
    injuryPoints.push(hadInj ? atlData[atlData.length - 1] : null);
  }

  currentTimelineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Daily Load (sRPE)",
          type: "bar",
          data: loadData,
          backgroundColor: "rgba(148, 163, 184, 0.25)",
          borderWidth: 0,
          yAxisID: "y"
        },
        {
          label: "ATL (7-Day Acute)",
          data: atlData,
          borderColor: "#3b82f6",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          yAxisID: "y"
        },
        {
          label: "CTL (28-Day Chronic)",
          data: ctlData,
          borderColor: "#10b981",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          yAxisID: "y"
        },
        {
          label: "ACWR Ratio",
          data: acwrData,
          borderColor: "#f59e0b",
          borderWidth: 1.8,
          pointRadius: 0,
          borderDash: [4, 4],
          tension: 0.2,
          yAxisID: "y1"
        },
        {
          label: "Reported Injury Event",
          data: injuryPoints,
          pointStyle: "circle",
          pointRadius: 6,
          pointBackgroundColor: "#ef4444",
          borderColor: "#fff",
          borderWidth: 2,
          showLine: false,
          yAxisID: "y"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleFont: { family: "Outfit", size: 13, weight: "bold" },
          bodyFont: { family: "Plus Jakarta Sans", size: 12 },
          borderColor: "rgba(255, 255, 255, 0.1)",
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: { color: "#64748b", font: { size: 10 }, maxTicksLimit: 12 }
        },
        y: {
          position: "left",
          title: { display: true, text: "Workload (sRPE)", color: "#94a3b8", font: { size: 11, weight: "bold" } },
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: { color: "#64748b", font: { size: 10 } }
        },
        y1: {
          position: "right",
          title: { display: true, text: "ACWR Ratio", color: "#f59e0b", font: { size: 11, weight: "bold" } },
          min: 0,
          max: 3.0,
          grid: { drawOnChartArea: false },
          ticks: { color: "#f59e0b", font: { size: 10 } }
        }
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", initApp);
