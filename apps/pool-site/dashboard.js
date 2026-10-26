"use strict";

// This interface never fabricates live pool figures. A missing backend produces
// em dashes, not demo balances. Only normalized, aggregate /api/pool-stats data
// is displayed. Miner addresses, payouts, cookies and wallet secrets are absent.
(() => {
  const byId = (id) => document.getElementById(id);
  const values = [
    "stat-pool-rate", "stat-network-rate", "stat-miners", "stat-blocks",
    "stat-height", "stat-difficulty", "stat-round", "stat-last-block",
    "stat-last-template", "stat-pool-fee",
  ];
  const history = [];
  let lastObservedAt = 0;

  function comma(num) {
    return Math.trunc(num).toLocaleString("en-US", {maximumFractionDigits: 0});
  }
  function rate(num) {
    if (!Number.isFinite(num) || num < 0) return "—";
    const units = ["H/s", "KH/s", "MH/s", "GH/s", "TH/s"];
    let n = num, i = 0;
    while (n >= 1000 && i < units.length - 1) { n /= 1000; i++; }
    const decimals = n >= 100 ? 0 : n >= 10 ? 1 : 2;
    return n.toLocaleString("en-US", {maximumFractionDigits: decimals}) + " " + units[i];
  }
  function timeAgo(value) {
    if (!Number.isSafeInteger(value) || value <= 0) return "None recorded";
    const diff = Math.floor(Date.now() / 1000 - value);
    if (diff < 0) return "Future timestamp";
    if (diff < 60) return "Just now";
    if (diff < 3600) return Math.floor(diff / 60) + " min ago";
    if (diff < 86400) return Math.floor(diff / 3600) + " hr ago";
    return Math.floor(diff / 86400) + " days ago";
  }
  function setText(id, value) {
    const node = byId(id);
    if (node) node.textContent = String(value);
  }
  function clearMetrics(message) {
    values.forEach((id) => setText(id, "—"));
    setText("observation-note", message);
    setText("last-checked", "No verified pool data received");
    history.length = 0;
    drawHistory();
  }
  function setState(connected, message) {
    const root = byId("feed-label");
    const feed = root?.parentElement;
    if (feed) feed.classList.toggle("connected", Boolean(connected));
    setText("feed-label", message);
  }
  function drawHistory() {
    const line = byId("chart-line");
    const area = byId("chart-area");
    const empty = byId("chart-empty");
    if (!line || !area || !empty) return;
    if (history.length < 2) {
      line.setAttribute("d", "");
      area.setAttribute("d", "");
      empty.hidden = false;
      byId("hashrate-chart")?.setAttribute("aria-label", "No observed hashrate history available yet");
      return;
    }
    empty.hidden = true;
    const min = Math.min(0, ...history), max = Math.max(1, ...history);
    const span = max - min || 1;
    const points = history.map((value, index) => {
      const x = index * 720 / (history.length - 1);
      const y = 197 - ((value - min) / span) * 155;
      return [x, y];
    });
    const d = points.map(([x, y], i) =>
      (i === 0 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1)
    ).join(" ");
    line.setAttribute("d", d);
    area.setAttribute("d", d + " L720 220 L0 220 Z");
    byId("hashrate-chart")?.setAttribute("aria-label",
      "Recent observed pool hashrate from " + rate(history[0]) +
      " to " + rate(history[history.length - 1]));
  }
  function valid(s) {
    if (!s || typeof s !== "object" || Array.isArray(s)) return false;
    const keys = [
      "poolHashrate", "networkHashrate", "networkDifficulty", "networkHeight",
      "connectedMiners", "poolBlocksFound", "roundHashes",
      "lastBlockFound", "lastTemplateFetched",
    ];
    if (!keys.every((key) => Number.isSafeInteger(s[key]) && s[key] >= 0)) return false;
    return typeof s.poolFeePercent === "number" && Number.isFinite(s.poolFeePercent)
      && s.poolFeePercent >= 0 && s.poolFeePercent <= 100;
  }
  function render(s, asOf) {
    setText("stat-pool-rate", rate(s.poolHashrate));
    setText("stat-network-rate", rate(s.networkHashrate));
    setText("stat-miners", comma(s.connectedMiners));
    setText("stat-blocks", comma(s.poolBlocksFound));
    setText("stat-height", comma(s.networkHeight));
    setText("stat-difficulty", comma(s.networkDifficulty));
    setText("stat-round", comma(s.roundHashes) + " hashes");
    setText("stat-last-block", timeAgo(s.lastBlockFound));
    setText("stat-last-template", timeAgo(s.lastTemplateFetched));
    setText("stat-pool-fee", s.poolFeePercent.toFixed(2) + "% (reported)");
    history.push(s.poolHashrate);
    if (history.length > 24) history.shift();
    drawHistory();
    setText("observation-note",
      "Source: jtgrassie-compatible read-only aggregate /stats. Backend observations are not independent proof of canonical FRG launch.");
    setText("last-checked", "Backend observation: " + (asOf || "time unavailable"));
    setState(true, "BACKEND OBSERVED · UNVERIFIED");
  }
  async function poll() {
    try {
      const resp = await fetch("api/pool-stats", {
        method: "GET", cache: "no-store", headers: {"Accept": "application/json"}
      });
      const body = await resp.json();
      if (!resp.ok || body.state !== "backend_observed_unverified"
          || body.launchApproved !== false || !valid(body.stats)) {
        throw new Error("No valid backend observations");
      }
      render(body.stats, body.asOf);
      lastObservedAt = Date.now();
    } catch (_) {
      clearMetrics("The verified-format statistics source is not connected or did not return valid data. Mining and payouts remain disabled.");
      setState(false, "STATISTICS DISCONNECTED");
    }
  }
  function clock() {
    setText("utc-clock", new Date().toLocaleTimeString("en-GB", {
      timeZone: "UTC", hour: "2-digit", minute: "2-digit", hour12: false
    }) + " UTC");
    // The last successful observation should never keep 'live' colors during
    // prolonged browser/network suspension.
    if (lastObservedAt && Date.now() - lastObservedAt > 60000) {
      lastObservedAt = 0;
      clearMetrics("Backend observation expired; no current figures are being displayed.");
      setState(false, "STATISTICS STALE");
    }
  }
  clock();
  poll();
  setInterval(clock, 10000);
  setInterval(poll, 20000);
})();
