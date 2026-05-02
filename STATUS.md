# Status — production-ready, cron set for June 1

## Production state

Single canonical workflow (v5) handles all 8 suppliers via Suppliers Registry. v4 retired.

**Cron:** `0 2 1 * *` Asia/Taipei (= SGT, GMT+8). **Next firing: June 1, 2026 02:00 SGT.**

| Supplier | Active | Latest verified | Status | Title hints | Excludes |
|---|---|---|---|---|---|
| Stan | TRUE | Mar+Apr 2026 | ✅ | `stinger` | (none) |
| Piggy | TRUE | Apr 2026 | ✅ | `piggy,piggyfoam,pgf,piggy foam` | `kunlun-1.8-experimental-spring` |
| Bluebird | TRUE | Mar+Apr 2026 | ✅ | `gel,gels,bluebird,blue bird,bbgb` | (none) |
| Ryan | TRUE | Apr 2026 | ✅ | `blu,accublu,dtb` | 24 SKUs |
| Bryan | TRUE | Mar+Apr 2026 | ✅ | `stk` | (none) |
| Dylan | TRUE | Apr 2026 | ✅ | `d2,dylan` | (none) |
| Gavin | TRUE | Apr 2026 | ✅ | `gfz,gavin,sbl,sbf` | 10 SKUs incl. `d2-victory-shroud-digital` |
| **Vitae** | TRUE | Mar+Apr 2026 | ⚠️ **INCOMPLETE** | `linny,linford,vitae,vitae precision,effort` | 5 SKUs (false-positive items) |

### Vitae incomplete — what's pending

- **Amount Reference price columns are blank.** SKUs are listed (51 entries: `vitae-*-knob`, `vitae-aeb-grip-*`, `mlok-*`, etc.) but Listing Price / 3DPS+Stripe Fee / Linford Amount columns are empty.
- **Workaround in workflow**: when ref listing is blank, Match Code falls back to Shopify sale price for the Listing column (and Takehome = Listing as a draft). Every such row is yellow-flagged `TITLE MATCH - ref price pending`.
- **Action for Linford onboarding**: fill in Listing / Fee / Takehome in `Vitae Amount Reference ` (the trailing-space tab in `1KWz6wl5m4gDkBUOehvlmOWBv4IYj9X5fwS1Te8yRxD8`). Once filled, future runs will produce clean SKU matches with proper takehome splits.

## Workflows in n8n

```
n8n list:workflow --active=true
  ShopifyErrHandle1     Shopify Sync — Error Handler           ACTIVE
  v5ChildPerSup1        Shopify Per-Supplier Sync v1 (child)   ACTIVE
  v5ParentMulti1        Shopify Multi-Supplier Sync v1 (parent) ACTIVE  ← cron 0 2 1 * * SGT
  Pn8M3kQrZb2WyT5j      Shopify Monthly SKU Sync v4            DEACTIVATED (retired post-convergence)
```

Container TZ: `Asia/Taipei` (verified inside container).

## Conditional formatting (auto-applied per run)

| Color | Trigger | Meaning |
|---|---|---|
| 🟪 Purple | Remarks contains `MANUAL ENTRY` | human-input rows (e.g., fedex deductions) |
| 🟦 Teal | Remarks contains `CANCELLED` | cancelled Shopify order — verify before paying |
| 🟥 Red | Remarks contains `REFUND` or `CURRENCY` | error — likely should NOT pay supplier |
| 🟨 Yellow | Remarks contains `TITLE MATCH` or `UNDERPRICED` | warning — review SKU match, price, or pending ref |
| 🟧 Orange | OrderNo non-numeric (Walkin / Cash IFB / blank) | non-Shopify entry |
| 🟫 Grey + bold | Header row | always |
| 🟧 Coral (manual) | one-off cell-level color | not auto — human flags specific rows |

## Match logic features (v5 child)

- SKU matching with `_↔-` interchangeable + `COLOUR`/`XXX` wildcards
- Title hints checked across `title`, `variant_title`, `name`, `vendor`, `properties` (PII-filtered: skip emails/phone/address fields), `o.note`, `o.tags`
- `exclude_skus` checks the same fallback used for SKU column (li.sku || li.title || li.name)
- UNDERPRICED check gated on currency=SGD
- **NEW**: when ref listing is empty (e.g. supplier still onboarding), use Shopify sale price as Listing + flag yellow `TITLE MATCH - ref price pending`
- CANCELLED order detection via `o.cancelled_at`
- REFUND detection via `o.refunds[]` non-empty
- Manual entries from supplier monthly tabs:
  - Type A — empty OrderNo + empty Date + has SKU + Takehome (e.g., fedex shipping deductions)
  - Type B — OrderNo prefix `Manual XXXX` (backdated entries)
- Composite dedup key (orderNo|sku|takehome) for manual rows
- "To pay" / "Paid" footer rows skipped
- NO SALE THIS MONTH placeholder when 0 rows match

## Resume here

Production validation when **June 1, 2026 02:00 SGT** cron fires. Verify:
- 8 child sub-workflow executions (one per active supplier)
- 8 monthly tabs `May 2026 <Supplier> n8n` created in internal sheet
- 8 Run Log entries appended
- No 429 rate-limit errors

## Open carryover items

- **Vitae**: fill in `Vitae Amount Reference ` listing/fee/takehome columns
- **Add `read_all_orders` scope** to Shopify app (Dev Dashboard → new version → uninstall/reinstall). Without this, Shopify API only returns last ~60 days. Affects historical backfills (Jan/Feb 2026 returned 0).
- **Rotate `changfrancis` DSM password** (was leaked early in chat).

## Anchors

- Suppliers Registry: https://docs.google.com/spreadsheets/d/1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs/edit
- Internal sheet (n8n output): https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit
- Service account: `n8n-sheets@ifb-n8n-integration.iam.gserviceaccount.com`
- Plan file (not in repo): `~/.claude/plans/n8n-shopify-linear-koala.md`
