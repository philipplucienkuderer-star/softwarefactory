// Evidence run for "Zutaten auf die Liste": drives the app at phone size, records a video,
// saves numbered screenshots and writes assertions.md.
// Usage: COMMIT=<sha> node record.mjs <base-url> <out-dir>
import { writeFileSync } from "node:fs";
import { chromium, devices } from "playwright";

const [base, out] = process.argv.slice(2);
const results = [];
let shots = 0;

function expectEqual(actual, expected) {
  if (actual !== expected) throw new Error(`expected "${expected}", got "${actual}"`);
}

async function check(page, slug, message, assertion) {
  let result = "passed";
  try {
    await assertion();
  } catch (error) {
    result = "failed";
    console.log(`FAILED ${message}: ${error.message}`);
  }
  shots += 1;
  const file = `${String(shots).padStart(2, "0")}-${slug}-${result}.png`;
  await page.screenshot({ path: `${out}/${file}` });
  results.push({ type: "assertion", result, message, file });
}

const ingredientQty = (page, name) => page.locator(".ingredients li", { hasText: name }).locator(".qty").innerText();
const itemQty = (page, name) => page.locator(".item", { hasText: name }).locator(".qty").innerText();
const itemSources = (page, name) => page.locator(".item", { hasText: name }).locator("small").innerText();

const browser = await chromium.launch();
let videoPath;
try {
  const device = devices["Pixel 7"];
  const context = await browser.newContext({ ...device, recordVideo: { dir: out, size: device.viewport } });
  try {
    const page = await context.newPage();
    const pause = () => page.waitForTimeout(900);
    page.on("pageerror", (error) => console.log("PAGE ERROR", error.message));

    results.push({ type: "setup", message: `Fresh data file with the three sample dishes at ${base}` });
    await page.goto(`${base}/#/liste`);
    await check(page, "precondition-list-empty", "Precondition: the shopping list is empty", () =>
      page.getByText("Die Liste ist leer").waitFor({ timeout: 5000 }),
    );
    await pause();

    results.push({ type: "test_start", message: "It should rescale a dish when the servings change" });
    await page.getByRole("link", { name: "Gerichte" }).click();
    await pause();
    await page.getByText("Gemüsecurry").click();
    await page.locator(".servings strong", { hasText: /^4$/ }).waitFor();
    await pause();
    for (let n = 0; n < 2; n += 1) {
      await page.getByRole("button", { name: "Eine Portion weniger" }).click();
      await pause();
    }
    await check(page, "curry-for-2-servings", "Curry for 2: 1 Stk Süßkartoffel, 200 ml Kokosmilch", async () => {
      await page.locator(".servings strong", { hasText: /^2$/ }).waitFor({ timeout: 5000 });
      expectEqual(await ingredientQty(page, "Süßkartoffel"), "1 Stk");
      expectEqual(await ingredientQty(page, "Kokosmilch"), "200 ml");
    });

    results.push({ type: "test_start", message: "It should put the scaled ingredients on the list" });
    await page.getByRole("button", { name: "Zutaten auf die Liste" }).click();
    await check(page, "curry-on-the-list", "7 curry items listed, Zwiebel 0,5 Stk für Gemüsecurry", async () => {
      await page.getByText("7 Zutaten für Gemüsecurry auf der Liste").waitFor({ timeout: 5000 });
      await page.getByText("7 von 7 noch offen").waitFor({ timeout: 5000 });
      expectEqual(await itemQty(page, "Zwiebel"), "0,5 Stk");
      expectEqual(await itemSources(page, "Zwiebel"), "für Gemüsecurry");
    });
    await pause();

    results.push({ type: "test_start", message: "It should merge an ingredient that two dishes need" });
    await page.getByRole("link", { name: "Gerichte" }).click();
    await pause();
    await page.getByText("Spaghetti Bolognese").click();
    await page.locator(".servings strong", { hasText: /^4$/ }).waitFor();
    await pause();
    await page.getByRole("button", { name: "Zutaten auf die Liste" }).click();
    await check(page, "onion-merged", "One Zwiebel row: 1,5 Stk, for both dishes; 13 items", async () => {
      await page.getByText("13 von 13 noch offen").waitFor({ timeout: 5000 });
      expectEqual(await page.locator(".item", { hasText: "Zwiebel" }).count(), 1);
      expectEqual(await itemQty(page, "Zwiebel"), "1,5 Stk");
      expectEqual(await itemSources(page, "Zwiebel"), "für Gemüsecurry, Spaghetti Bolognese");
    });
    await pause();

    results.push({ type: "test_start", message: "It should tick items off and clear them" });
    await page.locator(".item", { hasText: "Zwiebel" }).locator("input").click();
    await page.getByText("12 von 13 noch offen").waitFor();
    await pause();
    await page.locator(".item", { hasText: "Koriander" }).locator("input").click();
    await page.getByText("11 von 13 noch offen").waitFor();
    await pause();
    await page.getByRole("button", { name: "Erledigte entfernen" }).click();
    await check(page, "ticked-items-cleared", "After clearing: 11 open items, no Zwiebel row", async () => {
      await page.getByText("11 von 11 noch offen").waitFor({ timeout: 5000 });
      expectEqual(await page.locator(".item", { hasText: "Zwiebel" }).count(), 0);
    });
    await pause();
    videoPath = await page.video().path();
  } finally {
    await context.close(); // Finalizes the video even if a step throws.
  }
} finally {
  await browser.close();
}

const lines = ["# Assertions", "", `Target: ${base} at commit ${process.env.COMMIT ?? "unknown"}, Chromium as Pixel 7`, ""];
for (const entry of results) {
  if (entry.type === "setup") lines.push(`setup: ${entry.message}`, "");
  if (entry.type === "test_start") lines.push(`## ${entry.message}`, "");
  if (entry.type === "assertion") lines.push(`- ${entry.result}: ${entry.message} (\`${entry.file}\`)`, "");
}
writeFileSync(`${out}/assertions.md`, lines.join("\n"));
console.log(lines.join("\n"));
console.log(`VIDEO ${videoPath}`);
if (results.some((entry) => entry.result === "failed")) process.exitCode = 1;
