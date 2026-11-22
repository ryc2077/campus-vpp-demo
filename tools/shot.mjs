// Headless-Chrome screenshot driver via CDP (no deps; Node 22+ built-in WebSocket).
// Usage:
//   node shot.mjs <url> <out.png> [width] [height] [waitMs] [settleMs]
// Waits `waitMs` real ms for the Godot wasm to boot, then `settleMs` more,
// captures a PNG, and prints console messages (errors flagged).
// Exit 0 = shot taken (console errors are reported, not fatal, so the caller
// can decide); exit 2 = Chrome/CDP failure.
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";

const CHROME = process.env.CHROME || "/home/hatch/workspace/chrome-linux64/chrome";
const [url, out, w = "1280", h = "720", waitMs = "20000", settleMs = "4000"] =
  process.argv.slice(2);
if (!url || !out) {
  console.error("usage: node shot.mjs <url> <out.png> [w] [h] [waitMs] [settleMs]");
  process.exit(2);
}
const PORT = 9333 + Math.floor(Math.random() * 500);
const PROFILE = `/tmp/chrome-shot-profile-${process.pid}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--enable-unsafe-swiftshader", "--use-angle=swiftshader",
  `--remote-debugging-port=${PORT}`,
  `--window-size=${w},${h}`,
  `--user-data-dir=${PROFILE}`,
  "about:blank",
], { stdio: "ignore" });
console.log("[chrome]", CHROME);
chrome.on("error", (e) => {
  console.error("[shot-fail] chrome spawn failed: " + e.message + " (" + CHROME + ")");
  process.exit(2);
});

const errors = [];
const logs = [];
let ws;
try {
  // wait for DevTools endpoint (高负载机器上 Chrome 启动慢：120×500ms=60s，
  // 之前 40×250ms=10s 在负载 20+ 时不够，报 "DevTools endpoint never came up")
  let targets;
  for (let i = 0; i < 120; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      targets = await res.json();
      break;
    } catch { await sleep(500); }
  }
  if (!targets) throw new Error("DevTools endpoint never came up");
  const page = targets.find((t) => t.type === "page");
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0;
  const pending = new Map();
  const send = (method, params = {}) => new Promise((res) => {
    const mid = ++id;
    pending.set(mid, res);
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result || {}); pending.delete(m.id); }
    if (m.method === "Runtime.consoleAPICalled") {
      const text = (m.params.args || []).map((a) => a.value ?? a.description ?? "").join(" ");
      const line = `[${m.params.type}] ${text}`;
      logs.push(line);
      if (m.params.type === "error") errors.push(line);
    }
    if (m.method === "Runtime.exceptionThrown") {
      errors.push("[exception] " + JSON.stringify(m.params.exceptionDetails).slice(0, 500));
    }
    if (m.method === "Log.entryAdded") {
      const e = m.params.entry;
      if (e.level === "error") errors.push("[log-error] " + (e.text || "") + " " + (e.url || ""));
    }
  };
  await send("Runtime.enable");
  await send("Log.enable");
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width: Number(w), height: Number(h), deviceScaleFactor: 1, mobile: Number(w) < 500,
  });
  await send("Page.navigate", { url });
  await sleep(Number(waitMs));
  // check the Godot canvas actually painted (non-blank heuristic via title)
  const evalRes = await send("Runtime.evaluate", {
    expression: `({title: document.title, canvas: !!document.querySelector('#canvas'), bodyText: document.body.innerText.slice(0,120)})`,
    returnByValue: true,
  });
  console.log("[page]", JSON.stringify(evalRes.result?.value));
  await sleep(Number(settleMs));
  const shot = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(out, Buffer.from(shot.data, "base64"));
  console.log("[shot]", out);
} catch (e) {
  console.error("[shot-fail]", e.message);
  process.exit(2);
} finally {
  try { ws?.close(); } catch {}
  chrome.kill("SIGKILL");
  // 每次新建的 Chrome profile 约 45–60MB；/tmp 只有 512MB tmpfs，不清会塞满导致后续截图挂起。
  try { await import("node:fs/promises").then((fs) => fs.rm(PROFILE, { recursive: true, force: true })); } catch {}
}
console.log(`[console] ${logs.length} messages, ${errors.length} errors`);
if (process.env.SHOW_LOGS) for (const l of logs.slice(0, 40)) console.log("  LOG:", l);
for (const e of errors.slice(0, 20)) console.log("  ERR:", e);
process.exit(0);
