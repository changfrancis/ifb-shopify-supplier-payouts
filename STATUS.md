# Status — SGD-reference pricing + 10% product fee confirmed; shipping excluded; hint matches record WHY (Vitae reviewed)

## Production state

Single canonical workflow (v5) handles all 8 suppliers via Suppliers Registry. v4 retired.

**Cron:** `0 2 1 * *` Asia/Taipei (= SGT, GMT+8). **Last fired: 2026-09-01 02:00 SGT — FAILED** on a transient Google Sheets 503 at `Read Suppliers Registry`; zero suppliers dispatched. Recovered by manual re-run the same day (282 rows, Aug 2026). Retry hardening has since been added to every Sheets node — see the failure write-up below. **Next firing: October 1, 2026 02:00 SGT** (first run with retry protection; also the second month on the TZ-safe date code).

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
n8n list:workflow   (as of 2026-09-02, n8n 2.36.9)
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
- **NEW (2026-09-03)**: courier/delivery line items (`lalamove`, `fedex`, `shipping`, `delivery fee`, …) are skipped when they are **only** a hint match — shipping is never supplier revenue. A shipping SKU the supplier has explicitly priced in their own Amount Reference is kept
- **NEW (2026-09-03)**: a hint match records *which field and which hint* fired, in Remarks — `TITLE MATCH [note:'linford'] vendor="SweetHeart" - add to Amount Reference?`. A match resting **only** on `note`/`tags` is labelled `TITLE MATCH WEAK`. See "Hint matches now say why" below
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

**3. Oct 1, 2026 02:00 SGT cron** — first run with retry protection on the Sheets nodes, and the second month on the TZ-safe date code. Verify: 1 parent + 8 child executions all `success`, 8 `Sep 2026 <Supplier> n8n` tabs, 8 Run Log entries with **SGT** timestamps (~`02:0x`, not `18:0x`), and no 429/503. If a Sheets node 503s again, the retry should absorb it — check the execution for a retried-then-succeeded node rather than a hard failure.

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

### Historical data — DECISION: left uncorrected (user call, 2026-08-07)

The fix only affects **future** runs. **Apr–Jul 2026 tabs keep their wrong dates by decision** — they stand as the historical record of what was actually generated and paid. Rebuilding was considered and declined; no action pending.

Consequences to keep in mind when reading those tabs:

- Amounts are **unaffected** — only the displayed date shifts, so payouts already made were correct.
- **277 Shopify rows** in Apr–Jul 2026 show a date one day earlier than the true SGT order date (every order placed 00:00–07:59 SGT). Gavin's Walkin/manual rows likewise: May 18, Jun 30.
- **Month-boundary rows read as the wrong month.** Order 5539 sits in the *Jul 2026 Gavin n8n* tab showing `30 Jun 2026`. If a supplier queries a date against their own records, this is the likely reason — their sheet is right, ours is a day early.
- **Aug 2026 onward is correct** (Sept 1 cron is the first clean month). A step change in date accuracy occurs at the Jul/Aug boundary — do not treat it as a data anomaly.
- Run Log timestamps before 2026-08-07 are **UTC**, not SGT (subtract 8h to read them as the cron's actual SGT firing time — e.g. the 1 Aug 02:00 SGT run is logged `2026-07-31 18:00`).

## 🔴 Sept 1 2026 cron FAILED — recovered same day (2026-09-01)

**The scheduled run produced nothing. All 8 August tabs were missing until a manual re-run.**

### What happened

Execution 5091, `v5ParentMulti1`, `mode=trigger`, fired 2026-08-31 18:00 UTC (= Sept 1 02:00 SGT) and errored after ~13s. It got four nodes deep:

| Node | Result |
|---|---|
| Monthly Cron (1st @ 02:00) | ✓ |
| Set Parameters | ✓ 50ms |
| Get Shopify Token | ✓ 445ms |
| Fetch All Orders (paginated) | ✓ 11 357ms |
| **Read Suppliers Registry** | ✗ **NodeApiError: Service unavailable (503)** |

A **transient Google Sheets 503** on the registry read. Because the parent could not load the registry, it never dispatched a single child — **zero suppliers processed, 8/8 August tabs missing**. The error workflow did fire correctly (exec 5092, 13s later) and sent the failure email.

**Red herring:** the logs are full of `SQLITE_CONSTRAINT: FOREIGN KEY constraint failed` around that timestamp. Unrelated — it comes from the insights-pruning subsystem ("Pruning old insights data" appears alongside) and is ongoing background noise, not the cause.

### Recovery

Manual re-run of `v5ParentMulti1` with the Aug 2026 override — 1 parent + 8 children, all success. **282 rows** written:

| Supplier | Rows | Flags |
|---|---:|---|
| Stan | 1 | clean |
| Piggy | 4 | TITLE MATCH=4 |
| Bluebird | 1 | REFUND=1 |
| Ryan | 124 | TITLE MATCH=23, REFUND=6 |
| Bryan | 14 | clean |
| Dylan | 14 | TITLE MATCH=1 |
| Gavin | 119 | TITLE MATCH=13, REFUND=5, CANCELLED=1 |
| Vitae | 5 | TITLE MATCH=5 |
| **Total** | **282** | |

### ✅ Timezone fix confirmed in production

Aug 2026 is the first month generated with the TZ-safe `fmtDate`. Checked every Shopify row against `created_at`: **0 wrong dates out of 282**, and **23 of those orders fell in the previously-broken 00:00–07:59 SGT window**. Run Log timestamps now read SGT (`2026-09-01 12:43:22`) instead of UTC.

### Root fix — retry hardening (the real gap)

Not one Google Sheets node in *either* workflow had retry configured. A single transient blip could — and did — kill an entire month. Now added:

| Workflow | Node | Retry |
|---|---|---|
| parent | Read Suppliers Registry | **5 tries / 3000ms** (single point of failure for the whole month) |
| parent | Get Shopify Token | 3 / 2000ms |
| child | all 7 Sheets nodes | 3 / 2000ms |

The child nodes matter **more** than their `onError: continueRegularOutput` suggests: a silent 503 there does not stop the run, it produces *wrong* data — a failed `Read Amount Reference` turns every row into TITLE MATCH, a failed `Read Existing Destination Rows` breaks dedup and duplicates rows. Verified live in the n8n DB after import.

`Execute Per-Supplier Sync` deliberately has **no** retry: it already uses `onError: continueRegularOutput` so one bad supplier cannot block the rest, and retrying a sub-workflow that partially completed risks double-appending rows.

### ⚠️ Deploy trap (hit twice now — always check)

`n8n import:workflow` reads `"active": false` from the JSON and **silently deactivates the live workflow**. Both parent and child were deactivated on import. Recovery is `n8n update:workflow --id=<ID> --active=true` **plus a container restart** — the CLI explicitly warns changes do not apply while n8n is running. Always re-verify active state after any import.

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

## Aug 2026 rebuild — 2026-09-02

Re-ran all 8 suppliers after a pre-flight SKU review. **271 rows, $11,784.56 takehome, 0 wrong dates** (22 orders fell in the previously-broken 00:00–07:59 SGT window and all landed correctly).

| Supplier | Rows | Takehome | Flags |
|---|---:|---:|---|
| Stan | 1 | $86.00 | clean |
| Piggy | 4 | $240.00 | clean — **was 4 TITLE MATCH** |
| Bluebird | 1 | $136.00 | REFUND=1 |
| Ryan | 117 | $5,976.40 | TITLE MATCH=16, REFUND=5 — **was 124 rows / 23** |
| Bryan | 14 | $273.00 | clean |
| Dylan | 14 | $160.90 | TITLE MATCH=1 |
| Gavin | 115 | $4,391.16 | TITLE MATCH=9, REFUND=7, CANCELLED=1 — **was 119 rows / 13** |
| Vitae | 5 | $521.10 | TITLE MATCH=5 |

### 1. Piggy's 4 TITLE MATCH rows were an artifact of the Sept 1 recovery run, not a data gap

`pgf-hana-hardware-kit` and `pgf-breacher-hardware-kit` were byte-identical to the reference and matched the workflow's own regex — yet all 4 Piggy rows were flagged, the signature of `Read Amount Reference` returning empty. That run went straight into the Google Sheets flakiness while the node still had `onError: continueRegularOutput` and **no retry**, so it silently produced guesses. This is exactly the failure mode predicted when the retry hardening was added — it had already happened. Rebuild fixes it: 4 → 0 TITLE MATCH, takehome now $240.00 with real fees applied.

### 2. Cross-supplier contamination — $1,029.59 credited to the wrong supplier

Excluded only the **provable** cases (SKU matches a *different* registered supplier's Amount Reference):

| Was on | SKU | Value | Belongs to |
|---|---|---:|---|
| Ryan | `sbl2-hwkit-cobaltblue` x2 | $499.62 | Gavin (`sbl2-hwkit-COLOUR`) |
| Ryan | `bbgb-shark-shus` | $170.00 | Bluebird (`bbgb_shark_shus`) |
| Ryan | `sbl2-3dparts` | $149.13 | Gavin |
| Ryan | `dd-kar98k-printed-parts-only` | $106.84 | see the `_`/`-` bug below |
| Ryan | `gfz20bcar-blue` x2 | $104.00 | Gavin (`gfz20bcar-COLOUR`) |
| Gavin | `sling-2pt-black-1000d` | $32.23 | Bryan |
| Gavin | `d2-SBL2-victory-shroud-digital` x2 | $20.25 | Dylan |
| Gavin | `d2-sbl2ex-longspearshroud-digital` | $9.97 | Dylan |

### 3. Latent bug — `exclude_skus` does NOT do `-`/`_` interchange

The **SKU matcher** treats `-` and `_` as interchangeable; the **exclude matcher** does not — it only handles `*` and case-insensitivity. So Ryan's existing excludes `bbgb_shark_shus` and `DD_kar98k_printed_parts_only` were **silently inert** against the hyphenated SKUs Shopify actually sends. Worked around by adding hyphen forms (recovered another $106.84); the proper fix is to apply the same `[-_]` normalisation used by the SKU matcher.

**Still at risk (underscore form, never matching):** `bbgb_heavy_blue_gels`, `DD_kar98k_printed_parts_assembled`, `bbgb_M870_Remington`, `G_minx`.

### 4. Root cause — title hints match things that do not identify a supplier

Verified against Shopify's `vendor` field. Every mis-attributed row matched on:

- **Colour words** — Ryan's hint `blu` matches "Blue" anywhere: `gfz20bcar-blue`, `sbl2-hwkit-cobaltblue`, `ait-18-mag-blue`, `worker-15-straight-blue`, `storm-404-blue-fullbuild`, "Sky Blue".
- **Customer property values** — order 6182 matched a colour selection: `Primary (Blue in Product Photos)=Blue`.
- **Free-text order notes** — `sabre-tdarts-white-red` went to Gavin because a note read *"missed lee enfield metal handle and SBL"*; `diana-cnc-slide-black` went to Vitae because the note was literally `Linford`.

Actual vendors: **SweetHeart, Diamond Dogs, Sabre, Hare Technology, IFB.SG** — none are registered suppliers, and IFB.SG is the house brand. **Decision 2026-09-02:** leave those vendors alone for now, keep Ryan's `blu` hint as-is, fix only provable cases via excludes.

### Still outstanding — 31 units, $4,093.84 unpriced

Genuinely absent from their supplier's reference, so takehome is the full sale price with **no fee deducted** (over-crediting, same as the Gavin issue that cost $272.59 in July):

- **Ryan** — `Heilun Cuckoo - Sky Blue & Light Pink` x5 $1,596.75 · `storm-404-blue-fullbuild` $820 · `Custom 404 Storm | Blue Tube` $820 · `ait-18-mag-blue` x7 $105 · `Ryan Blu ZWQ30 upgrade` $20 · `worker-15-straight-blue` $10. **Confirmed NOT Ryan's** (vendors SweetHeart / IFB.SG / unset) but pending a decision on those vendors.
- **Gavin** — `GFZ | NEO BCAR 5-Row 7°` x2 $104 · `sabre-tdarts-white-red` $26.86 · `Lalamove for GFZ 4s LiPo` $18 · `GFZ SBL2 Spring` + `gfz sbl2 spring` $24 (**same item, two casings**) · `GFZ parts` $3.13 · `Gavin forehead kiss` $0.00
- **Vitae** — `vitae folding buttstock-1` $372.10 · `diana-cnc-slide-black` $140 · `storm-mag-magnet` x3 $9
- **Dylan** — `d2-sbl1-deskmat-3060` $25 (SBL1 variant of the existing `d2-sbl2-deskmat-3060`)

Vitae shows all 5 rows as TITLE MATCH, but this is **not** a read failure — each SKU was tested against the current reference and is genuinely absent. Vitae simply had only 5 rows this month. **4 of those 5 rows turned out to be false positives — see the Vitae audit below.**

Pre-rebuild backups of all 8 tabs: `/tmp/aug2026_backup/` on the NAS (json + csv per supplier).

### Supplier-by-supplier review — Vitae (2026-09-03)

Every Aug 2026 Vitae row was replayed through the workflow's exact matcher against the live Shopify orders (`/tmp/probe_vitae.py` on the NAS).

| Order | SKU | $ | Shopify vendor | Matched on |
|---|---|---:|---|---|
| 6037 | `storm-mag-magnet` ×3 | 9.00 | **SweetHeart** | ❌ `order.note` only |
| 5918 | `diana-cnc-slide-black` | 140.00 | **Hare Technology** | ❌ `order.note` only |
| 6159 | `vitae folding buttstock-1` | 372.10 | **Vitae Precision** | ✅ title + vendor |

**$149.00 of Vitae's $521.10 is misattributed.** Order 6037's note reads *"To be picked up by linford of vitae precision, lord of the wood makers"* and order 5918's note is literally `Linford` — Linford is the **person collecting the order**, not the maker of the item. `order.note` sits in the same hint haystack as the product fields, so three SweetHeart magnets and a Hare Technology slide landed in his tab. Not one product field on either order mentions Vitae.

This is the same vector that pulled Gavin's `sabre-tdarts-white-red` in off a note mentioning "SBL". It is a **general** flaw, not a Vitae one.

Order 6159 is genuinely Linford's but absent from his 51-SKU Amount Reference, so its $372.10 is the Shopify sale price, not an agreed takehome. **Open: needs a reference price.**

### Pricing rules confirmed by the user (2026-09-03)

- **All products are referenced in SGD. Currency conversion is ignored.** Suppliers are paid the SGD figure in their Amount Reference, whatever the customer paid in.
- **Product sale fee = 10%.** Labour/service jobs (e.g. Linford's barrel machining) are **TBC** — do not assign a fee.
- **Shipping is never included in the extract** as supplier revenue.

**Do NOT "fix" the currency check.** `o.currency` is Shopify's *shop* currency and is always `SGD`, so the `CURRENCY:` flag has never fired on any order since the workflow was built — the customer's currency is `o.presentment_currency`. This looks like a bug and was investigated as one, but per the rule above it is the **desired** behaviour: FX is irrelevant to payouts. Left as-is deliberately.

Why it surfaced: order 6159's buttstock showed `$372.10` against a `$350.00` Shopify list price. It was a US order — customer paid **USD 293.00**, settled as SGD 372.10 (Shopify market adjustment + FX). Same signature across `vitae-galaxy` (CAD 347 → $318.28), `vitae-aeb-grip-03-jatoba` (GBP 130 → $222.82), `vitae-aeb-grip-02-osage` (AUD 199 → $181.00), `vitae-purple-maple` (CAD 80 → $74.77), plus `city-r-brace` and `zius-bk2s-buttstock`. All ~6% over SGD list.

**Consequence to remember:** SKUs *in* an Amount Reference are unaffected — they are paid the reference amount (`vitae-galaxy` sold for $318.28, Linford correctly got $280). Only **title-match rows have no reference**, so they take the raw Shopify SGD figure and can be FX-inflated by ~6%. That is what made the buttstock read $372.10 instead of $350.

### Vitae fee schedule, derived from all 51 priced reference rows

Fee is 10% of listing, floored to whole dollars — **except 11 rows at $210 and above, which are all flat $20**:

| SKU | Listing | Fee charged | 10% would be |
|---|---:|---:|---:|
| `vitae-tiger-koa`, `-azure-blush`, `-black-pink`, `-galaxy`, `-nebula-blue`, `-turqoise-jade` | $300 | $20 | $30 |
| `vitae-aeb-grip-07-blackwood` | $250 | $20 | $25 |
| `vitae-aeb-grip-05-purpleheart`, `-06-ebony` | $240 | $20 | $24 |
| `vitae-aeb-grip-03-jatoba`, `-04-redheart` | $210 | $20 | $21 |

$75 of fees per unit sold across those 11 SKUs. One row goes the other way: `vitae-mystery-knob` is $30 listing / $5 fee (10% = $3). **Open: confirm with Linford whether the $20 is a real agreement on higher-value pieces or a stale hand-entry.**

### 'NO SALE THIS MONTH' placeholder fired on re-runs (fixed 2026-09-03)

Found by re-running the Aug 2026 parent over already-populated tabs: **7 of 8 tabs gained a junk `NO SALE THIS MONTH` row**, takehome unaffected ($0.00 rows).

The guard was `if (orderedRows.length === 0)`. That array is empty in **two** situations and only one is a genuine no-sale month — on a re-run every row dedups away, so it is empty while the tab is actually full. Fixed by additionally requiring the destination to be empty:

```javascript
if (orderedRows.length === 0) {
  if (existingRows.length > 0) return [];   // re-run over a populated tab, not a no-sale month
  ...
}
```

**Not new.** A sweep of Mar–Aug found **11** stray rows: 7 from the 2026-09-03 re-run and **4 from Jun 2026** (Stan, Piggy, Bluebird, Vitae), dating to the 2026-06-29/30 targeted rebuilds. All 11 deleted after verifying each row was the placeholder and that real rows remained. `Mar 2026 Bluebird` keeps its placeholder — it is that tab's only row, which is what the feature is for.

**Sheets API 429.** The first purge attempt was rate-limited mid-scan (48 tab reads on top of a verification pass; the quota is ~60 reads/min/user). It failed **before any deletion**. Redone as a targeted purge of the 11 known rows with exponential backoff and a 1.2s inter-call pause. Worth remembering for any future full-sheet sweep.

### Vitae Aug 2026 rebuilt (2026-09-03)

User confirmed `diana-cnc-slide-black` and `storm-mag-magnet` are **not Vitae's**. Both added to his `exclude_skus`; tab deleted and rebuilt.

| | Before | After |
|---|---:|---:|
| Rows | 5 | **1** |
| Takehome | $521.10 | **$315.00** |

Jul 2026 Vitae re-audited at the same time: **clean** — 1 row, `vitae-galaxy`, matched his reference at the SGD $300 (the customer paid CAD 347; the reference price correctly won). No change needed.

**Buttstock resolved.** The rebuild alone could not fix its `$372.10` — with no reference row the workflow has nothing to price against and falls back to the Shopify SGD figure, which is the FX-inflated one from that USD order. Appended `vitae folding buttstock-1 | $350.00 | $35.00 | $315.00` to row 53 of `Vitae Amount Reference ` (append only, nothing overwritten) and rebuilt again. The row is now **$350.00 / $315.00 and carries no flag at all** — it matches the reference, so the SGD price wins, exactly as `vitae-galaxy` does.

**Final: Vitae Aug 2026 = 1 row, $315.00** (was 5 rows / $521.10).

The placeholder fix was confirmed by this second re-run: seven populated tabs, **zero** stray `NO SALE` rows added.

Backup of the pre-rebuild tab: `/tmp/vitae_aug_backup/` on the NAS.

**Still outstanding:** Gavin's `Lalamove for GFZ 4s LiPo` **$18.00** row is still present in `Aug 2026 Gavin n8n`. The shipping filter prevents it being re-added but cannot remove what is already there — that needs either a single-row delete or a Gavin tab rebuild.

### Shipping is not supplier revenue (2026-09-03)

`isShippingCharge()` in the v5 child drops courier/delivery line items **when they are only a hint match**. A shipping SKU the supplier has explicitly priced in their Amount Reference is kept — that is a deliberate agreement, not a false positive.

Found by scanning Apr–Aug across all 8 suppliers. Exactly **one** offender: `Lalamove for GFZ 4s LiPo` (order 6194, Aug 2026), a courier fee credited to Gavin as **$18.00** of product revenue because the title contains `gfz`.

Safety-checked before deploy: **0 of 246** Amount Reference SKUs and **1 of 275** distinct Shopify SKUs affected — the Lalamove line, nothing else.

**Gavin's 87 Walkin Fedex rows are deliberately untouched.** Those are `$0.00` listing / negative takehome entries (`-$36.79`, remarks `Fedex 870770846133`) that Gavin records in his *own* sheet as deductions from his payout — **-$4,379.33** across Apr–Aug. They are shipping *costs he absorbs*, not revenue. The filter only runs against Shopify line items; Walkin rows are processed further down and never reach it. Dropping them would overpay Gavin by $4,379.33.

### Hint matches now say why (2026-09-03)

**Decision (user):** *"false positive is better than missing it"* — keep matching on `order.note`, but make every hint match auditable from the sheet instead of dropping the field. Rejected the alternative (removing `note`/`tags` from the haystack) because a missing payout row is worse than a labelled spurious one.

`titleHints()` in the v5 child now returns `{ weak, why }` instead of a boolean, and the Remarks cell carries the evidence:

```text
TITLE MATCH [title:'vitae','vitae precision' vendor:'vitae','vitae precision'] vendor="Vitae Precision" - add to Amount Reference?
TITLE MATCH WEAK [note:'linford','vitae','vitae precision'] vendor="SweetHeart" - add to Amount Reference?
TITLE MATCH WEAK [note:'linford'] vendor="Hare Technology" - add to Amount Reference?
```

- `WEAK` = matched **only** on `note`/`tags` (free-text logistics), no product field. One filter — Remarks contains `TITLE MATCH WEAK` — surfaces every row of this class across all 8 suppliers.
- `vendor="…"` echoes Shopify's vendor field, the fastest ownership signal.
- `name` is suppressed when it only echoes `title`/`variant` (it is those two concatenated).
- `TITLE MATCH - ref price pending` now also names the reference row it hit: `[ref:<sku>]`.
- Existing `countFlag('TITLE MATCH')` in the Run Log still counts both classes — the string is a prefix, so no Run Log schema change was needed.

Verified before deploy: `node --check` on the whole Match node, plus a harness replaying the three real Vitae line items above and a no-hint control. Imported to `v5ChildPerSup1`, re-published, container restarted, 8/8 workflows active.

**Takes effect on the next run** — the Aug 2026 tabs still show the old bare `TITLE MATCH - add to Amount Reference?` until rebuilt.

**Note:** `n8n update:workflow` is now deprecated in 2.36.9 in favour of `n8n publish:workflow --id=<id>`. The old form still works and still requires the container restart.

**Not applied to v4** — `v4` no longer exists in n8n (retired when Gavin folded into the Registry; `n8n list:workflow` shows 10 workflows, none of them v4). Its repo JSON has already drifted (hardcoded hints, un-fixed TZ bug) and was deliberately left alone rather than half-ported. **Open: decide whether to delete `n8n-workflow-shopify-monthly-sku-v4-import.json` or mark it retired**, since the knowledge-transfer rule can no longer be honoured for it. `v6Tshirt1` has no title-hint logic, so nothing to port there.

## Resolved (was carryover)

- ✅ **Stack update round 2 (2026-09-02)** — n8n off the EOL 2.33.x line, plus every container image refreshed again. All 15 containers healthy, zero errors after settle.
  - **n8n 2.33.7 → 2.36.9** (3 minor versions). **2.33.x had gone EOL** — no further patches — which is what forced the jump rather than another patch-level hop. The fix that mattered: **2.35.5 "Avoid restarting task runners that are only slow"** — directly relevant because the parent runs ~348s and the child ~151s, so a runner killed for slowness is exactly how a monthly cron would die. **13 migrations** applied cleanly.
  - **Image pin moved to `n8nio/n8n:2.36.9`** — keep pinning; bump deliberately. Backup: `docker-compose.yml.pre-2.36.9.bak`.
  - **✅ Upgrading does NOT deactivate workflows** — unlike `import:workflow`, a `compose up -d` version bump preserved all 8 active. Verified retry config survived all 13 migrations (parent registry 5×3000ms, token 3×2000ms, all 7 child Sheets nodes 3×2000ms) and re-ran the `v6Tshirt1` smoke test to confirm Code nodes still load `fs`/`crypto`/`https`/`luxon`.

  | Container | Before | After |
  |---|---|---|
  | n8n | 2.33.7 | **2.36.9** (pinned) |
  | 3dps-db | PostgreSQL 15.18 | **15.19** |
  | dolibarr-db | MariaDB 10.11.18 | **10.11.19** |
  | dolibarr-app, nginx, clamav, autoheal, cloudflared ×2 | stale | current |
  | tailscale | 1.102.3 | unchanged — registry `last_updated` moved but the amd64 digest did not |

  - Same safety procedure: `pg_dumpall` (15 MB, marker verified) + `mysqldump --single-transaction` (20 MB, trailer verified) + n8n SQLite + all 5 compose files into `/volume1/docker/_preupdate_2026-09-02/`, and 9 `:rollback-20260902` image tags. Data verified after: Postgres 25 tables / 48 MB, MariaDB 372 tables / 2 users, dolibarr HTTP 200, n8n healthz + UI HTTP 200, both Cloudflare tunnels 12 connections each.
  - **Benign noise not to chase:** cloudflared logs `failed to sufficiently increase receive buffer size` on every start (standard quic-go notice on Linux UDP defaults), and 3dps-tunnel briefly logs `Unable to reach the origin service ... lookup nginx` during the restart window before nginx finishes coming up. Both clear on their own — 0 errors across all services 2 minutes after settle.
- ✅ **DSM upgraded 7.3.2 → 7.4.1** (build 90080) by the user, ~2026-08-27. This closes the one layer I could not reach (`synoupgrade` needs an interactive sudo password). Explains the ~6-day uptime; checked for fallout and found **no execution gaps** — nothing was dropped by the reboot.

- ✅ **Full stack update (2026-08-07)** — n8n plus every stale container image on the NAS, all 15 containers healthy afterwards, zero unhealthy/restarting.
  - **n8n 2.33.3 → 2.33.7.** Chosen over 2.34.4 deliberately: both carry the *same* core fixes, but 2.33.7 is patch-level on a line already validated, whereas 2.34.4 was a minor bump released hours earlier with no soak. The relevant fixes are all task-runner ones, which matter because the whole pipeline runs Code nodes there — *task broker resilience when a runner dies* (2.33.4), *recover unresponsive task runners* (2.33.4), *fix task runner health check failing* (2.33.7). A hung runner during the Sept 1 cron would mean a missed payout run. 0 migrations, 8 workflows active, zero deprecations, `v6Tshirt1` smoke test success.
  - **⚠️ n8n image is now PINNED to `n8nio/n8n:2.33.7`, no longer `:latest`.** Required, because `:latest` had already moved to 2.34.4 and a plain `compose up -d` would have silently jumped a minor version. Keep pinning — bump the tag deliberately on future upgrades. Backup: `docker-compose.yml.pre-2.33.7.bak`.
  - **No security fixes in any release** — an initial grep appeared to flag `rce` in all five, but those were substring hits on *"resource"* / *"force"*. Reading the actual notes showed bug fixes only.

  | Container | Before | After |
  |---|---|---|
  | n8n | 2.33.3 | **2.33.7** (pinned) |
  | dolibarr-db | MariaDB 10.11.16 | **10.11.18** |
  | 3dps-db | PostgreSQL 15.18 | 15.18 (Alpine base refresh — OS-level patches only) |
  | dolibarr-app | image 2026-04-04 | 2026-08-08 |
  | tailscale | 2026-05-01 | 2026-07-31 |
  | cloudflared ×2 | 2026-06-09 | 2026-07-23 |
  | nginx:alpine | 2026-05-22 | 2026-07-15 |
  | clamav | 2026-06-22 | 2026-08-10 |
  | autoheal | 2026-06-13 | 2026-08-11 |

  - **Safety taken first:** `pg_dumpall` (15 MB, 62 453 lines, completion marker verified) and `mysqldump --all-databases --single-transaction` (19 MB, 182 183 lines, clean trailer) *before* touching either DB; all 5 compose files and the n8n SQLite copied to `/volume1/docker/_preupdate_2026-08-07/`; every public image tagged `:rollback-20260807` (n8n as `:rollback-2.33.3`) so any container can be reverted by flipping one tag.
  - **Data verified intact after:** Postgres 25 tables / 47 MB unchanged; MariaDB 372 tables / 2 users unchanged; dolibarr HTTP 200; n8n healthz 200.
  - **Note for other projects:** recreating `3dps-nginx` also restarted `3dps-api` via compose's `depends_on` chain — expected, came back healthy and serving traffic. The mariadb root password env var is `MYSQL_ROOT_PASSWORD`, *not* `MARIADB_ROOT_PASSWORD` (the first dump attempt failed on this).
  - **Deferred by decision:** ~35 GB of reclaimable Docker garbage (245 dangling images + 19 GB build cache) left alone — disk is at 3 % of 7 TB, and pruning the build cache would slow 3dps's next image build.
  - **DSM 7.3.2** (build 86009, 2026-06-18) — update status unverified; `synoupgrade` needs an interactive sudo password. Check in the DSM UI.

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
