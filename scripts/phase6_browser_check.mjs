import { writeFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath, pathToFileURL } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const playwrightEntry = pathToFileURL(
  resolve(__dirname, "../frontend/node_modules/playwright/index.mjs"),
).href;
const { chromium } = await import(playwrightEntry);

const API = process.env.SETU_API_URL ?? "http://127.0.0.1:8000";
const UI = process.env.SETU_UI_URL ?? "http://127.0.0.1:5173";
const SCRATCH = process.env.SCRATCH_DIR ?? "/tmp/grok-goal-df3a238e5ed0/implementer";
const log = [];

async function runOnce(label) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  await page.goto(UI, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForSelector("#dashboard-root", { timeout: 30000 });

  const health = await fetch(`${API}/health`).then((r) => r.json());
  log.push(`${label}: health=${JSON.stringify(health)}`);

  const grid = await page.locator("#corridor-score-grid > div").count();
  log.push(`${label}: dashboard_score_cards=${grid}`);

  await page.getByRole("button", { name: "Map" }).click();
  await page.waitForSelector("#setu-map-container .leaflet-container", { timeout: 30000 });
  await page.waitForTimeout(1500);

  const markerCount = await page.locator("#setu-map-container .leaflet-interactive").count();
  const mapBox = await page.locator("#setu-map-container").boundingBox();
  log.push(`${label}: map_markers=${markerCount} map_bbox=${JSON.stringify(mapBox)}`);

  await page.screenshot({ path: `${SCRATCH}/phase6_browser_map_${label}.png` });

  await page.getByRole("button", { name: "Backtest Replay" }).click();
  await page.waitForSelector("#replay-scrub", { timeout: 20000 });
  const before = await page.locator("#replay-timeline-card").innerText();
  await page.locator("#replay-scrub").fill("40");
  await page.locator("#replay-scrub").dispatchEvent("input");
  await page.waitForTimeout(500);
  const after = await page.locator("#replay-timeline-card").innerText();
  log.push(`${label}: replay_scrub_changed=${before !== after}`);

  await page.getByRole("button", { name: "Dashboard" }).click();
  await page.waitForSelector("#forecast-panel", { timeout: 20000 });
  const forecastText = await page.locator("#forecast-panel").innerText();
  log.push(`${label}: forecast_populated=${!forecastText.includes("No forecasts")}`);

  await page.selectOption("select", "MALACCA");
  await page.getByRole("button", { name: /Run MALACCA cascade/ }).click();
  await page.waitForTimeout(10000);
  const scenarioText = await page.locator("#scenario-controls").innerText();
  log.push(`${label}: scenario_result=${scenarioText.includes("options")}`);

  log.push(`${label}: page_errors=${errors.length}`);
  if (errors.length) log.push(...errors.map((e) => `ERR: ${e}`));

  const scrubChanged = before !== after;
  const forecastOk = !forecastText.includes("No forecasts");
  const scenarioOk = scenarioText.includes("options");

  await browser.close();
  return (
    errors.length === 0 &&
    mapBox &&
    mapBox.width >= 700 &&
    markerCount >= 5 &&
    grid >= 1 &&
    forecastOk &&
    scrubChanged &&
    scenarioOk
  );
}

const ok1 = await runOnce("run1");
const ok2 = await runOnce("run2");
const body = `api=${API}\nui=${UI}\n` + log.join("\n") + `\nconsistent=${ok1 && ok2}\n`;
writeFileSync(`${SCRATCH}/phase6_browser.log`, body);
process.exit(ok1 && ok2 ? 0 : 1);