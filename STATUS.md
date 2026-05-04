# Status — production-ready, cron set for June 1

## Production state

Single canonical workflow (v5) handles all 8 suppliers via Suppliers Registry. v4 retired.

**Cron:** `0 2 1 * *` Asia/Taipei (= SGT, GMT+8). **Next firing: June 1, 2026 02:00 SGT.**

| Supplier | Active | Latest verified | Status | Title hints | Excludes |
|---|---|---|---|---|---|
| Stan | TRUE | Mar+Apr 2026 | ✅ | `stinger` | (none) |
| Piggy | TRUE | Apr 2026 | ✅ | `piggy,piggyfoam,pgf,piggy foam` | `kunlun-1.8-experimental-spring` |
| Bluebird | TRUE | Mar+Apr 2026 | ✅ | `gel,gels,bluebird,blue bird,bbgb` | (none) |
| Ryan | TRUE | Apr 2026 | ✅ | `blu,accublu,dtb,holster,molle` | 25 SKUs |
| Bryan | TRUE | Mar+Apr 2026 | ✅ | `stk` | (none) |
| Dylan | TRUE | Apr 2026 | ✅ | `d2,dylan` | (none) |
| Gavin | TRUE | Apr 2026 | ✅ | `gfz,gavin,sbl,sbf` | 10 SKUs incl. `d2-victory-shroud-digital` |
| Vitae | TRUE | Mar+Apr 2026 | ✅ | `linny,linford,vitae,vitae precision,effort` | 5 SKUs (false-positive items) |

### Vitae onboarding completed (2026-05-04)

- Linford filled in all 51 SKUs' Listing / Fee / Takehome columns in `Vitae Amount Reference ` (trailing-space tab in `1KWz6wl5m4gDkBUOehvlmOWBv4IYj9X5fwS1Te8yRxD8`).
- Mar 2026 Vitae n8n re-run (delete + rebuild): **14 clean SKU matches** with proper takehome splits + 1 title match (custom barrel job). Was 13 yellow-flagged `ref price pending` rows before.
- Apr 2026 Vitae n8n re-run: 1 row (custom barrel machining for Order 4712). All 331 April orders scanned — only one Vitae-related line item exists for April, and it's a custom title-match. Reference SKUs didn't sell in April.

## Workflows in n8n

```
n8n list:workflow
  ShopifyErrHandle1     Shopify Sync — Error Handler           ACTIVE
  v5ChildPerSup1        Shopify Per-Supplier Sync v1 (child)   ACTIVE
  v5ParentMulti1        Shopify Multi-Supplier Sync v1 (parent) ACTIVE  ← cron 0 2 1 * * SGT
  v6Tshirt1             Shopify Tshirt Pre-orders v1           INACTIVE  ← manual trigger, on-demand
```

v1 (`KT4gqTWzWIoYtQpC`) and v4 (`Pn8M3kQrZb2WyT5j`) deleted from DB on 2026-05-02 (post-convergence cleanup).

## T-shirt pre-order workflow (v6)

Standalone workflow for the custom-printed pre-order t-shirt product (SKU `nerfsg-tshirt-custom-*`). Pulls the last 60 days of Shopify orders, extracts size + nickname, writes the overwriting tab `Tshirt Pre-orders` in the internal sheet for handover to the t-shirt printer.

- **Trigger:** **on-demand only** — no cron, no schedule. Run manually each time the user wants a fresh hand-off list for the t-shirt printer. Window is always trailing 60 days from run time, so each run produces the current snapshot; no historical state to preserve between runs.
- **Run procedure:** stop n8n container, `docker run --rm` the CLI image with the same env as production, `n8n execute --id=v6Tshirt1`, restart n8n. (Same procedure as the single-supplier re-run flow above.)
- **Output:** 10 columns — Order No., Order Date, Customer Name, Email, SKU, Size, Quantity, Nickname, Status, Remarks
- **Quantity expansion:** `qty > 1` → one row per shirt with `Unit n/N` in Remarks
- **Conditional formatting (per-run, idempotent):**
  - 🟥 Red: Remarks contains `CANCELLED` or `REFUND` (likely don't print)
  - 🟨 Yellow: Remarks contains `NON-ASCII` or `EMPTY NICKNAME` (verify printer / customer)
- **Last verified run:** 2026-05-03 — 31 orders pulled, 2 with emoji nicknames flagged NON-ASCII, 2 with EMPTY NICKNAME flagged. Tab leftmost in [internal sheet](https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit#gid=1367981525).

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
- NO SALE THIS MONTH placeholder when 0 rows match (⚠ also fires on idempotent re-runs that produce 0 net-new rows even when tab already has data — see Open items)

## Resume here

Production validation when **June 1, 2026 02:00 SGT** cron fires. Verify:
- 8 child sub-workflow executions (one per active supplier)
- 8 monthly tabs `May 2026 <Supplier> n8n` created in internal sheet
- 8 Run Log entries appended
- No 429 rate-limit errors

## Open carryover items

- **Workflow bug (low pri):** `NO SALE THIS MONTH` placeholder is appended on idempotent re-runs that produce 0 net-new rows, even when the destination tab already has real data. Fix: gate the placeholder on `existingDataRows == 0`, not `matchedThisRun == 0`. Workaround: delete the trailing placeholder row manually after re-runs.
- **Workflow limitation:** v5 child only **appends** to dest tabs — it never deletes or updates existing rows. To pick up new excludes / updated reference prices for a past month, **delete the dest tab first**, then re-run with the month override (the workflow recreates the tab from scratch). Demonstrated 2026-05-04: Apr 2026 Ryan rebuilt cleanly after `HC-diana-magnetic-holster` was added to Ryan's exclude list; Mar+Apr 2026 Vitae rebuilt cleanly after Linford filled in reference prices.

## Manual re-run procedure (single supplier, specific month)

n8n CLI `execute` cannot share port 5679 with the running container, so:

1. **Deactivate non-target rows** in Registry (set `active=FALSE`); keep only the target supplier `TRUE`.
2. **Stop n8n container** (`docker stop n8n`) — releases port 5679 + DB lock.
3. **Run a one-shot CLI container** with the same volumes/env as the production container, plus `OVERRIDE_MONTH_*` env vars:
   ```
   docker run --rm --user 1000:1000 \
     -v /volume1/docker/n8n/n8n_data:/home/node/.n8n \
     -v /volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json:/files/sa.json:ro \
     -e N8N_RUNNERS_ENABLED=false -e N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
     -e N8N_GOOGLE_SA_JSON=/files/sa.json \
     -e NODE_FUNCTION_ALLOW_BUILTIN=fs,crypto,https,http,path,buffer \
     -e NODE_FUNCTION_ALLOW_EXTERNAL=luxon \
     -e SHOPIFY_SHOP=... -e SHOPIFY_CLIENT_ID=... -e SHOPIFY_CLIENT_SECRET=... \
     -e GENERIC_TIMEZONE=Asia/Taipei -e TZ=Asia/Taipei \
     -e "OVERRIDE_MONTH_NAME=Apr 2026" -e "OVERRIDE_MONTH_NAME_YY=Apr 26" \
     -e OVERRIDE_MONTH_START_ISO=2026-04-01T00:00:00.000+08:00 \
     -e OVERRIDE_MONTH_END_ISO=2026-04-30T23:59:59.999+08:00 \
     --entrypoint n8n n8nio/n8n:latest execute --id=v5ParentMulti1
   ```
4. **Restart n8n** (`docker start n8n`).
5. **Reactivate all suppliers** in Registry.
6. Delete trailing `NO SALE THIS MONTH` placeholder if the run was idempotent (see bug above).

**For a clean rebuild** (e.g. after adding excludes or filling in reference prices for a past month): **delete the dest tab first** (`deleteSheet` via Sheets API or manually), then run the procedure above. The workflow will recreate the tab from scratch with the latest config.

Note: workflow only appends. Re-runs do **not** delete previously matched rows that are now excluded — manual deletion required for those.

## Resolved (was carryover)

- ✅ **Shopify `read_all_orders` scope** granted (verified — Jan 2026 now accessible). Granted scopes on token: `read_all_orders, read_customers, read_orders, read_products`.
- ✅ **v1 + v4 workflows deleted** from n8n DB on 2026-05-02. SQLite executed inside `python:3-alpine` container with `/volume1/docker/n8n/n8n_data` mounted (host user lacks write perms; container ran as root). Cleared rows from `shared_workflow`, `execution_entity`, `insights_metadata`, `workflow_history`, `workflow_statistics`, `workflow_dependency`, `workflow_publish_history`, `workflow_entity`. Workflow JSON files retained in repo as historical artifacts.
- ⏸️ **DSM password rotation** — deferred. Other projects are using the same credential during testing; revisit later.

## Anchors

- Suppliers Registry: https://docs.google.com/spreadsheets/d/1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs/edit
- Internal sheet (n8n output): https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit
- Service account: `n8n-sheets@ifb-n8n-integration.iam.gserviceaccount.com`
- Plan file (not in repo): `~/.claude/plans/n8n-shopify-linear-koala.md`
