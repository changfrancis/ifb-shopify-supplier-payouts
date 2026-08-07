# Status — production live, Aug 1 2026 cron clean; n8n upgraded to 2.33.3

## Production state

Single canonical workflow (v5) handles all 8 suppliers via Suppliers Registry. v4 retired.

**Cron:** `0 2 1 * *` Asia/Taipei (= SGT, GMT+8). **Last fired: 2026-08-01 02:00 SGT** — clean run on 2.27.5, 9/9 executions success (1 parent + 8 children), all 8 `Jul 2026 <Supplier> n8n` tabs + run logs written in 5m47s (02:00:00 → 02:05:47). **Next firing: September 1, 2026 02:00 SGT** (first scheduled cron on 2.33.3).

### Jul 2026 cron output (2026-08-01 02:00 SGT)

| Supplier | Rows | Flags |
|---|---:|---|
| Stan | 1 | clean |
| Piggy | 17 | clean |
| Bluebird | 4 | TITLE MATCH=2 |
| Ryan | 135 | TITLE MATCH=32, REFUND=8 |
| Bryan | 3 | clean |
| Dylan | 18 | TITLE MATCH=1 |
| Gavin | 159 | TITLE MATCH=5, REFUND=11 — **rebuilt 2026-08-06**, was 158 rows / 40 title-match |
| Vitae | 1 | clean |
| **Total** | **338** | |

⚠️ Ryan's 32 title-match rows are still outstanding — same suspected Shopify SKU-rename pattern. Gavin's is now resolved (see below).

| Supplier | Active | Latest verified | Status | Title hints | Excludes |
|---|---|---|---|---|---|
| Stan | TRUE | Mar–May 2026 | ✅ | `stinger` | (none) |
| Piggy | TRUE | May 2026 (rebuilt) | ✅ | `piggy,piggyfoam,pgf,piggy foam` | `kunlun-1.8-experimental-spring` |
| Bluebird | TRUE | Mar–May 2026 | ✅ | `gel,gels,bluebird,blue bird,bbgb` | (none) |
| Ryan | TRUE | Apr 2026 (rebuilt) + May 2026 | ✅ | `blu,accublu,dtb,holster,molle` | 25 SKUs |
| Bryan | TRUE | Jun 2026 (rebuilt) | ✅ | `stk` | (none) |
| Dylan | TRUE | May 2026 (rebuilt) | ✅ | `d2,dylan` | (none) |
| Gavin | TRUE | Apr–May 2026 | ✅ | `gfz,gavin,sbl,sbf` | 10 SKUs incl. `d2-victory-shroud-digital` |
| Vitae | TRUE | Mar–May 2026 | ✅ | `linny,linford,vitae,vitae precision,effort` | 5 SKUs (false-positive items) |

### May 2026 cron output (2026-06-01 02:00 SGT)

| Supplier | Rows | Notes |
|---|---|---|
| Stan | 1 | |
| Piggy | 5 | Rebuilt 2026-06-01 after `pgf-fenrir-717-3d-prints` SKU update; row count unchanged (no fenrir sales in May) |
| Bluebird | 4 | |
| Ryan | 89 | |
| Bryan | 7 | Rebuilt 2026-06-01 after Bryan refreshed sling SKUs in Amount Reference; **1 row → 7 rows** (was missing 6 sling sales that had no SKU match). Includes 1 row flagged `REFUND - verify` (Order 5107) |
| Dylan | 27 | Rebuilt 2026-06-01 after 14 SKU renames (D2-Worker handguards, low-rise rails, mousepads, deskmats); 9 title-match → **2 title-match** (7 rows now SKU-match cleanly with proper takehome) |
| Gavin | 63 | |
| Vitae | 9 | |

### Vitae onboarding completed (2026-05-04)

- Linford filled in all 51 SKUs' Listing / Fee / Takehome columns in `Vitae Amount Reference ` (trailing-space tab in `1KWz6wl5m4gDkBUOehvlmOWBv4IYj9X5fwS1Te8yRxD8`).
- Mar 2026 Vitae n8n re-run (delete + rebuild): **14 clean SKU matches** with proper takehome splits + 1 title match (custom barrel job). Was 13 yellow-flagged `ref price pending` rows before.
- Apr 2026 Vitae n8n re-run: 1 row (custom barrel machining for Order 4712). All 331 April orders scanned — only one Vitae-related line item exists for April, and it's a custom title-match. Reference SKUs didn't sell in April.

### Jun 2026 (manual run + targeted rebuilds, 2026-06-29..30)

Manual Jun 2026 run done 2026-06-29 ahead of the July 1 cron, then two targeted rebuilds today:

- **Gavin source tab rename**: source had `June 2026` (full month) but workflow expects `Jun 2026` (`LLL yyyy` template — what every other Gavin month uses). Renamed via Sheets API, rebuilt: **80 → 107 rows (+22 Walkin manual entries** for Gavin Purchase shipping deductions that had been silently dropped).
- **Bluebird rebuild for Order 5526**: order placed 2026-06-30 05:07 SGT (after the manual run). Bluebird Jun 2026 was 1 → **3 rows** (Order 5526 captured: `bbgb-mk3-thor`, `bbgb-shark-shus`).

| Supplier | Jun 2026 rows | Notes |
|---|---|---|
| Stan | 2 | |
| Piggy | 8 | |
| Bluebird | 3 | Rebuilt 2026-06-30 to capture Order 5526 (created after manual run) |
| Ryan | 200 | 113 title-match — possible Shopify SKU rename pattern, worth auditing after July 1 cron |
| Bryan | 6 | Clean — new sling SKUs working |
| Dylan | 11 | Clean — SKU refresh working |
| Gavin | 107 | Rebuilt 2026-06-30 after tab rename — 22 Walkin manual entries now flowing |
| Vitae | 1 | |

## Workflows in n8n

```
n8n list:workflow   (as of 2026-08-05, n8n 2.33.3)
  ShopifyErrHandle1     Shopify Sync — Error Handler            ACTIVE
  v5ChildPerSup1        Shopify Per-Supplier Sync v1 (child)    ACTIVE
  v5ParentMulti1        Shopify Multi-Supplier Sync v1 (parent) ACTIVE    ← cron 0 2 1 * * SGT
  v6Tshirt1             Shopify Tshirt Pre-orders v1            INACTIVE  ← manual trigger, on-demand
  v7FolderGrant1        Shopify Folder Grants v1                INACTIVE  ← imported 2026-08-05, dry run pending
  --- non-supplier workflows sharing this n8n instance ---
  EmailReqToDash1       Email Heads-up → Ops Dashboard          ACTIVE
  IfbReplyDrafter1      IFB Reply Drafter (scheduled batch)     ACTIVE
  IfbShopifySync1       IFB Brain: nightly Shopify sync         ACTIVE
  IfbFeedbackFwd1       IFB Brain: forward review verdicts      ACTIVE
  IfbOrdersToSheet1     IFB Orders -> Google Sheet              ACTIVE
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
- **Last verified run:** 2026-06-01 (post n8n 2.22.5 upgrade) — 32 orders pulled including a May 7 pre-order (5076), Order 4997 `Deez🥜` + Order 4996 `DuncanRyuu🇸🇬` flagged NON-ASCII, qty expansion verified, 2 CF rules stable. Tab leftmost in [internal sheet](https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit#gid=1367981525).

Container TZ: `Asia/Taipei` (verified inside container).

## Folder Grants automation (v7) — pending go-live

Standalone workflow that auto-shares Google Drive release folders (e.g. Mega Barrett SMC Release) to customers who buy the tagged SKU. Sharer identity is the existing service account (`n8n-sheets@ifb-n8n-integration.iam.gserviceaccount.com` — SA key reused, no new OAuth); Google sends its default "shared with you" notification email to the customer.

- **Trigger:** cron `*/15 * * * *` Asia/Singapore + manual trigger for testing.
- **Config location:** three new tabs on the internal sheet `1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM`:
  - `Folder Grants` — `SKU | Folder ID | Folder Name | Role | Active | Notes` (mapping table).
  - `Folder Grants Log` — `Timestamp | Order No | Customer Email | SKU matched | Folder ID | Folder Name | Status | Message`. Status ∈ `SHARED` / `ALREADY_SHARED` / `ERROR` / `NO_EMAIL`. Doubles as dedup source.
  - `Folder Grants Cursor` — `A2` holds `last_processed_iso` (updated_at high-water mark). Missing/empty → first run defaults to `now - CURSOR_FALLBACK_HOURS` (1h) to avoid scanning the whole store.
- **Prerequisites (one-time, not yet done):**
  1. Gavin adds the service-account email (Editor role) on each folder we want auto-shared. Confirmed targets available today: `Mega Barrett SMC Release` (`1MsyG4satjsITzwrTjqyjGwV9TMwpK87n`), `SBL2 (Release)` (`1UD3O2A_ub9fyYvMG9Hb1vZ1uzgVNIwmw`), `SBF (Release)` (`1jcHNC7modnlKCUUHd81Nts7h4ZjwUJMz`).
  2. Enable Drive API on the `ifb-n8n-integration` GCP project (Sheets is enabled; Drive is a separate enablement).
- **Real Mega Barrett SMC SKUs to seed into `Folder Grants`:** `MegaSMC-3dparts-BRT-XXXX`, `MegaSMC-3dparts-CQB-xxxx`, `MegaSMC-hwkit-grey`, `MegaSMC-hwkit-red`. All → Mega Barrett SMC Release folder.
- **Enhanced SKU placeholder rule (vs v5):** matches `COLOUR` (any case) OR any run of 3+ x's / X's. Handles the `XXXX`/`xxxx` colour placeholders on the Mega Barrett SKUs and any future 4+-X SKUs. Treats `-`/`_` interchangeably. v5's stricter `XXX`-only rule is unchanged and continues to drive the monthly pipeline.
- **Idempotency:** cursor prevents re-scanning old orders; log dedups within the cursor window by `(order_no, email, folder_id)`. Cursor only advances *after* the log append succeeds — a mid-batch failure re-processes the same window on the next tick, and log-based dedup makes that safe.
- **Auth note (non-obvious):** the workflow's JWT requests **both** `spreadsheets` and `drive` scopes in one token. The existing pipeline still requests spreadsheets-only tokens from the same SA key — unaffected.
- **Status (2026-08-05):** ✅ Drive API enabled on GCP. ✅ SA added as Editor on Mega Barrett SMC Release. ✅ Three tabs created on internal sheet + seeded with the 4 Mega Barrett SKU rows (Active=TRUE). ✅ Workflow imported into n8n as `v7FolderGrant1` (11 nodes) — **INACTIVE**, not yet executed.
- **⚠️ Next step — dry run NOT yet done.** Executing this workflow grants real Drive access and triggers Google's notification email to real customers. Per the approved plan, run first against a throwaway test folder before flipping `Active` on in n8n. Cursor is blank, so the first run scans `now − 1h` of paid orders.
- **Out of scope initially:** refund/cancellation does NOT revoke Drive access; no historical backfill for orders placed before go-live.

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

**1. Folder Grants dry run (blocking go-live).** `v7FolderGrant1` is imported but INACTIVE and never executed. Executing it grants real Drive access and fires Google's notification email to real customers — so per the approved plan, dry-run against a throwaway test folder first:
   - Create a test folder in your own Drive, add the SA as Editor.
   - Temporarily point a Folder Grants row at that test folder ID using a cheap real SKU.
   - Execute: `docker exec -e N8N_PORT=5699 -e N8N_RUNNERS_BROKER_PORT=5697 -e N8N_RUNNERS_TASK_BROKER_PORT=5697 n8n n8n execute --id=v7FolderGrant1`
   - Verify: (a) test folder's share list gained the order email, (b) `Folder Grants Log` shows one `SHARED` row, (c) `Folder Grants Cursor!A2` advanced.
   - Re-run with the cursor rolled back → expect `ALREADY_SHARED`, no duplicate permission.
   - Only then restore the real folder ID and activate the workflow.

**2. SKU audit for Ryan.** 32 title-match rows in Jul 2026, unresolved since June. **Now known to be a payout-accuracy issue, not cosmetic** — the Gavin rebuild proved title-match rows overstate supplier takehome by omitting the fee (Gavin was over by $272.59 in one month). Ryan's Amount Reference likely has dead refs from bulk Shopify SKU renames — same failure mode as the Bryan sling SKUs. Gavin's equivalent was resolved 2026-08-06.

**3. Sept 1, 2026 02:00 SGT cron** — first scheduled run on 2.33.3. Verify 8 child executions, 8 `Aug 2026 <Supplier> n8n` tabs, 8 run log entries, no 429s.

**4. Optional — DB bloat.** `IfbOrdersToSheet1` holds 946 MB of the 1.09 GB execution data. Not urgent (disk is at 3%), and it's an IFB Brain workflow rather than this repo's, but it shares the n8n instance. Fix would be `EXECUTIONS_DATA_SAVE_ON_SUCCESS=none` scoped to that workflow, or trimming its payload.

## System health check — 2026-08-05

| Check | Result |
|---|---|
| Disk `/volume1` | 160 GB / 7.0 TB — **3%** |
| Memory | 3.6 GB used / 11 GB, 6.7 GB available |
| Uptime | 17 days, load 1.53 (IO-bound, CPU 0.10) |
| n8n health | `{"status":"ok"}` |
| Execution pruning | Active (14-day default), oldest execution 2026-07-21 |
| v5 pipeline errors | **Zero** |

**⚠️ DB bloat — `IfbOrdersToSheet1` is the driver (not the supplier pipeline).** SQLite is 1.28 GB; execution payloads break down as:

```
IfbOrdersToSheet1     70 execs    946.2 MB   ← 87% of all execution data (13.8 MB/run, every ~3h)
EmailReqToDash1      387 execs     62.2 MB
v5ParentMulti1         1 exec      31.7 MB
v5ChildPerSup1         8 execs     29.9 MB
IfbShopifySync1       14 execs     15.5 MB
IfbFeedbackFwd1      675 execs      1.4 MB
IfbReplyDrafter1      69 execs       0.7 MB
ShopifyErrHandle1     33 execs       0.1 MB
TOTAL                            1,087.7 MB
```

VACUUM won't help — only 17 MB (1.3%) is reclaimable. Fix would be `EXECUTIONS_DATA_SAVE_ON_SUCCESS=none` scoped to `IfbOrdersToSheet1`, or trimming its payload. Not urgent at 3% disk usage. **Out of scope for this repo** (IFB Brain workflow), logged here because it shares the n8n instance.

**Failed executions (both outside the supplier pipeline):** `IfbFeedbackFwd1` 2026-08-04 15:00, `IfbOrdersToSheet1` 2026-07-29 01:00. The Shopify Error Handler fired 33 times, all triggered by IFB Brain workflows.

## 🐛 Timezone off-by-one in dates — FIXED 2026-08-07, historical data NOT yet corrected

**Found because Gavin asked why generated dates differed from his own monthly tab.**

### Root cause

`fmtDate()` used `d.getDate()` / `d.getMonth()` / `d.getFullYear()`, which read the **process** timezone. The n8n **JS Task Runner runs as a separate process (PID 19) that does NOT inherit `TZ`** from the container — it only gets `GENERIC_TIMEZONE`, which Node ignores. So Code nodes evaluated as **UTC** while the main n8n process (PID 7) correctly had `TZ=Asia/Taipei`.

Every timestamp between **00:00 and 07:59 SGT** therefore rendered **one day early**. Proven directly:

```
TZ=Asia/Taipei  ->  5 May 2026   (correct)
TZ unset (UTC)  ->  4 May 2026   (what the runner produced)
```

n8n exposes **no** config to pass `TZ` through to the internal runner (checked the full `N8N_RUNNERS_*` list — no env allowlist exists), so the fix had to be in the workflow code.

### Blast radius (measured against Shopify `created_at` as ground truth)

**277 Shopify-order rows across 4 months × 8 suppliers had the wrong date.**

| Month | Stan | Piggy | Bluebird | Ryan | Bryan | Dylan | Gavin | Vitae |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Apr 2026 | 1 | 0 | 1 | 6 | 0 | 4 | 13 | 0 |
| May 2026 | 0 | 0 | 1 | 13 | 1 | 5 | 13 | 0 |
| Jun 2026 | 0 | 1 | 3 | **118** | 5 | 1 | 9 | 0 |
| Jul 2026 | 0 | 6 | 0 | 29 | 1 | 2 | **44** | 0 |

Plus all **Walkin/manual** rows (they go through `parseDate()` → SGT midnight → `fmtDate()`, the worst case). Gavin May = 18 rows, Jun = 30 rows, all −1 day.

⚠️ **This predates the 2.22.5 upgrade** — April is affected too, so the runner has been UTC since the beginning, not since the upgrade.

⚠️ **Month-boundary crossings are the real damage.** Order 5539 was placed **1 Jul 2026 07:30 SGT** but renders as **`30 Jun 2026`** inside the *July* tab. A year boundary would be worse: `1 Jan 03:00 SGT` → `31 Dec 2026`.

Run Log timestamps were affected identically — the 1 Aug **02:00 SGT** cron was logged as `2026-07-31 18:00` (UTC).

### The fix (shipped to v5 child + v6 tshirt together, per the knowledge-transfer rule)

Replaced process-local getters with an explicit SGT conversion. SGT is UTC+8 year-round with no DST, so shifting the instant and reading UTC parts is exact and dependency-free — and **identical in both files** so they cannot drift:

```js
function fmtDate(d) {
  if (!d || isNaN(d.getTime())) return '';
  const sgt = new Date(d.getTime() + 8 * 3600 * 1000);
  return sgt.getUTCDate() + ' ' + MON[sgt.getUTCMonth()] + ' ' + sgt.getUTCFullYear();
}
```

Same treatment for the Run Log timestamp. `parseDate()` was already correct (it passes `zone: 'Asia/Singapore'` to Luxon explicitly) and is unchanged.

**Validation:** 6 boundary cases (00:36, 07:30, midnight, afternoon, year-rollover) — old code fails **5/6** under UTC, new code passes **6/6**; both pass under Taipei, so no regression. Live smoke test after deploy: `v6Tshirt1` → **0/8 wrong**, including order 5311 created 00:49 SGT which previously rendered a day early.

**Deploy gotcha:** `n8n import:workflow` reads `"active": false` from the JSON and **deactivates** the workflow. The child was silently deactivated on import — reactivated via `n8n update:workflow --id=v5ChildPerSup1 --active=true` **plus a container restart** (the CLI warns changes don't apply while n8n is running). Verified all 8 workflows active afterwards. **Always re-check active state after importing over a live workflow.**

### ⚠️ Still outstanding — historical data not corrected

The fix only affects **future** runs. The 277 wrong dates in the Apr–Jul 2026 tabs are still there. Sept 1's cron will produce a correct Aug 2026 but will not touch history. Remediation options:

1. **Rebuild Apr–Jul for all 8 suppliers** (~30 tabs) — most correct, but heavy churn; each needs the delete-and-rebuild dance and a manual-column safety check first.
2. **Rebuild only the months still unpaid** — least churn; paid months stay as historical record.
3. **Leave history, fix going forward** — dates stay wrong in past tabs.

Financially the amounts are unaffected (only the displayed date shifts), but month-boundary rows can appear under the wrong month, which matters for reconciliation.

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
     -e N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
     -e N8N_GOOGLE_SA_JSON=/files/sa.json \
     -e NODE_FUNCTION_ALLOW_BUILTIN=fs,crypto,https,http,path,buffer \
     -e NODE_FUNCTION_ALLOW_EXTERNAL=luxon \
     -e N8N_RUNNERS_TASK_RUNNER_NODE_FUNCTION_ALLOW_BUILTIN=fs,crypto,https,http,path,buffer \
     -e N8N_RUNNERS_TASK_RUNNER_NODE_FUNCTION_ALLOW_EXTERNAL=luxon \
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

- ✅ **Gavin Jul 2026 rebuild after 12 new SKUs (2026-08-06)** — Gavin added the `Gdart-*` (ribbed/plain × 200/1000), `gfz-mega-mag-*` (full/half × 7/10, hardware-only) and `MegaSMC-3dparts-*` families to his Amount Reference (26 → 38 SKUs). Rebuilt Jul 2026: **158 → 159 rows, TITLE MATCH 40 → 5**, exactly matching the pre-flight prediction (35 resolvable, 5 genuinely custom).
  - **Financial correction — this was not cosmetic.** Title-match rows assume the supplier keeps the full sale price (no known fee), so they were *overstating* Gavin's takehome. With real reference prices the fee is applied: **payout $10,484.31 → $10,211.72 (−$272.59)**. Per-unit examples: `Gdart-ribbed-1000` $70.00 → $59.50, `gfz-mega-mag-full-7` $15.00 → $2.25, `gfz-mega-mag-half-10` $16.24 → $13.50.
  - **Takeaway:** a high TITLE MATCH count is a *payout accuracy* problem, not just a cosmetic flag. Ryan's 32 rows carry the same risk and remain unaudited.
  - Remaining 5 title matches are legitimately one-off, no reference expected: `Custom GFZ 235fps Upgrade Spring` (5613), `SBL2 spare orings kit` (5737), `d2-SBL2-yuuka-digital` (5719), `gfz gdart 5box presale` (5784), `GFZ Neo orange display unit` (5778).
  - **Walkin cross-check passed** (per the standing rule): source `Jul 2026` tab has 16 manual/Walkin rows, dest has 16. Pre-rebuild backup at `/tmp/gavin_jul2026_backup.{json,csv}` on the NAS. Verified beforehand that `Payment Complete` / `Date of Payment` were both empty, so no human-entered data was at risk.
  - Executed with **zero downtime** via `n8n-run.sh` — first real use of the new helper.
- 🐛 **Fixed `n8n-run.sh` word-splitting bug (2026-08-06)** — the original `OVERRIDE="..."` env-var approach split on spaces, so `OVERRIDE_MONTH_NAME=Jul 2026` sent `2026` to docker as a container name (`Error response from daemon: No such container: 2026`). Rewritten to pass extra flags through as argv (`"$@"`), which preserves quoting. New form: `n8n-run.sh v5ParentMulti1 -e "OVERRIDE_MONTH_NAME=Jul 2026" ...`.

- ✅ **n8n upgraded 2.27.5 → 2.33.3** on 2026-08-05 (27 days before the Sept 1 cron — deliberate wide validation window). 16 DB migrations applied cleanly. All 10 workflows re-activated. Env vars survived the recreate (`NODE_FUNCTION_ALLOW_*`, `N8N_RUNNERS_TASK_RUNNER_NODE_FUNCTION_ALLOW_*`, SA mount at `/files/sa.json`, TZ `Asia/Taipei`). Smoke test: `v6Tshirt1` executed `status: success` — confirms JS Task Runner still loads `fs`/`crypto`/`https`/`luxon`; 9 rows written to `Tshirt Pre-orders`. Rollback image tagged `n8nio/n8n:rollback-2.27.5` (`sha256:07eb74b4...`). Backups: `database.sqlite{,-wal,-shm}.pre-2.33.3-2026-08-05.bak` + `docker-compose.yml.pre-2.33.bak`.
  - **New in 2.33.3:** Python task runner attempts internal-mode start and fails (`Python 3 is missing`) — benign, we only use the JS runner, which registers fine.
- ✅ **All n8n deprecation warnings cleared (2026-08-05)** — compose now pins every warned variable; startup log shows **zero** deprecations. Decisions were evidence-driven, not blanket-pinning:

  | Variable | Set to | Why |
  |---|---|---|
  | `N8N_RUNNERS_TASK_TIMEOUT` | `300` (keep old) | **Kept permissive deliberately.** Future default is 60s, but `v5ParentMulti1` runs 348s and `v5ChildPerSup1` 151s — dropping to 60s risks breaking the monthly cron. |
  | `N8N_COMPRESSION_NODE_MAX_DECOMPRESSED_SIZE_BYTES` | `268435456` (256 MiB — adopt new) | Audited all 10 workflows: **zero compression/zip nodes**. Pre-adopting the tighter default silences the warning *and* improves zip-bomb posture at no risk. |
  | `N8N_COMPRESSION_NODE_MAX_ZIP_ENTRIES` | `1000` (adopt new) | Same — no compression nodes in use. |
  | `N8N_UNVERIFIED_PACKAGES_ENABLED` | `false` (adopt new) | Every node across all workflows is official `n8n-nodes-base.*`; no community packages installed. |
  | `WEBHOOK_URL` → `N8N_WEBHOOK_URL` | renamed | Straight rename, identical semantics (sets base URL for both test + production webhooks). |

  Backups: `docker-compose.yml.pre-envpin-2026-08-05.bak`, `docker-compose.yml.pre-deprec2-2026-08-05.bak`.
- ✅ **CLI runner helper `/volume1/docker/n8n/n8n-run.sh` (2026-08-05)** — `n8n execute` inside the running container conflicts on **Task Broker port 5679**, not 5678 as you'd expect. The helper overrides both the HTTP and broker ports so a one-shot execution coexists with production, **eliminating the old stop-container → `docker run --rm` → restart procedure** (and its downtime). Usage:

  ```bash
  /volume1/docker/n8n/n8n-run.sh                  # no args -> usage + workflow list
  /volume1/docker/n8n/n8n-run.sh v6Tshirt1        # execute by ID
  OVERRIDE="-e OVERRIDE_MONTH_NAME=Apr 2026" \
    /volume1/docker/n8n/n8n-run.sh v5ParentMulti1 # with month-override env
  ```

  Verified end-to-end: `v6Tshirt1` → `status: success` in 18s, zero downtime.
- ✅ **Aug 1 2026 cron clean (2026-08-01 02:00 SGT)** — last run on 2.27.5. 9/9 executions success, 337 rows across 8 suppliers, 5m47s end-to-end.
- ✅ **Folder Grants prerequisites completed (2026-08-05)** — Drive API enabled, SA granted Editor on Mega Barrett SMC Release, 3 sheet tabs created + seeded, workflow imported as `v7FolderGrant1`. Dry run still outstanding.

- ✅ **n8n upgraded 2.17.8 → 2.22.5** on 2026-06-01 (post-cron). 6 DB migrations applied cleanly. Removed deprecated `N8N_RUNNERS_ENABLED=false` from compose. Code nodes still work — JS Task Runner uses `N8N_RUNNERS_TASK_RUNNER_NODE_FUNCTION_ALLOW_BUILTIN=fs,crypto,https,http,path,buffer` (already set). DB backup at `/home/node/.n8n/database.sqlite.pre-upgrade-2026-06-01.bak` (1.07 GB); compose backup at `/volume1/docker/n8n/docker-compose.yml.pre-2.22.5.bak`. Smoke test: v6Tshirt1 re-run successful (32 rows, 2 CF rules, emoji preserved).
- ✅ **n8n upgraded 2.22.5 → 2.27.5** on 2026-06-30 (~15 hours before July 1 cron). No DB migrations needed (2.22.5 already current schema). All 3 active workflows re-activated cleanly. Smoke test v6Tshirt1 passed (10 rows, 2 CF rules, JS Task Runner working with fs/crypto/https/luxon). DB backup at `/volume1/docker/n8n/n8n_data/database.sqlite.pre-2.27.5-2026-06-30.bak`.
- ✅ **Gavin Jun 2026 tab rename + rebuild (2026-06-30)** — source had `June 2026` instead of `Jun 2026` (anomaly vs all other Gavin months); workflow read 0 rows from walkin source. Renamed via Sheets API, deleted dest, rebuilt: 80 → 107 rows (+22 Walkin manual entries recovered).
- ✅ **Bluebird Jun 2026 rebuild for Order 5526 (2026-06-30)** — order placed after the manual run; rebuild captured `bbgb-mk3-thor` + `bbgb-shark-shus`. 1 → 3 rows.
- ✅ **Bryan dual-mag-pouch SKU add + Jun 2026 rebuild (2026-07-01)** — orders 5457 (qty 4) + 5462 (qty 1) had SKU `stk-worker-dual-mag-pouch` not in ref. First attempt added `stk-worker-mag-pouch-2x` (Bryan interpreted "dual" as "2x"), which didn't match Shopify's literal `dual`. Added `stk-worker-dual-mag-pouch` ($19/$5/$14 same as 2x) alongside; rebuilt Jun 2026 Bryan: 7 → 11 rows.
- ✅ **July 1 cron success (2026-07-01 02:00 SGT)** — first scheduled cron on n8n 2.27.5, mode=`trigger` (not manual). All 8 suppliers appended cleanly, +30 orders for June 29–30 sales. Total: Stan 3, Piggy 9, Bluebird 4, Ryan 209, Bryan 11, Dylan 13, Gavin 121, Vitae 2.
- ✅ **Dylan SKU refresh (2026-06-01)** — added 14 new lowercase-hyphenated SKUs to Amount Reference (Worker handguards, low-rise rails, mousepads, deskmats) alongside the old uppercase-space variants for historical reference. May 2026 rebuilt cleanly (9 → 2 title-match).
- ✅ **Piggy fenrir SKU update (2026-06-01)** — added `pgf-fenrir-717-3d-prints` to Amount Reference. May 2026 rebuilt (preventative; no fenrir sales in May).
- ✅ **Bryan sling SKU refresh (2026-06-01)** — added 4 new sling SKUs to Amount Reference (`stk-qd-swivel-mount`, `sling-qd-pic-mount`, `sling-2pt-black-1000d`, `sling-2pt-multicam-500d`); old `stk-sling-*` refs kept as historical. May 2026 rebuilt → **1 row → 7 rows** (was silently missing 6 sales). Bryan supplier has only the title hint `stk` so SKUs without that prefix were dropping through. **Lesson**: when Shopify renames SKUs in bulk for a supplier, dead refs are silent — only the SKU audit catches them.
- ✅ **Shopify `read_all_orders` scope** granted (verified — Jan 2026 now accessible). Granted scopes on token: `read_all_orders, read_customers, read_orders, read_products`.
- ✅ **v1 + v4 workflows deleted** from n8n DB on 2026-05-02. SQLite executed inside `python:3-alpine` container with `/volume1/docker/n8n/n8n_data` mounted (host user lacks write perms; container ran as root). Cleared rows from `shared_workflow`, `execution_entity`, `insights_metadata`, `workflow_history`, `workflow_statistics`, `workflow_dependency`, `workflow_publish_history`, `workflow_entity`. Workflow JSON files retained in repo as historical artifacts.
- ⏸️ **DSM password rotation** — deferred. Other projects are using the same credential during testing; revisit later.

## Anchors

- **Sheets Index** (quick links to all sheets, leftmost tab in internal sheet): https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit#gid=1615623275
- Suppliers Registry: https://docs.google.com/spreadsheets/d/1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs/edit
- Internal sheet (n8n output): https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit
- Service account: `n8n-sheets@ifb-n8n-integration.iam.gserviceaccount.com`
- Plan file (not in repo): `~/.claude/plans/n8n-shopify-linear-koala.md`
