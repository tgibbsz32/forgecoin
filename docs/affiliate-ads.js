(function () {
  'use strict';
  const container = document.getElementById('affiliate-offers');
  if (!container) return;
  fetch('affiliate-offers.json', {cache:'no-store'}).then(r => {if (!r.ok) throw Error('feed unavailable'); return r.json();}).then(data => {
    if (!data || !Array.isArray(data.offers)) return;
    const offers = data.offers.filter(o => o.enabled === true && typeof o.title === 'string' && typeof o.url === 'string' && /^https:\/\//i.test(o.url)).slice(0,2);
    if (!offers.length) return;
    const title = document.createElement('strong'); title.textContent = 'Partner offers'; container.appendChild(title);
    const notice = document.createElement('p'); notice.textContent = 'Advertisement — ForgeCoin may earn a commission if you purchase through these links.'; container.appendChild(notice);
    for (const o of offers) {
      const a = document.createElement('a'); a.href=o.url; a.textContent=o.title; a.target='_blank'; a.rel='sponsored noopener noreferrer'; a.className='affiliate-offer'; container.appendChild(a);
    }
    container.hidden = false;
  }).catch(() => {});
})();
