import { copyFileSync, writeFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath, pathToFileURL } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const playwrightEntry = pathToFileURL(
  resolve(__dirname, "../frontend/node_modules/playwright/index.mjs"),
).href;
const { chromium } = await import(playwrightEntry);

const API = process.env.SETU_API_URL ?? "http://127.0.0.1:8000";
const UI = process.env.SETU_UI_URL ?? "http://127.0.0.1:5173";
const SCRATCH = process.env.SCRATCH_DIR ?? "/tmp/grok-goal-ff8428ca3705/implementer";
const GATE = process.env.SETU_GATE_NAME ?? "browser";
const BROWSER_LOG =
  process.env.SETU_BROWSER_LOG ?? `${SCRATCH}/${GATE}_browser.log`;
const COLD_START = process.env.SETU_BROWSER_COLD_START === "1";
const RUNS = COLD_START ? 1 : 2;
const log = [];

const SCENARIO_RE = /Scenario MALACCA: cascade [a-f0-9]{8}… → \d+ options/;

function isBenignConsoleError(text) {
  return (
    /favicon/i.test(text) ||
    /Failed to load resource.*\b404\b/i.test(text) ||
    /net::ERR_/i.test(text) ||
    /tile.*error/i.test(text)
  );
}

function healthOk(health) {
  return health?.status === "ok" && health?.version === "1.0.0" && health?.phase === 8;
}

async function waitForForecast(page) {
  await page.waitForFunction(
    () => {
      const panel = document.querySelector("#forecast-panel");
      if (!panel) return false;
      const text = panel.textContent ?? "";
      return text.length > 0 && !text.includes("No forecasts");
    },
    { timeout: COLD_START ? 180_000 : 60_000 },
  );
}

async function runOnce(label) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  page.setDefaultTimeout(COLD_START ? 180_000 : 60_000);
  let bootstrapPipelinePost = false;
  let bootstrapForecastPost = false;
  let dbEmptyBeforeLoad = false;
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (msg) => {
    if (msg.type() === "error" && !isBenignConsoleError(msg.text())) {
      errors.push(msg.text());
    }
  });

  let grid = 0;
  let markerCount = 0;
  let mapBox = null;
  let scrubChanged = false;
  let forecastOk = false;
  let scenarioOk = false;
  let capeBadgeOk = false;
  let polylineOk = false;
  let healthPass = false;

  const loadTimeout = COLD_START ? 180_000 : 60_000;

  try {
    if (COLD_START) {
      const [scoresRes, forecastsRes] = await Promise.all([
        fetch(`${API}/api/risk-scores/latest`),
        fetch(`${API}/api/forecast/latest`),
      ]);
      const scores = await scoresRes.json();
      const forecasts = await forecastsRes.json();
      dbEmptyBeforeLoad = scores.length === 0 && forecasts.length === 0;
      log.push(
        `${label}: pre_load_scores=${scores.length} pre_load_forecasts=${forecasts.length} db_empty_before_load=${dbEmptyBeforeLoad}`,
      );

      page.on("request", (req) => {
        const url = req.url();
        const method = req.method();
        if (method === "POST" && url.includes("/api/pipeline/run")) {
          bootstrapPipelinePost = true;
        }
        if (method === "POST" && url.includes("/api/forecast/run")) {
          bootstrapForecastPost = true;
        }
      });
    }

    await page.goto(UI, { waitUntil: "domcontentloaded", timeout: 90_000 });
    await page.waitForSelector("#dashboard-root, .text-slate-400", { timeout: loadTimeout });
    await waitForForecast(page);
    await page.waitForSelector("#dashboard-root", { timeout: loadTimeout });

    const health = await fetch(`${API}/health`).then((r) => r.json());
    healthPass = healthOk(health);
    log.push(`${label}: health=${JSON.stringify(health)} health_ok=${healthPass}`);

    grid = await page.locator("#corridor-score-grid > div").count();
    log.push(`${label}: dashboard_score_cards=${grid}`);

    await page.getByRole("button", { name: "Map" }).click();
    await page.waitForSelector("#setu-map-container .leaflet-container", { timeout: 30_000 });
    await page.waitForSelector("#cape-overlay-badge", { timeout: 10_000 });

    const badgeText = await page.locator("#cape-overlay-badge").innerText();
    capeBadgeOk = badgeText.includes("Cape reroute overlay (demo ASSUMPTION)");
    log.push(`${label}: cape_badge=${capeBadgeOk}`);

    markerCount = await page.locator("#setu-map-container .leaflet-interactive").count();
    const polylines = await page
      .locator("#setu-map-container svg path.leaflet-interactive")
      .count();
    polylineOk = polylines >= 2;
    mapBox = await page.locator("#setu-map-container").boundingBox();
    log.push(
      `${label}: map_markers=${markerCount} polylines=${polylines} map_bbox=${JSON.stringify(mapBox)}`,
    );

    const mapShot = `${SCRATCH}/phase6_browser_map_${label}.png`;
    await page.screenshot({ path: mapShot });
    if (label === "run1") {
      copyFileSync(mapShot, `${SCRATCH}/phase6_browser_load.png`);
    }

    await page.getByRole("button", { name: "Backtest Replay" }).click();
    await page.waitForSelector("#replay-scrub", { timeout: 20_000 });
    const before = await page.locator("#replay-timeline-card").innerText();
    const slider = page.locator("#replay-scrub");
    await slider.fill("40");
    await slider.dispatchEvent("input");
    await page.waitForFunction(
      (prev) => {
        const card = document.querySelector("#replay-timeline-card");
        return card && card.textContent !== prev;
      },
      before,
      { timeout: 10_000 },
    );
    const after = await page.locator("#replay-timeline-card").innerText();
    scrubChanged = before !== after;
    log.push(`${label}: replay_scrub_changed=${scrubChanged}`);

    await page.getByRole("button", { name: "Dashboard" }).click();
    await page.waitForSelector("#forecast-panel", { timeout: 20_000 });
    await waitForForecast(page);
    const forecastText = await page.locator("#forecast-panel").innerText();
    forecastOk = !forecastText.includes("No forecasts");
    log.push(`${label}: forecast_populated=${forecastOk}`);

    await page.locator("#scenario-corridor-select").selectOption("MALACCA");
    const scenarioResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes("/api/recommendations/run") && resp.request().method() === "POST",
      { timeout: 120_000 },
    );
    await page.getByRole("button", { name: /Run MALACCA cascade/ }).click();
    await scenarioResponse;
    const scenarioText = await page.locator("#scenario-controls").innerText();
    scenarioOk = SCENARIO_RE.test(scenarioText);
    log.push(`${label}: scenario_result=${scenarioOk} text=${scenarioText.slice(0, 80)}`);

    log.push(`${label}: page_errors=${errors.length}`);
    if (errors.length) log.push(...errors.map((e) => `ERR: ${e}`));

    if (COLD_START) {
      log.push(`${label}: bootstrap_pipeline_post=${bootstrapPipelinePost}`);
      log.push(`${label}: bootstrap_forecast_post=${bootstrapForecastPost}`);
      const bootstrapFromEmpty =
        dbEmptyBeforeLoad && bootstrapPipelinePost && bootstrapForecastPost;
      log.push(`${label}: bootstrap_from_empty_db=${bootstrapFromEmpty}`);
    }

    const coldBootstrapOk =
      !COLD_START ||
      (dbEmptyBeforeLoad && bootstrapPipelinePost && bootstrapForecastPost);

    return (
    errors.length === 0 &&
    healthPass &&
    mapBox &&
    mapBox.width >= 700 &&
    markerCount >= 5 &&
    grid >= 3 &&
    forecastOk &&
    scrubChanged &&
    scenarioOk &&
    capeBadgeOk &&
    polylineOk &&
    coldBootstrapOk
    );
  } catch (err) {
    log.push(`${label}: fatal=${err.message ?? err}`);
    return false;
  } finally {
    await browser.close();
  }
}

const results = [];
for (let i = 0; i < RUNS; i += 1) {
  const label = COLD_START ? "cold" : `run${i + 1}`;
  results.push(await runOnce(label));
}

const ok = results.every(Boolean);
const lastLabel = COLD_START ? "cold" : `run${RUNS}`;
const summaryLines = log.filter((line) => line.startsWith(`${lastLabel}:`));
const capeLine = summaryLines.find((l) => l.includes("cape_badge="));
const forecastLine = summaryLines.find((l) => l.includes("forecast_populated="));
const markersLine = summaryLines.find((l) => l.includes("map_markers="));
const errorsLine = summaryLines.find((l) => l.includes("page_errors="));

const bootstrapLines = COLD_START
  ? log.filter(
      (line) =>
        line.includes("db_empty_before_load=") ||
        line.includes("bootstrap_pipeline_post=") ||
        line.includes("bootstrap_forecast_post=") ||
        line.includes("bootstrap_from_empty_db="),
    )
  : [];

const body =
  `api=${API}\nui=${UI}\ngate=${GATE}\ncold_start=${COLD_START}\n` +
  log.join("\n") +
  `\nconsistent=${ok}\n` +
  `${capeLine ?? "cape_badge=false"}\n` +
  `${forecastLine ?? "forecast_populated=false"}\n` +
  `${markersLine ?? "map_markers=0"}\n` +
  `${errorsLine ?? "page_errors=1"}\n` +
  (COLD_START
    ? bootstrapLines
        .map((line) => line.replace(/^cold: /, ""))
        .join("\n") + "\n"
    : "");
writeFileSync(BROWSER_LOG, body);
process.exit(ok ? 0 : 1);