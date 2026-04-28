# Status — paused 2026-04-29

## Where we are

End-to-end pipeline is **deployed and active** on the Synology n8n container:

- v4 (Gavin) — patched + active, cron `0 1 1 * *` SGT
- v5 parent + child — active, cron `0 2 1 * *` SGT
- Error handler — active
- Suppliers Registry seeded with 6 first-wave rows (all `active=TRUE`)
- Multi-supplier dry run completed; all 6 produced their `Mar 2026 <Supplier> n8n` tab + per-supplier `Run Log <Supplier>` tab in the consolidated internal sheet

## Resume here

User flagged: "i noticed mistake, will correct with you one supplier at a time" — paused before identifying the first supplier issue.

When resuming, expect a per-supplier correction request. The fix likely lands in one of these places:

| Issue type | Fix location |
|---|---|
| Wrong tab name / wrong sheet ID / wrong format | Suppliers Registry sheet (`1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs`) |
| Missing SKU in Amount Reference | Supplier's own source sheet (the one they edit) |
| Match logic bug (affects all suppliers) | `n8n-workflow-shopify-per-supplier-child-import.json` Match SKUs Code node — **and apply same change to v4** per knowledge-transfer rule |
| Output format / column / sort order | Same Match SKUs Code node |
| Title hints too broad / narrow | Suppliers Registry `title_hints` column |
| Conditional formatting rule | `Apply Format + Tab Front` Code node in child |

After any code fix:
1. Edit local JSON
2. `scp -O` to NAS `/volume1/docker/n8n/`
3. `docker cp` into container
4. `n8n import:workflow --input=...`
5. `n8n update:workflow --id=<id> --active=true`
6. `docker restart n8n` to pick up activation
7. Test via `docker stop n8n` → `docker run --rm --entrypoint n8n …` → `docker start n8n`
8. Read execution data via `python3 /tmp/dump_exec.py <id> "<NodeName>"` on NAS for debugging

## Per-supplier dry-run summary (Mar 2026 data)

| Supplier | Rows in dest | TITLE MATCH | Notes for review |
|---|---|---|---|
| Piggy | 22 | 2 | `swampfox-raider-prism-optic` flagged — confirm if Piggy product or false positive |
| Stan | 8 | 7 | High title-match ratio — Stinger SKUs probably need to be added to `Stinger Amount Reference` |
| Bluebird | 1 | 1 | Only 1 match in March — confirm correct, or expand `title_hints` beyond `bbsg,bluebird,gel` |
| Ryan | 246 | 129 | Many Blu-barrel SKUs flagged — likely missing from `Ryan Amount Reference` |
| Bryan | 0 (deleted) | — | After narrowing hints to `stk,bryan`, will regenerate clean on next cron |
| Dylan | 14 | 8 | Dylan SKUs not in `AI Dylan Amount Reference` — review TITLE MATCH list |

## Open items unrelated to corrections

- v4 parity test: manually trigger v4 via n8n UI → confirm Mar 2026 + Apr 2026 output unchanged after Amount Ref source flip (or wait for May 1 cron, which will be the natural validation)
- Vitae onboarding deferred until Linford adds an Amount Reference tab
- Carryover from v4 era: confirm `d2-sbl1-deskmat-3060` SKU dash convention
- Carryover: rotate `changfrancis` DSM password (was leaked in chat earlier)

## File anchors

- Plan file (not in repo): `~/.claude/plans/n8n-shopify-linear-koala.md`
- Suppliers Registry: https://docs.google.com/spreadsheets/d/1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs/edit
- Internal sheet (output): https://docs.google.com/spreadsheets/d/1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM/edit
- Service account: `n8n-sheets@ifb-n8n-integration.iam.gserviceaccount.com`
