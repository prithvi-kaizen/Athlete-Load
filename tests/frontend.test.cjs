const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const source = fs.readFileSync(path.join(root, "app.js"), "utf8");

function element() {
  const classes = new Set();
  return {
    textContent: "",
    innerText: "",
    className: "",
    children: [],
    options: [],
    disabled: true,
    style: { setProperty() {} },
    attributes: {},
    classList: {
      add: (value) => classes.add(value),
      remove: (value) => classes.delete(value),
      contains: (value) => classes.has(value),
      toggle(value, selected) {
        if (selected) classes.add(value);
        else classes.delete(value);
      },
    },
    setAttribute(key, value) {
      this.attributes[key] = value;
    },
    addEventListener() {},
    appendChild(child) {
      this.children.push(child);
    },
    replaceChildren() {
      this.children = [];
      this.options = [];
    },
    add(option) {
      this.options.push(option);
    },
    insertRow() {
      const row = element();
      row.insertCell = () => {
        const cell = element();
        row.children.push(cell);
        return cell;
      };
      this.children.push(row);
      return row;
    },
  };
}

function fixture(dataSource = "") {
  const nodes = new Map(
    [...html.matchAll(/id="([^"]+)"/g)].map((match) => [match[1], element()]),
  );
  const ranges = [...html.matchAll(/<input\s+type="range"[\s\S]*?\/>/g)].map(
    (match) => {
      const attrs = Object.fromEntries(
        [...match[0].matchAll(/([\w-]+)="([^"]+)"/g)].map((value) => [
          value[1],
          value[2],
        ]),
      );
      const input = nodes.get(attrs.id);
      Object.assign(input, attrs);
      return input;
    },
  );
  const presets = ["recovered", "spike", "overtraining", "sleep_debt"].map(
    (preset) => Object.assign(element(), { dataset: { preset } }),
  );
  nodes
    .get("athlete-select")
    .options.push({ textContent: "Loading athlete records" });
  const context = vm.createContext({
    console,
    setTimeout,
    Blob,
    URL,
    Option: function (text, value) {
      this.text = text;
      this.value = value;
    },
    window: { addEventListener() {} },
    document: {
      getElementById: (id) => {
        assert.ok(nodes.has(id), `Unknown element: ${id}`);
        return nodes.get(id);
      },
      querySelectorAll: (selector) =>
        selector.includes("range") ? ranges : presets,
      querySelector: () => Object.assign(element(), { open: false }),
      createElement: () => element(),
      addEventListener() {},
    },
  });
  vm.runInContext(dataSource, context);
  vm.runInContext(source, context);
  return { context, nodes, presets };
}

const exportedData = fs.readFileSync(path.join(root, "data.js"), "utf8");

test("presets update all outputs without a browser event global", () => {
  const { context, nodes, presets } = fixture();
  context.loadPreset("recovered");
  assert.equal(nodes.get("risk-pct").innerText, "0.5%");
  assert.equal(nodes.get("readiness-score").innerText, "9.3");
  assert.equal(presets[0].attributes["aria-pressed"], "true");
  context.loadPreset("overtraining");
  assert.equal(nodes.get("risk-pct").innerText, "76.9%");
  assert.equal(nodes.get("readiness-score").innerText, "1.0");
  assert.equal(presets[0].attributes["aria-pressed"], "false");
  assert.equal(presets[2].attributes["aria-pressed"], "true");
  assert.equal(nodes.get("waterfall-container").children.length, 6);
});

test("missing data shows actionable errors while simulator still works", () => {
  const { context, nodes } = fixture();
  context.initApp();
  assert.match(nodes.get("timeline-status").textContent, /could not load/);
  assert.equal(nodes.get("athlete-select").disabled, true);
  assert.equal(nodes.get("download-history").disabled, true);
  assert.match(
    nodes.get("benchmark-body").children[0].children[0].textContent,
    /CSV download/,
  );
  assert.match(
    nodes.get("statistics-body").children[0].children[0].textContent,
    /could not load/,
  );
  assert.equal(nodes.get("risk-pct").innerText, "0.5%");
});

test("empty export shows explicit empty states and disables athlete actions", () => {
  const { context, nodes } = fixture(
    "const SOCCERMON_TIMELINES = {}; const MODEL_BENCHMARKS = []; const STATISTICAL_TESTS = [];",
  );
  context.initApp();
  assert.match(nodes.get("timeline-status").textContent, /No athlete records/);
  assert.match(
    nodes.get("benchmark-body").children[0].children[0].textContent,
    /No test results/,
  );
  assert.match(
    nodes.get("statistics-body").children[0].children[0].textContent,
    /No statistical signals/,
  );
  assert.equal(nodes.get("athlete-select").disabled, true);
});

test("chart-library failure preserves summaries and CSV access", () => {
  const { context, nodes } = fixture(exportedData);
  context.initializeAthletes();
  assert.match(
    nodes.get("timeline-status").textContent,
    /chart library could not load/,
  );
  assert.match(
    nodes.get("timeline-summary").textContent,
    /731 daily records \/ 45 injury reports/,
  );
  assert.equal(nodes.get("athlete-select").options.length, 4);
  assert.equal(nodes.get("download-history").disabled, false);
});

test("research tables use exported test metrics, sorted by primary score", () => {
  const { context, nodes } = fixture(exportedData);
  context.populateResearchTables();
  const rows = nodes.get("benchmark-body").children;
  assert.equal(rows.length, 4);
  assert.equal(rows[0].children[0].textContent, "XGBoost");
  assert.equal(rows[0].children[1].textContent, "0.0391");
  assert.equal(rows[0].children[4].textContent, "1.18%");
  assert.equal(nodes.get("statistics-body").children.length, 5);
});
