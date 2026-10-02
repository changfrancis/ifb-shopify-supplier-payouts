#!/usr/bin/env python3
"""Build per-supplier exclude_skus candidates from evidence, into two tabs of the
internal sheet: 'Exclude Paste' (one paste-ready line per supplier) and
'Exclude Detail' (every candidate with its reason).

Replays every Shopify order since 1 Mar 2026 through the CURRENT matcher (current
references, hints and excludes), so anything already excluded or already priced
does not appear. Each remaining title-hint match is classified:

  EXCLUDE           in another supplier's reference, or matched ONLY on an order
                    note/tags, or its Shopify vendor is not one this supplier sells
  ADD TO REFERENCE  vendor is one this supplier sells -> probably theirs, unpriced
  CHECK             no vendor and no other evidence -> human call

"Vendors this supplier sells" = vendors seen on their reference-matched sales in
the same window (empirical, not assumed).
Usage: exclude_candidates.py [--apply]     (dry run prints; --apply writes the tabs)
"""
import json, time, base64, subprocess, tempfile, os, re, socket, sys
from urllib import request, parse, error

socket.setdefaulttimeout(60)
SA = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
REG = "1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs"
DEST = "1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM"
START = "2026-03-01T00:00:00+08:00"
BSL = chr(92)
APPLY = "--apply" in sys.argv
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

sa = json.load(open(SA))
b = lambda x: base64.urlsafe_b64encode(x).rstrip(b"=").decode()
now = int(time.time())
si = b(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode()) + "." + \
     b(json.dumps({"iss": sa["client_email"], "scope": "https://www.googleapis.com/auth/spreadsheets",
                   "aud": "https://oauth2.googleapis.com/token", "exp": now + 3600, "iat": now},
                  separators=(",", ":")).encode())
fd, kp = tempfile.mkstemp(prefix="sa_")
os.write(fd, sa["private_key"].encode()); os.close(fd)
sg = subprocess.run(["openssl", "dgst", "-binary", "-sha256", "-sign", kp],
                    input=si.encode(), capture_output=True, check=True).stdout
os.unlink(kp)
H = {"Authorization": "Bearer " + json.load(request.urlopen(request.Request(
    "https://oauth2.googleapis.com/token",
    data=parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                          "assertion": si + "." + b(sg)}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"})))["access_token"]}
HJ = {**H, "Content-Type": "application/json"}


def req(sid, path, data=None, method="GET"):
    url = "https://sheets.googleapis.com/v4/spreadsheets/" + sid + path
    d = 2
    for a in range(7):
        try:
            r = json.load(request.urlopen(request.Request(url, data=data, method=method,
                                                          headers=HJ if data else H), timeout=60))
            time.sleep(1.0)
            return r
        except error.HTTPError as e:
            if e.code in (429, 500, 503) and a < 6:
                time.sleep(d); d = min(d * 2, 60); continue
            raise


# ---------- shopify ----------
env = {}
for line in open("/volume1/docker/n8n/.env"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
SHOP = env["SHOPIFY_SHOP"]
tok = json.load(request.urlopen(request.Request(
    "https://%s.myshopify.com/admin/oauth/access_token" % SHOP,
    data=parse.urlencode({"grant_type": "client_credentials", "client_id": env["SHOPIFY_CLIENT_ID"],
                          "client_secret": env["SHOPIFY_CLIENT_SECRET"]}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"})))["access_token"]
orders = []
url = ("https://%s.myshopify.com/admin/api/2026-04/orders.json?status=any&limit=250&created_at_min=%s"
       % (SHOP, parse.quote(START)))
while url:
    r = request.urlopen(request.Request(url, headers={"X-Shopify-Access-Token": tok}))
    orders += json.load(r).get("orders", [])
    m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link") or "")
    url = m.group(1) if m else None
print("orders since %s: %d" % (START[:10], len(orders)))

# ---------- matcher pieces (mirror the v5 child) ----------
SPECIAL = set(".+?^${}()|[]" + BSL)


def esc(s):
    return "".join((BSL + ch) if ch in SPECIAL else ch for ch in s)


def master_re(sku):
    p = esc(sku).replace("COLOUR", ".+").replace("XXX", ".+")
    return re.compile("^" + re.sub("[-_]", "[-_]", p) + "$", re.I)


def excl_re(p):
    return re.compile("^" + esc(p).replace(BSL + "*", ".*") + "$", re.I)


SHIP_WORDS = ["lalamove", "grab" + BSL + "s*express", "gogovan", "ninja" + BSL + "s*?van",
              "j&t", "qxpress", "singpost", "fedex", "dhl", "courier", "postage",
              "freight", "shipping", "delivery" + BSL + "s*(fee|charge)"]
SHIPPING = re.compile("(" + "|".join(SHIP_WORDS) + ")", re.I)
PRODUCT = {"title", "variant", "name", "vendor", "props"}


def month_of(iso):
    # created_at carries +08:00 for this store; month in SGT
    return "%s %s" % (MON[int(iso[5:7]) - 1], iso[:4])


reg = req(REG, "/values/Registry!A:M").get("values", [])
ci = {h.strip().lower(): i for i, h in enumerate(reg[0])}


def g(r, k):
    i = ci.get(k)
    return r[i] if i is not None and i < len(r) else ""


sups = []
for r in reg[1:]:
    nm = g(r, "supplier_name")
    if not nm or g(r, "active").strip().upper() != "TRUE":
        continue
    ref = req(g(r, "amount_ref_sheet_id"), "/values/" + parse.quote(g(r, "amount_ref_tab_name") + "!A:A")).get("values", [])
    masters = [master_re(str(x[0]).strip()) for x in ref[1:]
               if x and str(x[0]).strip() and str(x[0]).strip().lower() != "sku"]
    exs = [x.strip() for x in g(r, "exclude_skus").split(",") if x.strip()]
    sups.append({"name": nm, "masters": masters, "excl_raw": exs, "excl": [excl_re(x) for x in exs],
                 "hints": [h.strip().lower() for h in g(r, "title_hints").split(",") if h.strip()]})
by = {s["name"]: s for s in sups}

# ---------- pass 1: which vendors does each supplier actually sell (ref-matched sales) ----------
own = {s["name"]: {} for s in sups}
for o in orders:
    for li in o.get("line_items", []):
        sku = li.get("sku") or ""
        v = (li.get("vendor") or "").strip()
        if not sku or not v:
            continue
        for s in sups:
            if any(rx.match(sku) for rx in s["masters"]):
                own[s["name"]][v] = own[s["name"]].get(v, 0) + (li.get("quantity") or 1)

# all-sales volume per vendor: a vendor is only "theirs" if this supplier's
# reference sales are at least half of EVERYTHING sold under that vendor
vtotal = {}
for o in orders:
    for li in o.get("line_items", []):
        v = (li.get("vendor") or "").strip()
        if v:
            vtotal[v] = vtotal.get(v, 0) + (li.get("quantity") or 1)

# ---------- pass 2: every title-hint match under the current config ----------
cand = {}   # (supplier, key) -> info
for o in orders:
    for li in o.get("line_items", []):
        key = li.get("sku") or li.get("title") or li.get("name") or ""
        for s in sups:
            if any(rx.match(key) for rx in s["excl"]):
                continue
            if li.get("sku") and any(rx.match(li["sku"]) for rx in s["masters"]):
                continue
            if SHIPPING.search(" ".join([li.get("sku") or "", li.get("title") or "", li.get("name") or ""])):
                continue
            props = [p for p in (li.get("properties") or [])
                     if not re.search("email|phone|address|contact|name", str(p.get("name") or "").lower())
                     and "@" not in str(p.get("value") or "")]
            fields = [("title", li.get("title") or ""), ("variant", li.get("variant_title") or ""),
                      ("name", li.get("name") or ""), ("vendor", li.get("vendor") or ""),
                      ("props", " ".join((str(p.get("name") or "") + " " + str(p.get("value") or "")) for p in props)),
                      ("note", o.get("note") or ""), ("tags", o.get("tags") or "")]
            fired = [(f, [h for h in s["hints"] if h in str(v).lower()]) for f, v in fields]
            fired = [(f, h) for f, h in fired if h]
            if not fired:
                continue
            q = li.get("quantity") or 1
            c = cand.setdefault((s["name"], key), {"units": 0, "amt": 0.0, "months": set(), "orders": [],
                                                   "vendors": set(), "why": set(), "weak_all": True,
                                                   "title": li.get("title") or ""})
            c["units"] += q
            c["amt"] += float(li.get("price") or 0) * q
            c["months"].add(month_of(o["created_at"]))
            if len(c["orders"]) < 4 and o["order_number"] not in c["orders"]:
                c["orders"].append(o["order_number"])
            if (li.get("vendor") or "").strip():
                c["vendors"].add(li["vendor"].strip())
            c["why"].add(" ".join("%s:%s" % (f, ",".join(h)) for f, h in fired))
            if any(f in PRODUCT for f, _ in fired):
                c["weak_all"] = False

# ---------- classify ----------
rows = []
for (sup, key), c in cand.items():
    others = [s["name"] for s in sups if s["name"] != sup and any(rx.match(key) for rx in s["masters"])]
    vend = sorted(c["vendors"])
    excl_v = [v for v in vend if v.upper() != "IFB.SG" and own[sup].get(v, 0)
              and own[sup][v] >= 0.8 * sum(own[n].get(v, 0) for n in own)
              and own[sup][v] >= 0.5 * vtotal.get(v, 0)]
    shared_v = [v for v in vend if v not in excl_v and (v.upper() == "IFB.SG" or own[sup].get(v, 0))]
    foreign_owner = sorted({n for v in vend for n, vs in own.items() if n != sup and v in vs})
    named = sup.lower() in (c["title"] or key).lower()
    if others:
        sug, why = "EXCLUDE", "In %s's Amount Reference" % "/".join(others)
    elif excl_v:
        sug, why = "ADD TO REFERENCE", "Vendor %s: most of its sales are %s's referenced SKUs - probably theirs, just unpriced" % ("/".join(excl_v), sup)
    elif named:
        sug, why = "CHECK", "Title names %s - may well be theirs" % sup
    elif c["weak_all"]:
        sug, why = "EXCLUDE", "Matched only on order note/tags, never on the product"
    elif shared_v:
        sug, why = "CHECK", "Vendor %s is shared across suppliers (IFB.SG is the house brand) - judge from the title" % "/".join(shared_v)
    elif vend:
        why = "Vendor %s is not one %s sells" % ("/".join(vend), sup)
        if foreign_owner:
            why += " (sold via %s)" % "/".join(foreign_owner)
        sug = "EXCLUDE"
    else:
        sug, why = "CHECK", "No Shopify vendor - judge from the title"
    paste = key
    note = ""
    if "," in key:
        paste = key.split(",")[0].rstrip() + "*"
        note = "contains a comma; exclude list is comma-separated, so use the wildcard form"
    rows.append({"sup": sup, "sug": sug, "key": key, "paste": paste, "why": why, "vendor": "/".join(vend) or "(none)",
                 "matched": " | ".join(sorted(c["why"]))[:180], "units": c["units"], "amt": round(c["amt"], 2),
                 "months": ", ".join(sorted(c["months"], key=lambda m: (m[-4:], MON.index(m[:3])))),
                 "orders": ", ".join(str(x) for x in c["orders"]), "note": note})

ORDER = {"EXCLUDE": 0, "CHECK": 1, "ADD TO REFERENCE": 2}
rows.sort(key=lambda r: ([s["name"] for s in sups].index(r["sup"]), ORDER[r["sug"]], -r["amt"]))

# ---------- report ----------
print()
print("%-9s %-17s %5s %10s  %-44s %s" % ("supplier", "suggestion", "units", "$", "sku / title", "reason"))
for r in rows:
    print("%-9s %-17s %5d %10s  %-44s %s" % (r["sup"], r["sug"], r["units"], format(r["amt"], ",.2f"), r["key"][:44], r["why"][:70]))
print()
summ = []
for s in sups:
    ex = [r for r in rows if r["sup"] == s["name"] and r["sug"] == "EXCLUDE"]
    ck = [r for r in rows if r["sup"] == s["name"] and r["sug"] == "CHECK"]
    ad = [r for r in rows if r["sup"] == s["name"] and r["sug"] == "ADD TO REFERENCE"]
    adds = []
    for r in ex:
        if r["paste"].lower() not in {x.lower() for x in s["excl_raw"]} and r["paste"] not in adds:
            adds.append(r["paste"])
    summ.append([s["name"], len(ex), round(sum(r["amt"] for r in ex), 2), len(ck), len(ad),
                 len(s["excl_raw"]), ",".join(adds), ",".join(s["excl_raw"] + adds)])
    print("%-9s exclude=%-3d ($%9s)  check=%-3d  add-to-ref=%-3d  current excludes=%d"
          % (s["name"], len(ex), format(sum(r["amt"] for r in ex), ",.2f"), len(ck), len(ad), len(s["excl_raw"])))

if not APPLY:
    print()
    print("DRY RUN - re-run with --apply to write the two tabs")
    sys.exit(0)

# ---------- write tabs ----------
meta = req(DEST, "?fields=sheets.properties")
ids = {x["properties"]["title"]: x["properties"]["sheetId"] for x in meta["sheets"]}
reqs = []
for t in ("Exclude Paste", "Exclude Detail"):
    if t in ids:
        reqs.append({"deleteSheet": {"sheetId": ids[t]}})
reqs += [{"addSheet": {"properties": {"title": "Exclude Paste", "index": 0, "gridProperties": {"frozenRowCount": 3}}}},
         {"addSheet": {"properties": {"title": "Exclude Detail", "index": 1, "gridProperties": {"frozenRowCount": 1}}}}]
res = req(DEST, ":batchUpdate", data=json.dumps({"requests": reqs}).encode(), method="POST")
new = {r["addSheet"]["properties"]["title"]: r["addSheet"]["properties"]["sheetId"] for r in res["replies"] if "addSheet" in r}

stamp = time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time() + 8 * 3600))
paste_vals = [["Exclude SKU candidates per supplier - generated %s SGT from %d Shopify orders since 1 Mar 2026, replayed through the CURRENT registry. Review 'Exclude Detail' first; copy column H into the supplier's exclude_skus cell (Suppliers Registry, column L) to accept all suggestions." % (stamp, len(orders))],
              [],
              ["Supplier", "Suggested EXCLUDE (count)", "$ credited by those (Mar-Oct)", "CHECK (count)", "ADD TO REFERENCE (count)",
               "Current exclude count", "New SKUs to add (comma-separated)", "FULL exclude_skus value = current + suggested (paste into Registry col L)"]]
paste_vals += summ
detail_vals = [["Supplier", "Suggestion", "SKU (or title when no SKU)", "Exclude string to use", "Reason", "Shopify vendor",
                "Matched on (field:hint)", "Units", "$ credited", "Months", "Example orders", "Note"]]
for r in rows:
    detail_vals.append([r["sup"], r["sug"], r["key"], r["paste"] if r["sug"] == "EXCLUDE" else "", r["why"], r["vendor"],
                        r["matched"], r["units"], r["amt"], r["months"], r["orders"], r["note"]])
req(DEST, "/values:batchUpdate", data=json.dumps({"valueInputOption": "RAW", "data": [
    {"range": "'Exclude Paste'!A1", "values": paste_vals},
    {"range": "'Exclude Detail'!A1", "values": detail_vals}]}).encode(), method="POST")

P, D = new["Exclude Paste"], new["Exclude Detail"]
GREY = {"red": 0.85, "green": 0.85, "blue": 0.85}
fmt = [
    {"repeatCell": {"range": {"sheetId": P, "startRowIndex": 2, "endRowIndex": 3},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": GREY, "wrapStrategy": "WRAP"}},
                    "fields": "userEnteredFormat(textFormat,backgroundColor,wrapStrategy)"}},
    {"repeatCell": {"range": {"sheetId": P, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"italic": True}}}, "fields": "userEnteredFormat.textFormat"}},
    {"repeatCell": {"range": {"sheetId": P, "startRowIndex": 3, "startColumnIndex": 6, "endColumnIndex": 8},
                    "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
                    "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": P, "startRowIndex": 3, "startColumnIndex": 2, "endColumnIndex": 3},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}},
                    "fields": "userEnteredFormat.numberFormat"}},
    {"updateDimensionProperties": {"range": {"sheetId": P, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 6},
                                   "properties": {"pixelSize": 120}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": P, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 8},
                                   "properties": {"pixelSize": 420}, "fields": "pixelSize"}},
    {"repeatCell": {"range": {"sheetId": D, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": GREY}},
                    "fields": "userEnteredFormat(textFormat,backgroundColor)"}},
    {"repeatCell": {"range": {"sheetId": D, "startRowIndex": 1, "startColumnIndex": 8, "endColumnIndex": 9},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}},
                    "fields": "userEnteredFormat.numberFormat"}},
    {"setBasicFilter": {"filter": {"range": {"sheetId": D, "startRowIndex": 0, "endRowIndex": len(detail_vals),
                                             "startColumnIndex": 0, "endColumnIndex": 12}}}},
    {"autoResizeDimensions": {"dimensions": {"sheetId": D, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 12}}},
]
for text, col in (("EXCLUDE", {"red": 0.96, "green": 0.80, "blue": 0.80}),
                  ("CHECK", {"red": 1.0, "green": 0.95, "blue": 0.70}),
                  ("ADD TO REFERENCE", {"red": 0.80, "green": 0.92, "blue": 0.80})):
    fmt.append({"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [{"sheetId": D, "startRowIndex": 1, "endRowIndex": len(detail_vals), "startColumnIndex": 0, "endColumnIndex": 12}],
        "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=$B2="%s"' % text}]},
                        "format": {"backgroundColor": col}}}}})
req(DEST, ":batchUpdate", data=json.dumps({"requests": fmt}).encode(), method="POST")
print()
print("WROTE  Exclude Paste  gid=%d  (%d suppliers)" % (P, len(summ)))
print("WROTE  Exclude Detail gid=%d  (%d candidates)" % (D, len(rows)))
