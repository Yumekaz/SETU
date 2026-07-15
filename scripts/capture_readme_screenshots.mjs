/** Capture public README screenshots from the running Docker application. */
import { mkdir } from "fs/promises";
import { dirname, resolve } from "path";
import { fileURLToPath, pathToFileURL } from "url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const playwrightEntry = pathToFileURL(
  resolve(root, "frontend/node_modules/playwright/index.mjs"),
).href;
const { chromium } = await import(playwrightEntry);

const ui = process.env.SETU_UI_URL ?? "http://127.0.0.1:5173";
const output = resolve(root, "docs/assets");
await mkdir(output, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
page.setDefaultTimeout(60_000);

try {
  await page.goto(ui, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#corridor-score-grid");
  await page.screenshot({ path: resolve(output, "setu-overview.png") });

  await page.getByRole("button", { name: "03 Scenario replay" }).click();
  await page.waitForSelector("#replay-scrub");
  await page.waitForFunction(
    () => document.body.textContent?.includes("20 Days"),
    { timeout: 60_000 },
  );
  await page.locator("#replay-headline").scrollIntoViewIfNeeded();
  await page.screenshot({ path: resolve(output, "setu-replay.png") });

  await page.getByRole("button", { name: "01 Overview" }).click();
  await page.waitForSelector("#scenario-corridor-select");
  await page.locator("#scenario-corridor-select").selectOption("MALACCA");
  await page.getByRole("button", { name: "Run scenario" }).click();
  await page.waitForFunction(
    () => document.querySelector("#scenario-controls")?.textContent?.includes("Scenario executed successfully:"),
    { timeout: 120_000 },
  );
  const scenario = page.locator("#scenario-controls");
  await scenario.screenshot({ path: resolve(output, "setu-simulation.png") });
} finally {
  await browser.close();
}
