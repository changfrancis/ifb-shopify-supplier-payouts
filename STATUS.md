# Status — production-ready, all 7 suppliers verified

## Production state

Single canonical workflow (v5) handles all 7 suppliers via Suppliers Registry (one row per supplier). v4 retired.

**Cron:** `0 2 1 * *` SGT (1st of every month at 02:00). Next firing: **June 1, 2026**.

| Supplier | Active | Latest verified | Title hints | Excludes |
|---|---|---|---|---|
| Stan | TRUE | Mar+Apr 2026 | `stinger` | (none) |
| Piggy | TRUE | Apr 2026 | `piggy,piggyfoam,pgf,piggy foam` | `kunlun-1.8-experimental-spring` |
| Bluebird | TRUE | Mar+Apr 2026 | `gel,gels,bluebird,blue bird,bbgb` | (none) |
| Ryan | TRUE | Apr 2026 | `blu,accublu,dtb` | 24 SKUs (bbgb_*, free-zwq-*, d2-*, etc.) |
| Bryan | TRUE | Mar+Apr 2026 | `stk` | (none) |
| Dylan | TRUE | Apr 2026 | `d2,dylan` | (none) |
| Gavin | TRUE | Apr 2026 | `gfz,gavin,sbl,sbf` | 10 SKUs incl. `d2-victory-shroud-digital` |

Vitae deferred — no Amount Reference tab in source sheet yet.

## Workflows in n8n

```
n8n list:workflow --active=true
  ShopifyErrHandle1     Shopify Sync — Error Handler           ACTIVE
  v5ChildPerSup1        Shopify Per-Supplier Sync v1 (child)   ACTIVE
  v5ParentMulti1        Shopify Multi-Supplier Sync v1 (parent) ACTIVE  ← cron 0 2 1 * *
  Pn8M3kQrZb2WyT5j      Shopify Monthly SKU Sync v4            DEACTIVATED (retired)
```

## Conditional formatting (auto-applied per run)

| Color | Trigger | Meaning |
|---|---|---|
| 🟪 Purple | Remarks contains `MANUAL ENTRY` | human-input rows (e.g., fedex deductions) |
| 🟦 Teal | Remarks contains `CANCELLED` | cancelled Shopify order — verify before paying |
| 🟥 Red | Remarks contains `REFUND` or `CURRENCY` | error — likely should NOT pay supplier |
| 🟨 Yellow | Remarks contains `TITLE MATCH` or `UNDERPRICED` | warning — review SKU match or price |
| 🟧 Orange | OrderNo non-numeric (Walkin / Cash IFB / blank) | non-Shopify entry |
| 🟫 Grey + bold | Header row | always |
| 🟧 Coral (manual) | one-off manual flag | direct cell color, not auto |

## Match logic features (v5 child)

- SKU matching with `_↔-` interchangeable + `COLOUR`/`XXX` wildcards
- Title hints checked across `title`, `variant_title`, `name`, `vendor`, `properties` (PII-filtered: skip emails / phone / address fields), `o.note`, `o.tags`
- `exclude_skus` checks the same fallback used for SKU column (li.sku || li.title || li.name)
- UNDERPRICED check gated on currency=SGD
- CANCELLED order detection via `o.cancelled_at`
- REFUND detection via `o.refunds[]` non-empty
- Manual entries from supplier monthly tabs:
  - Type A — empty OrderNo + empty Date + has SKU + Takehome (e.g., fedex shipping deductions)
  - Type B — OrderNo prefix `Manual XXXX` (backdated entries)
  - Both surface as `MANUAL ENTRY` in Remarks → 🟪 Purple
- Composite dedup key (orderNo|sku|takehome) for manual rows
- "To pay" / "Paid" footer rows skipped
- NO SALE THIS MONTH placeholder when 0 rows match

## Resume here

Production validation when **June 1, 2026 02:00 SGT** cron fires. Check Run Log entries for all 7 suppliers and inspect each `May 2026 <Supplier> n8n` tab.

## Open carryover items

- **Vitae onboarding** — needs an Amount Reference tab in `1KWz6wl5m4gDkBUOehvlmOWBv4IYj9X5fwS1Te8yRxD8`. Currently inactive in Registry.
- **Add `read_all_orders` scope** to Shopify app (Dev Dashboard → new version → uninstall/reinstall). Without this, Shopify API only returns last ~60 days of orders. Affects historical backfills (e.g. Jan 2026 returned 0).
- **Rotate `changfrancis` DSM password** (was leaked early in chat).

## Anchors

- Plan file (not in repo): `~/.claude/plans/n8n-shopify-linear-koala.md`
- Suppliers Registry: https://docs.google.com/spreadsheets/d/1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs/edit
- Internal sheet (output): https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit
- Service account: `n8n-sheets@ifb-n8n-integration.iam.gserviceaccount.com`
