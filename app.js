// AthleteLoad scenario illustration and exported research explorer.

// Global State
let currentTimelineChart = null;
let scene, camera, renderer, controls;
let athleteMeshGroup = null;
let anatomicalParts = {};
let pitchGrid = null;
let animationFrameId = null;

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
    stress: 2,
  },
  spike: {
    atl: 3600,
    ctl: 1900,
    soreness: 6,
    fatigue: 5,
    sleep_dur: 7.0,
    sleep_qual: 6,
    readiness: 5,
    stress: 5,
  },
  overtraining: {
    atl: 3400,
    ctl: 1800,
    soreness: 8,
    fatigue: 8,
    sleep_dur: 6.0,
    sleep_qual: 4,
    readiness: 3,
    stress: 7,
  },
  sleep_debt: {
    atl: 2000,
    ctl: 1800,
    soreness: 5,
    fatigue: 7,
    sleep_dur: 4.5,
    sleep_qual: 3,
    readiness: 4,
    stress: 8,
  },
};

// -----------------------------------------------------------------------------
// Initialization
// -----------------------------------------------------------------------------
function initApp() {
  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", () => loadPreset(button.dataset.preset));
  });
  document.querySelectorAll('input[type="range"]').forEach((input) => {
    input.addEventListener("input", () => {
      document.querySelectorAll("[data-preset]").forEach((button) => {
        button.classList.remove("active");
        button.setAttribute("aria-pressed", "false");
      });
      document.getElementById("scenario-name").textContent = "Custom scenario";
      updateSimulation();
    });
  });
  document
    .getElementById("reset-scenario")
    .addEventListener("click", () => loadPreset("recovered"));
  document
    .getElementById("reset-camera")
    .addEventListener("click", reset3DCamera);
  document
    .getElementById("athlete-select")
    .addEventListener("change", switchAthleteTimeline);
  document
    .getElementById("download-history")
    .addEventListener("click", downloadAthleteHistory);
  document
    .querySelector(".anatomy-details")
    .addEventListener("toggle", (event) => {
      if (event.target.open && !renderer) {
        try {
          if (typeof THREE === "undefined")
            throw new Error("3D library unavailable");
          init3DScene();
          document.getElementById("three-status").textContent = "";
          updateSimulation();
        } catch {
          document.getElementById("three-status").textContent =
            "The 3D view could not load. Check your connection and WebGL support, then reload. All scenario controls still work.";
        }
      }
      if (event.target.open) {
        onWindowResize();
        if (renderer && animationFrameId === null) animate3D();
      } else {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
    });
  loadPreset("recovered");
  populateResearchTables();
  initializeAthletes();
  window.addEventListener("resize", onWindowResize);
}

// -----------------------------------------------------------------------------
// 3D Three.js Biomechanics Scene Setup
// -----------------------------------------------------------------------------
function init3DScene() {
  const container = document.getElementById("three-container");
  if (!container || typeof THREE === "undefined") return;

  // Scene
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x222a25, 0.08);

  // Camera
  const width = container.clientWidth;
  const height = container.clientHeight;
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 1.2, 4.2);

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.replaceChildren();
  container.appendChild(renderer.domElement);

  // Orbit Controls
  if (typeof THREE.OrbitControls !== "undefined") {
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.1;
    controls.minDistance = 2.0;
    controls.maxDistance = 7.0;
    controls.target.set(0, 1.0, 0);
  }

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const mainLight = new THREE.DirectionalLight(0xf4f1ea, 1.2);
  mainLight.position.set(3, 5, 4);
  scene.add(mainLight);

  const rimLight = new THREE.DirectionalLight(0x909e89, 0.8);
  rimLight.position.set(-3, 3, -3);
  scene.add(rimLight);

  // Build 3D Biomechanical Athlete Body
  buildAthleteModel();

  // Animation Loop
  animate3D();
}

function buildAthleteModel() {
  athleteMeshGroup = new THREE.Group();

  // Helper Material Generator
  function createBiomechMat(baseColor) {
    return new THREE.MeshStandardMaterial({
      color: baseColor,
      roughness: 0.35,
      metalness: 0.4,
      wireframe: false,
      emissive: baseColor,
      emissiveIntensity: 0.25,
    });
  }

  const defaultColor = 0x799781;
  const jointColor = 0xb9c6b7;

  // 1. Head
  const headGeo = new THREE.SphereGeometry(0.13, 24, 24);
  const headMat = createBiomechMat(defaultColor);
  const head = new THREE.Mesh(headGeo, headMat);
  head.position.set(0, 1.82, 0);
  athleteMeshGroup.add(head);
  anatomicalParts.head = head;

  // 2. Neck
  const neckGeo = new THREE.CylinderGeometry(0.045, 0.05, 0.08, 16);
  const neckMat = createBiomechMat(0x64748b);
  const neck = new THREE.Mesh(neckGeo, neckMat);
  neck.position.set(0, 1.71, 0);
  athleteMeshGroup.add(neck);

  // 3. Torso / Chest
  const chestGeo = new THREE.CylinderGeometry(0.17, 0.13, 0.35, 20);
  const chestMat = createBiomechMat(defaultColor);
  const chest = new THREE.Mesh(chestGeo, chestMat);
  chest.position.set(0, 1.5, 0);
  athleteMeshGroup.add(chest);
  anatomicalParts.chest = chest;

  // 4. Pelvis / Hips
  const pelvisGeo = new THREE.CylinderGeometry(0.13, 0.15, 0.18, 18);
  const pelvisMat = createBiomechMat(defaultColor);
  const pelvis = new THREE.Mesh(pelvisGeo, pelvisMat);
  pelvis.position.set(0, 1.25, 0);
  athleteMeshGroup.add(pelvis);
  anatomicalParts.pelvis = pelvis;

  // 5. Left & Right Thighs (Hamstrings / Quads)
  const thighGeo = new THREE.CylinderGeometry(0.065, 0.05, 0.38, 16);

  const leftThighMat = createBiomechMat(defaultColor);
  const leftThigh = new THREE.Mesh(thighGeo, leftThighMat);
  leftThigh.position.set(-0.11, 0.96, 0);
  athleteMeshGroup.add(leftThigh);
  anatomicalParts.leftThigh = leftThigh;

  const rightThighMat = createBiomechMat(defaultColor);
  const rightThigh = new THREE.Mesh(thighGeo, rightThighMat);
  rightThigh.position.set(0.11, 0.96, 0);
  athleteMeshGroup.add(rightThigh);
  anatomicalParts.rightThigh = rightThigh;

  // 6. Left & Right Knee Joints (Hotspot spheres)
  const kneeGeo = new THREE.SphereGeometry(0.058, 20, 20);

  const leftKneeMat = createBiomechMat(jointColor);
  const leftKnee = new THREE.Mesh(kneeGeo, leftKneeMat);
  leftKnee.position.set(-0.11, 0.74, 0.01);
  athleteMeshGroup.add(leftKnee);
  anatomicalParts.leftKnee = leftKnee;

  const rightKneeMat = createBiomechMat(jointColor);
  const rightKnee = new THREE.Mesh(kneeGeo, rightKneeMat);
  rightKnee.position.set(0.11, 0.74, 0.01);
  athleteMeshGroup.add(rightKnee);
  anatomicalParts.rightKnee = rightKnee;

  // 7. Left & Right Calves / Shins
  const shinGeo = new THREE.CylinderGeometry(0.05, 0.04, 0.38, 16);

  const leftShinMat = createBiomechMat(defaultColor);
  const leftShin = new THREE.Mesh(shinGeo, leftShinMat);
  leftShin.position.set(-0.11, 0.52, 0);
  athleteMeshGroup.add(leftShin);
  anatomicalParts.leftShin = leftShin;

  const rightShinMat = createBiomechMat(defaultColor);
  const rightShin = new THREE.Mesh(shinGeo, rightShinMat);
  rightShin.position.set(0.11, 0.52, 0);
  athleteMeshGroup.add(rightShin);
  anatomicalParts.rightShin = rightShin;

  // 8. Feet
  const footGeo = new THREE.BoxGeometry(0.07, 0.05, 0.16);
  const footMat = createBiomechMat(0x475569);

  const leftFoot = new THREE.Mesh(footGeo, footMat);
  leftFoot.position.set(-0.11, 0.3, 0.04);
  athleteMeshGroup.add(leftFoot);

  const rightFoot = new THREE.Mesh(footGeo, footMat);
  rightFoot.position.set(0.11, 0.3, 0.04);
  athleteMeshGroup.add(rightFoot);

  // 9. Arms (Shoulders & Forearms)
  const armGeo = new THREE.CylinderGeometry(0.045, 0.038, 0.32, 14);

  const leftArmMat = createBiomechMat(defaultColor);
  const leftArm = new THREE.Mesh(armGeo, leftArmMat);
  leftArm.position.set(-0.25, 1.48, 0);
  leftArm.rotation.z = Math.PI / 16;
  athleteMeshGroup.add(leftArm);
  anatomicalParts.leftArm = leftArm;

  const rightArmMat = createBiomechMat(defaultColor);
  const rightArm = new THREE.Mesh(armGeo, rightArmMat);
  rightArm.position.set(0.25, 1.48, 0);
  rightArm.rotation.z = -Math.PI / 16;
  athleteMeshGroup.add(rightArm);
  anatomicalParts.rightArm = rightArm;

  scene.add(athleteMeshGroup);
}

function animate3D() {
  if (!document.querySelector(".anatomy-details").open) return;
  animationFrameId = requestAnimationFrame(animate3D);
  if (controls) {
    controls.update();
  }

  renderer.render(scene, camera);
}

function reset3DCamera() {
  if (camera && controls) {
    camera.position.set(0, 1.2, 4.2);
    controls.target.set(0, 1.0, 0);
    controls.update();
    if (athleteMeshGroup) {
      athleteMeshGroup.rotation.y = 0;
    }
  }
}

function onWindowResize() {
  const container = document.getElementById("three-container");
  if (!container || !renderer || !camera) return;

  const width = container.clientWidth;
  const height = container.clientHeight;

  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

// -----------------------------------------------------------------------------
// Dynamic 3D Biomechanical Heatmap Updater
// -----------------------------------------------------------------------------
function update3DHeatmap(riskProb, acwr, soreness, fatigue) {
  if (!anatomicalParts.leftThigh) return;

  // Colors
  const optimalGreen = new THREE.Color(0x799781);
  const warningAmber = new THREE.Color(0xb08b55);
  const dangerRed = new THREE.Color(0xab3f24);
  const telemetryCyan = new THREE.Color(0xb9c6b7);

  // Thigh & Knee (Hamstring & Knee strain from ACWR + Soreness)
  let legColor = optimalGreen;
  let legIntensity = 0.25;

  if (riskProb >= 0.2 || acwr > 1.5 || soreness >= 7) {
    legColor = dangerRed;
    legIntensity = 0.85;
  } else if (riskProb >= 0.05 || acwr > 1.3 || soreness >= 5) {
    legColor = warningAmber;
    legIntensity = 0.55;
  }

  // Apply to Thighs & Knees
  [anatomicalParts.leftThigh, anatomicalParts.rightThigh].forEach((mesh) => {
    mesh.material.color = legColor;
    mesh.material.emissive = legColor;
    mesh.material.emissiveIntensity = legIntensity;
  });

  [anatomicalParts.leftKnee, anatomicalParts.rightKnee].forEach((mesh) => {
    mesh.material.color = legColor === dangerRed ? dangerRed : telemetryCyan;
    mesh.material.emissive = legColor === dangerRed ? dangerRed : telemetryCyan;
    mesh.material.emissiveIntensity = legIntensity + 0.2;
  });

  // Torso / Fatigue
  let torsoColor = optimalGreen;
  let torsoIntensity = 0.25;
  if (fatigue >= 7) {
    torsoColor = fatigue >= 8.5 ? dangerRed : warningAmber;
    torsoIntensity = 0.6;
  }
  anatomicalParts.chest.material.color = torsoColor;
  anatomicalParts.chest.material.emissive = torsoColor;
  anatomicalParts.chest.material.emissiveIntensity = torsoIntensity;

  // Update HUD Telemetry
  const hudFocus = document.getElementById("hud-focus");
  const hudStrain = document.getElementById("hud-strain");

  if (riskProb >= 0.2 || acwr > 1.5) {
    hudFocus.innerText = "Hamstring & Knee Joint Hotspots (High Strain)";
    hudFocus.style.color = "#a33328";
    hudStrain.innerText = "Overload Warning (" + acwr.toFixed(2) + "x ACWR)";
    hudStrain.style.color = "#a33328";
  } else if (riskProb >= 0.05 || acwr > 1.3) {
    hudFocus.innerText = "Lower Extremities (Moderate Workload Accumulation)";
    hudFocus.style.color = "#805015";
    hudStrain.innerText = "Elevated (" + acwr.toFixed(2) + "x ACWR)";
    hudStrain.style.color = "#805015";
  } else {
    hudFocus.innerText = "Balanced workload illustration";
    hudFocus.style.color = "#426451";
    hudStrain.innerText = "Nominal (" + acwr.toFixed(2) + "x ACWR)";
    hudStrain.style.color = "#426451";
  }
}

// -----------------------------------------------------------------------------
// Interactive scenario formulas. These do not execute the trained model or SHAP.
// -----------------------------------------------------------------------------
function loadPreset(presetName) {
  const preset = PRESETS[presetName];
  if (!preset) return;

  document.getElementById("slider-atl").value = preset.atl;
  document.getElementById("slider-ctl").value = preset.ctl;
  document.getElementById("slider-soreness").value = preset.soreness;
  document.getElementById("slider-fatigue").value = preset.fatigue;
  document.getElementById("slider-sleep-dur").value = preset.sleep_dur;
  document.getElementById("slider-sleep-qual").value = preset.sleep_qual;
  document.getElementById("slider-readiness").value = preset.readiness;
  document.getElementById("slider-stress").value = preset.stress;

  document
    .querySelectorAll(".preset-pill")
    .forEach((btn) => btn.classList.remove("active"));
  document.querySelectorAll("[data-preset]").forEach((button) => {
    const selected = button.dataset.preset === presetName;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  const names = {
    recovered: "Recovered",
    spike: "Workload spike",
    overtraining: "High strain",
    sleep_debt: "Sleep deficit",
  };
  document.getElementById("scenario-name").textContent =
    names[presetName] + " scenario";

  updateSimulation();
}

function updateSimulation() {
  document.querySelectorAll('input[type="range"]').forEach((input) => {
    input.style.setProperty(
      "--fill",
      ((input.value - input.min) / (input.max - input.min)) * 100 + "%",
    );
  });
  const atl = parseFloat(document.getElementById("slider-atl").value);
  const ctl = parseFloat(document.getElementById("slider-ctl").value);
  const soreness = parseFloat(document.getElementById("slider-soreness").value);
  const fatigue = parseFloat(document.getElementById("slider-fatigue").value);
  const sleepDur = parseFloat(
    document.getElementById("slider-sleep-dur").value,
  );
  const sleepQual = parseFloat(
    document.getElementById("slider-sleep-qual").value,
  );
  const readiness = parseFloat(
    document.getElementById("slider-readiness").value,
  );
  const stress = parseFloat(document.getElementById("slider-stress").value);

  // Numerical display tags
  document.getElementById("val-atl").innerText = atl.toLocaleString() + " sRPE";
  document.getElementById("val-ctl").innerText = ctl.toLocaleString() + " sRPE";
  document.getElementById("val-soreness").innerText = soreness + " / 10";
  document.getElementById("val-fatigue").innerText = fatigue + " / 10";
  document.getElementById("val-sleep-dur").innerText =
    sleepDur.toFixed(1) + " hrs";
  document.getElementById("val-sleep-qual").innerText = sleepQual + " / 10";
  document.getElementById("val-readiness").innerText = readiness + " / 10";
  document.getElementById("val-stress").innerText = stress + " / 10";

  // ACWR calculation
  const acwr = atl / 7 / (ctl / 7 + 0.0001);
  const acwrBadge = document.getElementById("badge-acwr");
  const acwrPin = document.getElementById("acwr-pin");

  // Position pin (0.0 to 3.0 scale mapped to 0% to 100%)
  const pinLeft = Math.min(Math.max((acwr / 3.0) * 100, 2), 98);
  if (acwrPin) acwrPin.style.left = pinLeft.toFixed(1) + "%";

  if (acwr >= 0.8 && acwr <= 1.3) {
    acwrBadge.className = "acwr-tag";
    acwrBadge.innerText = `${acwr.toFixed(2)} / Balanced load`;
  } else if (acwr > 1.3 && acwr <= 1.5) {
    acwrBadge.className = "acwr-tag warning";
    acwrBadge.innerText = `${acwr.toFixed(2)} / Workload surge`;
  } else if (acwr > 1.5) {
    acwrBadge.className = "acwr-tag danger";
    acwrBadge.innerText = `${acwr.toFixed(2)} / High workload ratio`;
  } else {
    acwrBadge.className = "acwr-tag warning";
    acwrBadge.innerText = `${acwr.toFixed(2)} / Lower recent load`;
  }

  // Illustrative contributions to log-odds, retained from the original simulator.
  let baseLogOdds = -4.18; // Base rate ~1.5%
  const contributions = [];

  // 1. Readiness (Primary Driver)
  const readinessShap = (7.0 - readiness) * 0.38;
  contributions.push({
    name: "Readiness Score (" + readiness + "/10)",
    value: readinessShap,
    isPositive: readinessShap > 0,
  });

  // 2. ACWR Surge
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
    isPositive: acwrShap > 0,
  });

  // 3. Soreness
  const sorenessShap = (soreness - 3.0) * 0.26;
  contributions.push({
    name: "Muscle Soreness (" + soreness + "/10)",
    value: sorenessShap,
    isPositive: sorenessShap > 0,
  });

  // 4. Fatigue
  const fatigueShap = (fatigue - 3.0) * 0.22;
  contributions.push({
    name: "Fatigue Level (" + fatigue + "/10)",
    value: fatigueShap,
    isPositive: fatigueShap > 0,
  });

  // 5. Sleep Recovery Deficit
  const sleepShap = (7.5 - sleepDur) * 0.2 + (6.5 - sleepQual) * 0.12;
  contributions.push({
    name: "Sleep Recovery Deficit (" + sleepDur + "h)",
    value: sleepShap,
    isPositive: sleepShap > 0,
  });

  // 6. Chronic Fitness Baseline
  const ctlBufferShap = -((ctl - 1200) / 3000) * 0.4;
  contributions.push({
    name: "Chronic Fitness Base (CTL)",
    value: ctlBufferShap,
    isPositive: ctlBufferShap > 0,
  });

  // Compute Final Risk Probability via Sigmoid
  let totalLogOdds = baseLogOdds;
  contributions.forEach((c) => (totalLogOdds += c.value));
  let riskProb = 1.0 / (1.0 + Math.exp(-totalLogOdds));
  riskProb = Math.min(Math.max(riskProb, 0.005), 0.95);

  // Update Output Risk Gauge
  const riskPctEl = document.getElementById("risk-pct");
  const riskPill = document.getElementById("risk-pill");
  const riskBar = document.getElementById("risk-progress-bar");

  riskPctEl.innerText = (riskProb * 100).toFixed(1) + "%";
  riskBar.style.width = riskProb * 100 + "%";

  if (riskProb < 0.05) {
    riskPill.className = "risk-status-badge";
    riskPill.innerText = "Low Risk";
    riskBar.className = "meter-bar-fill";
  } else if (riskProb < 0.2) {
    riskPill.className = "risk-status-badge moderate";
    riskPill.innerText = "Moderate Risk";
    riskBar.className = "meter-bar-fill moderate";
  } else {
    riskPill.className = "risk-status-badge elevated";
    riskPill.innerText = "Elevated Risk";
    riskBar.className = "meter-bar-fill elevated";
  }

  // Next-Day Readiness Regression Forecast
  let forecastReadiness =
    7.0 +
    (sleepDur - 7.5) * 0.45 +
    (sleepQual - 6.0) * 0.35 -
    (fatigue - 3.0) * 0.5 -
    (soreness - 3.0) * 0.35 -
    (stress - 3.0) * 0.25 -
    Math.max(0, acwr - 1.4) * 0.8;
  forecastReadiness = Math.min(Math.max(forecastReadiness, 1.0), 10.0);

  const readScoreEl = document.getElementById("readiness-score");
  const readPill = document.getElementById("readiness-pill");
  const readBar = document.getElementById("readiness-progress-bar");

  readScoreEl.innerText = forecastReadiness.toFixed(1);
  readBar.style.width = forecastReadiness * 10 + "%";

  if (forecastReadiness >= 7.0) {
    readPill.innerText = "High";
    readPill.style.background = "#e4ebe2";
    readPill.style.color = "#426451";
  } else if (forecastReadiness >= 4.5) {
    readPill.innerText = "Moderate";
    readPill.style.background = "#f0e5cd";
    readPill.style.color = "#805015";
  } else {
    readPill.innerText = "Low";
    readPill.style.background = "#f4e2da";
    readPill.style.color = "#a33328";
  }

  // Update Coaching Alert Box
  updateCoachingAlert(riskProb, forecastReadiness, acwr, soreness, sleepDur);

  // Rank the illustrative contributions by magnitude.
  renderShapWaterfall(contributions);

  // Update 3D Three.js Biomechanical Model Heatmap
  update3DHeatmap(riskProb, acwr, soreness, fatigue);
}

function updateCoachingAlert(risk, readiness, acwr, soreness, sleep) {
  const alertCard = document.getElementById("coach-alert");
  const alertIcon = document.getElementById("coach-icon");
  const alertHeading = document.getElementById("coach-heading");
  const alertMessage = document.getElementById("coach-message");

  if (risk >= 0.2 || readiness <= 4.0) {
    alertCard.className = "advisory-card danger";
    alertIcon.innerText = "!";
    alertHeading.innerText = "Recovery is falling behind";
    let flags = [];
    if (acwr > 1.4)
      flags.push("acute workload spike (" + acwr.toFixed(2) + " ACWR)");
    if (soreness >= 6) flags.push("high muscle soreness");
    if (readiness <= 4) flags.push("low subjective readiness");
    if (sleep < 6) flags.push("sleep deficit");
    alertMessage.innerText =
      "This scenario combines " +
      (flags.join(", ") || "accumulated fatigue and reduced recovery") +
      ". Try lowering the acute load or improving recovery inputs to compare the response.";
  } else if (risk >= 0.05 || readiness <= 5.5) {
    alertCard.className = "advisory-card warning";
    alertIcon.innerText = "!";
    alertHeading.innerText = "Some recovery signals are under pressure";
    alertMessage.innerText =
      "Fatigue or workload is pushing the illustration upward. Compare this scenario with the recovered preset to see which inputs contribute most.";
  } else {
    alertCard.className = "advisory-card";
    alertIcon.innerText = "=";
    alertHeading.innerText = "Recovery in balance";
    alertMessage.innerText =
      "The current inputs produce a lower illustrative risk estimate. Increase the workload or reduce sleep to see how the balance changes.";
  }
}

function renderShapWaterfall(contributions) {
  const container = document.getElementById("waterfall-container");
  if (!container) return;
  container.replaceChildren();

  const sorted = [...contributions].sort(
    (a, b) => Math.abs(b.value) - Math.abs(a.value),
  );
  const maxAbs = Math.max(...sorted.map((c) => Math.abs(c.value)), 0.5);

  sorted.forEach((item) => {
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

// -----------------------------------------------------------------------------
// Longitudinal Timeline Explorer Chart.js
// -----------------------------------------------------------------------------
function switchAthleteTimeline() {
  const select = document.getElementById("athlete-select");
  renderTimelineChart(select.value);
}

function renderTimelineChart(athleteKey) {
  const status = document.getElementById("timeline-status");
  if (typeof SOCCERMON_TIMELINES === "undefined") {
    status.textContent =
      "Athlete records could not load. Reload the page to try again.";
    return;
  }
  const ath = SOCCERMON_TIMELINES[athleteKey];
  if (!ath || !ath.dates.length) {
    if (currentTimelineChart) {
      currentTimelineChart.destroy();
      currentTimelineChart = null;
    }
    status.textContent =
      "This record contains no daily observations. Choose another athlete.";
    document.getElementById("timeline-summary").textContent = "";
    document.getElementById("download-history").disabled = true;
    return;
  }
  const reports = ath.injuries.reduce((sum, value) => sum + value, 0);
  document.getElementById("timeline-summary").textContent =
    `${ath.dates.length.toLocaleString()} daily records / ${reports} injury reports`;
  document.getElementById("timeline-caption").textContent =
    `${ath.dates[0]} to ${ath.dates[ath.dates.length - 1]}. Chart sampled every four days; injury markers include all reports in each interval. Chronic load is shown as the weekly equivalent from the export.`;
  document.getElementById("download-history").disabled = false;
  if (typeof Chart === "undefined") {
    status.textContent =
      "The chart library could not load. Check your connection and reload, or download this athlete’s daily records below.";
    return;
  }
  status.textContent = "";

  const canvas = document.getElementById("timelineChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (currentTimelineChart) {
    currentTimelineChart.destroy();
  }

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
          backgroundColor: "#737a70",
          borderWidth: 0,
          yAxisID: "y",
        },
        {
          label: "ATL (7-Day Acute)",
          data: atlData,
          borderColor: "#ab3f24",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          yAxisID: "y",
        },
        {
          label: "CTL (28-Day Chronic)",
          data: ctlData,
          borderColor: "#426451",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          yAxisID: "y",
        },
        {
          label: "ACWR Ratio",
          data: acwrData,
          borderColor: "#76561d",
          borderWidth: 1.8,
          pointRadius: 0,
          borderDash: [4, 4],
          tension: 0.2,
          yAxisID: "y1",
        },
        {
          label: "Reported Injury Event",
          data: injuryPoints,
          pointStyle: "circle",
          pointRadius: 6,
          pointBackgroundColor: "#a33328",
          borderColor: "#fff",
          borderWidth: 2,
          showLine: false,
          yAxisID: "y",
        },
      ],
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(6, 9, 14, 0.95)",
          titleFont: { family: "DM Sans", size: 13, weight: "bold" },
          bodyFont: { family: "DM Sans", size: 12 },
          borderColor: "rgba(255, 255, 255, 0.1)",
          borderWidth: 1,
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: "#62665e",
            font: { size: 10 },
            maxTicksLimit: 6,
            maxRotation: 0,
          },
        },
        y: {
          position: "left",
          title: {
            display: true,
            text: "Workload (sRPE)",
            color: "#62665e",
            font: { size: 11 },
          },
          grid: { color: "#dedfd5" },
          ticks: { color: "#62665e", font: { size: 10 }, maxTicksLimit: 5 },
        },
        y1: {
          position: "right",
          title: {
            display: true,
            text: "ACWR",
            color: "#76561d",
            font: { size: 11 },
          },
          min: 0,
          suggestedMax: 3.0,
          grid: { drawOnChartArea: false },
          ticks: { color: "#76561d", font: { size: 10 }, maxTicksLimit: 5 },
        },
      },
    },
  });
}

function initializeAthletes() {
  const select = document.getElementById("athlete-select");
  if (typeof SOCCERMON_TIMELINES === "undefined") {
    document.getElementById("timeline-status").textContent =
      "Athlete records could not load. Check your connection and reload.";
    select.options[0].textContent = "Athlete records unavailable";
    return;
  }
  const keys = Object.keys(SOCCERMON_TIMELINES);
  select.replaceChildren();
  if (!keys.length) {
    select.add(new Option("No athlete records", ""));
    document.getElementById("timeline-status").textContent =
      "No athlete records are included in this data export.";
    return;
  }
  keys.forEach((key) => select.add(new Option(key, key)));
  select.disabled = false;
  renderTimelineChart(keys[0]);
}

function populateResearchTables() {
  const benchmarkBody = document.getElementById("benchmark-body");
  const statisticsBody = document.getElementById("statistics-body");
  function message(body, text, span) {
    body.replaceChildren();
    const row = body.insertRow();
    const cell = row.insertCell();
    cell.colSpan = span;
    cell.textContent = text;
  }
  if (typeof MODEL_BENCHMARKS === "undefined") {
    message(
      benchmarkBody,
      "Model results could not load. Use the CSV download or reload.",
      6,
    );
  } else {
    const rows = MODEL_BENCHMARKS.filter((row) => row.split === "Test").sort(
      (a, b) => b.pr_auc - a.pr_auc,
    );
    benchmarkBody.replaceChildren();
    if (!rows.length)
      message(benchmarkBody, "No test results are included in this export.", 6);
    rows.forEach((record, index) => {
      const row = benchmarkBody.insertRow();
      if (index === 0) row.className = "row-winner";
      [
        record.model,
        record.pr_auc.toFixed(4),
        record.roc_auc.toFixed(4),
        (record.recall * 100).toFixed(1) + "%",
        (record.precision * 100).toFixed(2) + "%",
        record.brier_score.toFixed(4),
      ].forEach((value) => {
        row.insertCell().textContent = value;
      });
    });
  }
  if (typeof STATISTICAL_TESTS === "undefined") {
    message(
      statisticsBody,
      "Statistical signals could not load. Use the CSV download or reload.",
      5,
    );
  } else {
    statisticsBody.replaceChildren();
    if (!STATISTICAL_TESTS.length)
      message(
        statisticsBody,
        "No statistical signals are included in this export.",
        5,
      );
    const labels = {
      readiness: "Readiness",
      recovery_deficit_index: "Recovery deficit",
      acwr: "Workload ratio (ACWR)",
      workload_soreness_interaction: "Workload × soreness",
      atl: "Acute training load",
    };
    STATISTICAL_TESTS.slice(0, 5).forEach((record) => {
      const row = statisticsBody.insertRow();
      [
        labels[record.variable] || record.variable.replaceAll("_", " "),
        record.injury_median.toFixed(2),
        record.healthy_median.toFixed(2),
        record.cliffs_delta.toFixed(3),
        record.effect_magnitude,
      ].forEach((value) => {
        row.insertCell().textContent = value;
      });
    });
  }
}

function downloadAthleteHistory() {
  const key = document.getElementById("athlete-select").value;
  if (typeof SOCCERMON_TIMELINES === "undefined" || !SOCCERMON_TIMELINES[key])
    return;
  const athlete = SOCCERMON_TIMELINES[key];
  const fields = Object.keys(athlete);
  const csv = [
    fields.join(","),
    ...athlete.dates.map((_, index) =>
      fields.map((field) => athlete[field][index]).join(","),
    ),
  ].join("\r\n");
  const url = URL.createObjectURL(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = key.split(" ")[0] + "-daily-records.csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

document.addEventListener("DOMContentLoaded", initApp);
