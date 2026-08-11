# IFB Shopify → Supplier Payouts

Self-hosted [n8n](https://n8n.io) automation that pulls monthly Shopify orders from `idealfoamblaster.myshopify.com`, matches them against per-supplier price references in Google Sheets, and writes a per-supplier monthly payout sheet — used to pay each supplier at the start of every month.

Runs on a Synology NAS in Docker (`n8nio/n8n:latest`).

## Architecture

```
[Cron 1st of month] → [Get Shopify Token] → [Fetch Orders (paginated)]
                                                  ↓
                              v4 (Gavin only)         v5 parent (multi-supplier)
                              ↓                       ↓
                              [Read Gavin Amt Ref]    [Read Suppliers Registry]
                              [Read Walkin]           [Filter Active=TRUE]
                              [Match + dedup]         [Execute Per-Supplier Sync]
                              [Append to Mar 2026 n8n] (calls v5 child once per supplier)
                                                            ↓
                              v5 child (per supplier):
                                [Pace API 15s] [Read Amount Reference]
                                [Read Walkin Source] [Create Month Tab]
                                [Read Existing Dest] [Match SKUs & Build Rows]
                                [Append Rows] [Apply Format + Tab Front (JWT batchUpdate)]
                                [Build & Append Run Log]
```

## Workflows

| File | Purpose |
|---|---|
| `n8n-workflow-shopify-monthly-sku-v4-import.json` | **v4** — Gavin's monthly payout sheet (retired post-convergence; kept as historical artifact). |
| `n8n-workflow-shopify-multi-supplier-parent-import.json` | **v5 parent** — Loads Suppliers Registry, fetches Shopify once, dispatches per-supplier child. Cron: `0 2 1 * *` SGT. |
| `n8n-workflow-shopify-per-supplier-child-import.json` | **v5 child** — Per-supplier pipeline: read Amount Ref + Walkin, match, append, format. Triggered via `Execute Workflow` from parent. |
| `n8n-workflow-shopify-tshirt-preorder-import.json` | **v6** — On-demand t-shirt pre-order extraction. Pulls last 60 days of orders matching `nerfsg-tshirt-custom-*`, writes the overwriting `Tshirt Pre-orders` tab for handover to the t-shirt printer. Manual trigger only. |
| `n8n-workflow-shopify-folder-grant-import.json` | **v7** — Auto-shares mapped Google Drive release folders (e.g. Mega Barrett SMC) to customers who buy a tagged SKU. Cron every 15 min + manual trigger. Uses the existing service account (dual scope: sheets + drive). Config lives on the internal sheet in `Folder Grants` / `Folder Grants Log` / `Folder Grants Cursor` tabs. |
| `n8n-workflow-error-handler.json` | Workflow-level failure catcher (wired as Error Workflow on v5 + v6 + v7). |

## Suppliers Registry

Each supplier is a row in a dedicated Google Sheet (`Registry` tab). Columns:

| Column | Example | Purpose |
|---|---|---|
| `supplier_name` | `Piggy` | Display name; used in dest tab name + run log |
| `supplier_code` | `piggy` | Short id (reserved) |
| `active` | `TRUE` | Only TRUE rows are processed |
| `amount_ref_sheet_id` | `1U_UC...` | Supplier's source Google Sheet ID |
| `amount_ref_tab_name` | `Piggy Amount Reference` | Tab name (verbatim — preserve trailing spaces if any) |
| `walkin_sheet_id` | (same as above for most) | Walkin source sheet |
| `walkin_tab_template` | `LLL yyyy` | Luxon format → derives tab name from `MONTH_NAME` |
| `walkin_format` | `standard-12` / `standard-11` / `ryan` / `vitae` | Column-mapping selector for Walkin source |
| `walkin_date_format` | `D LLL yyyy` | Luxon format used to parse dates in Walkin tab |
| `run_log_tab` | `Run Log Piggy` | Per-supplier run log inside the consolidated internal sheet |
| `title_hints` | `piggy,pgf,pf` | Comma-separated lowercase substrings; products matched by title get flagged TITLE MATCH |
| `exclude_skus` | `freebie-x,promo-y` | Comma-separated SKU exclusions (supports `*` wildcard) |

## Output

All v5 supplier tabs land in a **consolidated internal sheet** (the same one Gavin's v4 writes to). Naming: `MMM yyyy <Supplier> n8n` (e.g., `Mar 2026 Piggy n8n`). Each supplier also gets a `Run Log <Supplier>` tab with timestamp + counts per run.

Conditional formatting applied automatically inside the workflow (no post-run script needed):
- 🟧 Orange — non-numeric Order No. (Walkin / Cash IFB / blank)
- 🟨 Yellow — `TITLE MATCH` or `UNDERPRICED` in Remarks
- 🟥 Red — `REFUND` or `CURRENCY` in Remarks

New tabs auto-positioned to leftmost (`updateSheetProperties index=0`).

## Knowledge transfer rule

v4 and v5 share one canonical pipeline; only data sources differ. **Any fix to match/transform logic must be applied to both workflows in the same change set.** Per-supplier oddities (different tab format, date format, column layout) are expressed as Registry data, never as forked code. See [feedback_workflow_knowledge_transfer.md](https://github.com/changfrancis/ifb-shopify-supplier-payouts) (in the agent memory, not this repo).

## Deployment

Container: **`n8nio/n8n:2.33.7`** on Synology DSM Docker (upgraded 2026-08-07). Compose file (NAS-only, not in repo) sets:

> **The image tag is pinned deliberately — do not revert it to `:latest`.** `:latest` drifts across minor versions (it had already moved to 2.34.4), so a routine `compose up -d` would silently jump versions. Bump the pinned tag as an explicit decision, and smoke-test afterwards.


- `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`
- `NODE_FUNCTION_ALLOW_BUILTIN=fs,crypto,https,http,path,buffer`
- `NODE_FUNCTION_ALLOW_EXTERNAL=luxon`
- `N8N_RUNNERS_TASK_RUNNER_NODE_FUNCTION_ALLOW_BUILTIN` / `..._ALLOW_EXTERNAL` — same values; required since the JS Task Runner became the default in 2.22.5+
- `N8N_RUNNERS_TASK_TIMEOUT=300` — **pinned deliberately.** n8n will lower this default to 60s in a future version, but `v5ParentMulti1` runs ~348s and `v5ChildPerSup1` ~151s; 60s would break the monthly cron.
- `N8N_COMPRESSION_NODE_MAX_DECOMPRESSED_SIZE_BYTES=268435456`, `N8N_COMPRESSION_NODE_MAX_ZIP_ENTRIES=1000`, `N8N_UNVERIFIED_PACKAGES_ENABLED=false` — pre-adopted future defaults. Safe: no workflow uses compression/zip nodes, and every node is official `n8n-nodes-base.*`.
- Mounts SA JSON at `/files/sa.json` for in-workflow JWT signing

### Running a workflow from the CLI

Use the helper on the NAS — **no container restart, no downtime**:

```bash
/volume1/docker/n8n/n8n-run.sh                  # no args -> usage + workflow list
/volume1/docker/n8n/n8n-run.sh v6Tshirt1        # execute by ID

# Supplier re-run with a month override. Extra args pass through to docker exec;
# quote any value containing a space.
/volume1/docker/n8n/n8n-run.sh v5ParentMulti1 \
  -e "OVERRIDE_MONTH_NAME=Jul 2026" \
  -e "OVERRIDE_MONTH_NAME_YY=Jul 26" \
  -e OVERRIDE_MONTH_START_ISO=2026-07-01T00:00:00.000+08:00 \
  -e OVERRIDE_MONTH_END_ISO=2026-07-31T23:59:59.999+08:00
```

The non-obvious bit it handles: `n8n execute` boots a full instance and collides on the **Task Broker port 5679** — *not* 5678. The helper remaps both ports so the one-shot run coexists with production. This supersedes the old stop-container → `docker run --rm` → restart procedure.

Quote each `-e` value that contains a space. An earlier version took the overrides through a single `OVERRIDE="..."` variable, which word-split `Jul 2026` and made docker read `2026` as a container name.

### Rebuilding a past month after a supplier updates their Amount Reference

The workflow only **appends** — it never rewrites existing rows. To pick up new SKUs or corrected prices for a month that already ran:

1. **Back up the dest tab** and confirm `Payment Complete` / `Date of Payment` are empty (a rebuild discards anything hand-entered there). `Gdrive access` and Fedex `Remarks` on Walkin rows are safe — they re-import from the supplier's Walkin source tab.
2. Set the target supplier `active=TRUE` in the Registry and everyone else `FALSE`.
3. **Delete the dest tab** so the workflow recreates it from scratch.
4. Run `n8n-run.sh v5ParentMulti1` with the four `OVERRIDE_MONTH_*` args for that month.
5. **Restore all suppliers to `active=TRUE`.**
6. Verify, and **cross-check manual/Walkin rows**: if the dest has fewer non-numeric-OrderNo rows than the source month tab, something silently mismatched (tab name, date format, `walkin_format`).

`.env` on NAS holds: `SHOPIFY_SHOP`, `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `N8N_BASIC_AUTH_PASSWORD`.

## Helper scripts

- `n8n-run.sh` — execute any workflow from the CLI with zero downtime (see above). Deployed to `/volume1/docker/n8n/n8n-run.sh` on the NAS; versioned here so it survives a rebuild.
- `apply_conditional_formatting.py` — manual fallback for applying conditional formatting + tab-to-front. Now redundant (built into v5 child), kept for debugging.
- `archive/` — earlier iterations (v1/v2/v3) and ad-hoc debug scripts kept for history.

## Bugs found in development

1. **Sheets node `row_number` prefix** — `Object.values(r)[0]` reads row number, not column A. Fixed: read by header name.
2. **Sandbox blocks `luxon` / `fs` / `crypto`** — even with `N8N_RUNNERS_ENABLED=false`. Fixed: `NODE_FUNCTION_ALLOW_*` env vars.
3. **Sheets API rate limit (60 reads/min/user)** — multi-supplier burst exhausted quota. Fixed: 15s pace at start of each child + retry-with-backoff in JWT format Code.
4. **`{__empty: true}` fallback row appended** to a freshly-created tab when 0 rows matched. Fixed: emit `[]` and rely on `alwaysOutputData: true` on downstream.

## Related

- Agent plan: `~/.claude/plans/n8n-shopify-linear-koala.md`
- Service account: `n8n-sheets@ifb-n8n-integration.iam.gserviceaccount.com`
