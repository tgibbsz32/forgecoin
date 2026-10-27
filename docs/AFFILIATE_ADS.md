# ForgeCoin affiliate placements

A small, hidden-by-default partner area is available on the home page and from the Android app's Partner Offers panel. Add active entries to `docs/affiliate-offers.json`:

```json
{"version":1,"offers":[{"title":"Approved partner offer","url":"https://example.com/your-approved-affiliate-link","enabled":true}]}
```

Replace the example URL with an actual approved partner link. Only the first two enabled HTTPS offers are rendered. Never put tracking credentials or customer data in this public JSON file. The ad area stays hidden if the feed is empty or unavailable. The Android link opens the same centrally managed offers; it requires no APK rebuild for updates. Offers are outbound links, not ads embedded in wallet, mining, transaction, or seed-entry flows. Disclosures must remain visible near links. Verify individual affiliate program restrictions, especially mobile-app eligibility, before adding offers. No external tracking SDK, auto-play, or intrusive overlay is installed. This does not constitute affiliate-program approval or guarantee income.
