'use strict';
/* Fail-closed public pool metrics. No synthetic figures, private accounts or wallet keys.
   A server operator may enable an audited, same-origin HTTPS endpoint using the
   "forgecoin-pool-api" meta tag. Untrusted/stale/missing fields stay unavailable. */
(() => {
  const slots = Array.from(document.querySelectorAll('[data-poolmetric],[data-observermetric]'));
  if (!slots.length) return;
  const status = document.getElementById('pool-feed-status');
  const meta = document.querySelector('meta[name="forgecoin-pool-api"]');
  const unavailable = message => {
    for (const slot of slots) slot.textContent = 'Unavailable';
    if (status) status.textContent = message;
  };
  if (!meta || !meta.content || !meta.content.trim()) {
    unavailable('The verified native FRG pool statistics API is not deployed.');
    return;
  }
  let endpoint;
  try {
    endpoint = new URL(meta.content, window.location.href);
    if (endpoint.protocol !== 'https:' || endpoint.origin !== window.location.origin)
      throw new Error('Refusing insecure or cross-origin service');
  } catch {
    unavailable('Pool API URL rejected: secure same-origin HTTPS required.');
    return;
  }
  const refresh = async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 7000);
    try {
      const response = await fetch(endpoint, {
        method: 'GET', mode: 'same-origin', credentials: 'omit',
        cache: 'no-store', headers: { Accept: 'application/json' },
        signal: controller.signal
      });
      if (!response.ok) throw new Error('API HTTP error');
      const data = await response.json();
      const seconds = Math.floor(Date.now() / 1000);
      if (!data || data.schema !== 'frg-pool-stats-v1' ||
          data.network !== 'frg-mainnet-20261026' ||
          data.source !== 'verified-native-pool' || data.ready !== true ||
          !Number.isInteger(data.observedAt) || Math.abs(seconds-data.observedAt) > 120 ||
          !data.metrics || typeof data.metrics !== 'object' || Array.isArray(data.metrics))
        throw new Error('Wrong network or stale/unverified pool source');
      for (const slot of slots) {
        const key = slot.dataset.poolmetric || slot.dataset.observermetric;
        const raw = Object.hasOwn(data.metrics,key) ? data.metrics[key] : null;
        slot.textContent = typeof raw === 'string' && raw.length <= 90 && raw.trim()
          ? raw : 'Unavailable';
      }
      if (status) status.textContent =
        'Verified FRG pool feed observed at ' + new Date(data.observedAt * 1000).toLocaleString();
    } catch {
      unavailable('No fresh verified FRG pool readings are available; figures are not estimated.');
    } finally {
      clearTimeout(timeout);
    }
  };
  refresh();
  window.setInterval(refresh, 30000);
})();