'use strict';
/* miniFORGE static GitHub Pages site.
   Locked checkout: this version can never construct a payment, ask to sign,
   receive deposits, or enable the disabled quantity field/button. */
(() => {
  const CHECKOUT_LOCKED = true;
  const ORIGINAL_STATUS = 'Not open';
  const $ = id => document.getElementById(id);
  const walletState = $('wallet-state');
  const walletButton = $('connect-wallet');
  const quoteButton = $('quote-button');
  const amountInput = $('token-amount');
  let activeProvider = null;

  // Security invariant: status content cannot override the disabled checkout.
  function lockCheckout() {
    amountInput.disabled = true;
    quoteButton.disabled = true;
    quoteButton.textContent = 'Checkout unavailable — sale not open';
    $('checkout-state').textContent = 'Not accepting payments';
    $('estimate-display').textContent = 'Unavailable';
    $('price-display').textContent = 'Not announced';
    $('token-price').textContent = 'Not announced';
    $('sale-status').textContent = ORIGINAL_STATUS;
    $('mint-address').textContent = 'Not issued';
  }

  lockCheckout();
  document.addEventListener('submit', event => {
    // This sale page does not have a live checkout form, even with JS injection.
    if (event.target.closest('.checkout-form')) event.preventDefault();
  });

  // Static availability data only, served from the same GitHub Pages origin.
  fetch('sale-status.json', {
    method: 'GET', mode: 'same-origin', credentials: 'omit',
    cache: 'no-store', headers: { Accept: 'application/json' }
  }).then(response => {
    if (!response.ok) throw new Error('No verified sale status');
    return response.json();
  }).then(status => {
    if (!status || status.schema !== 'miniforge-sale-status-v1' ||
        status.network !== 'solana-mainnet-beta' ||
        status.sale_enabled !== false ||
        status.payments_enabled !== false ||
        status.token_mainnet_mint !== null ||
        status.sale_price_usdc !== null ||
        status.supply_total_mfrg !== 50000000 ||
        status.sale_treasury_mfrg !== 5000000 ||
        status.future_liquidity_reserve_mfrg !== 5000000 ||
        status.future_distribution_reserve_mfrg !== 40000000) {
      // A bad or unexpectedly enabled status is a hard stop, not authorization.
      throw new Error('Unreviewed or contradictory sale metadata');
    }
  }).catch(() => {
    walletState.textContent =
      'Sale status could not be verified. All checkout actions remain disabled.';
  }).finally(lockCheckout);

  function shorten(value) {
    if (value.length < 15) return value;
    return value.slice(0, 6) + '…' + value.slice(-6);
  }
  async function connectReadOnly() {
    if (!CHECKOUT_LOCKED) return;
    if (activeProvider && activeProvider.publicKey) {
      walletState.textContent = 'Connected public address: ' +
        shorten(String(activeProvider.publicKey)) +
        '. No checkout, signing or payment is possible.';
      return;
    }
    const provider = window.phantom?.solana || window.solana || null;
    if (!provider || typeof provider.connect !== 'function') {
      walletState.textContent =
        'No supported injected Solana wallet was detected. The sale remains unavailable.';
      return;
    }
    walletButton.disabled = true;
    walletState.textContent = 'Requesting public address access only…';
    try {
      const data = await provider.connect();
      const address = String(data?.publicKey || provider.publicKey || '');
      if (!/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(address))
        throw new Error('The wallet did not return a valid-looking Solana address.');
      activeProvider = provider;
      walletState.textContent =
        'Public wallet preview: ' + shorten(address) +
        '. No purchase is available; no transaction was signed.';
    } catch {
      walletState.textContent =
        'Public address connection declined or unavailable. No funds moved.';
    } finally {
      walletButton.disabled = false;
    }
  }

  walletButton.addEventListener('click', connectReadOnly);
  // No wallet signer, Pay URL or transaction builder is present in this build.
})();
