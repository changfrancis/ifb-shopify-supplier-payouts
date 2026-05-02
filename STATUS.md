# Status — all 7 suppliers verified for Apr 2026

## Production state

Single canonical workflow (v5) handles all 7 suppliers via Suppliers Registry (one row per supplier). v4 retired.

**Cron:** `0 2 1 * *` SGT (1st of every month at 02:00). Next firing: **June 1, 2026**.

| Supplier | Active | Apr 2026 Result | Notable |
|---|---|---|---|
| Stan | TRUE | 2 rows | hint=`stinger`; clean SKU matches |
| Piggy | TRUE | 18 rows | manual fedex deductions captured (purple); Cash IFB cancelled order flagged teal |
| Bluebird | TRUE | 4 rows | hint=`gel,gels,bluebird,blue bird,bbgb`; 1 TITLE MATCH for verify |
| Ryan | TRUE | 56 rows | hint=`blu,accublu,dtb`; 24 SKU excludes; bundle SKUs added; 4685+4980 manually flagged coral |
| Bryan | TRUE | 6 rows | hint=`stk`; sling + stk-worker SKUs; PII filter on properties |
| Dylan | TRUE | 17 rows | date format `d/LL/yyyy`; 2 REFUND flags |
| Gavin | TRUE | 85 rows | merged from v4 to v5 (April 2026); excludes incl. d2-victory-shroud-digital |

## Workflows in n8n

```
n8n list:workflow --active=true
  ShopifyErrHandle1   Shopify Sync — Error Handler           ACTIVE
  v5ChildPerSup1      Shopify Per-Supplier Sync v1 (child)   ACTIVE
  v5ParentMulti1      Shopify Multi-Supplier Sync v1 (parent) ACTIVE  ← cron 0 2 1 * *
  Pn8M3kQrZb2WyT5j    Shopify Monthly SKU Sync v4            DEACTIVATED (retired)
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
- Title hints checked across `title`, `variant_title`, `name`, `vendor`, `properties` (PII-filtered), `o.note`, `o.tags`
- exclude_skus checks the same fallback used for SKU column (li.sku || li.title || li.name)
- UNDERPRICED check gated on currency=SGD
- CANCELLED order detection via `o.cancelled_at`
- REFUND detection via `o.refunds[]` non-empty
- Manual entries from supplier monthly tabs: type A (fedex deduction-style with empty OrderNo+Date) and type B (Manual XXXX prefix); composite dedup key
- "To pay" / "Paid" footer rows skipped
- NO SALE THIS MONTH placeholder when 0 rows match

## Resume here

Next session: production validation when **June 1, 2026 02:00 SGT** cron fires. Verify Run Log entries for all 7 suppliers and inspect each `May 2026 <Supplier> n8n` tab.

Carryover items:
- Rotate `changfrancis` DSM password (was leaked in chat earlier)
- Vitae onboarding deferred until Linford adds an Amount Reference tab
- v4 JSON kept in repo as historical artifact; can be archived to `archive/` later

## Anchors

- Plan file (not in repo): `~/.claude/plans/n8n-shopify-linear-koala.md`
- Suppliers Registry: https://docs.google.com/spreadsheets/d/1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs/edit
- Internal sheet (output): https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit
- Service account: `n8n-sheets@ifb-n8n-integration.iam.gserviceaccount.com`
