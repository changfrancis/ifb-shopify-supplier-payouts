#!/usr/bin/env python3
"""Verify a month's generated supplier tabs against an independent replay.

Usage (on the NAS, read-only):  python3 verify_month_output.py "Sep 2026"

1. Per-supplier rows / takehome / flags, stray NO SALE placeholders.
2. Every Shopify row's Date vs the order's real SGD date (TZ regression check).
3. Every Shopify row's order actually falls in the month.
4. Independent replay of the matcher over ALL Sep orders: compare the multiset
   of (order, sku) units with what the workflow wrote -- missing / extra.
5. Spot checks: courier lines absent, Ryan's silver Aerial present, WEAK labels.
6. Manual/Walkin rows: source tab vs dest (memory rule).
7. Run Log: latest entry per supplier.
"""
import json, time, base64, subprocess, tempfile, os, re, socket
from datetime import datetime, timedelta
from urllib import request, parse, error

socket.setdefaulttimeout(60)
SA = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
DEST = "1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM"
REG = "1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs"
import sys
M = sys.argv[1] if len(sys.argv) > 1 else "Sep 2026"
import calendar
MON_FULL = ["January", "February", "March", "April", "May", "June", "July", "August",
            "September", "October", "November", "December"]
_mi = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(M.split()[0])
_yr = int(M.split()[1])
M_START = "%d-%02d-01T00:00:00+08:00" % (_yr, _mi + 1)
M_END = "%d-%02d-%02dT23:59:59+08:00" % (_yr, _mi + 1, calendar.monthrange(_yr, _mi + 1)[1])
BSL = chr(92)
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

sa = json.load(open(SA))
b = lambda x: base64.urlsafe_b64encode(x).rstrip(b"=").decode()
now = int(time.time())
si = b(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode()) + "." + \
     b(json.dumps({"iss": sa["client_email"],
                   "scope": "https://www.googleapis.com/auth/spreadsheets.readonly",
                   "aud": "https://oauth2.googleapis.com/token",
                   "exp": now + 3600, "iat": now}, separators=(",", ":")).encode())
fd, kp = tempfile.mkstemp(prefix="sa_")
os.write(fd, sa["private_key"].encode()); os.close(fd)
sg = subprocess.run(["openssl", "dgst", "-binary", "-sha256", "-sign", kp],
                    input=si.encode(), capture_output=True, check=True).stdout
os.unlink(kp)
GH = {"Authorization": "Bearer " + json.load(request.urlopen(request.Request(
    "https://oauth2.googleapis.com/token",
    data=parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                          "assertion": si + "." + b(sg)}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"})))["access_token"]}


def vals(sid, rng):
    d = 2
    for a in range(7):
        try:
            r = json.load(request.urlopen(request.Request(
                "https://sheets.googleapis.com/v4/spreadsheets/" + sid + "/values/" + parse.quote(rng),
                headers=GH), timeout=60)).get("values", [])
            time.sleep(1.1)
            return r
        except error.HTTPError as e:
            if e.code in (429, 500, 503) and a < 6:
                time.sleep(d); d = min(d * 2, 60); continue
            return None


def tabs(sid):
    try:
        return [s["properties"]["title"] for s in json.load(request.urlopen(request.Request(
            "https://sheets.googleapis.com/v4/spreadsheets/" + sid + "?fields=sheets.properties.title",
            headers=GH), timeout=60))["sheets"]]
    except Exception:
        return []


env = {}
for line in open("/volume1/docker/n8n/.env"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
SHOP = env["SHOPIFY_SHOP"]
stok = json.load(request.urlopen(request.Request(
    "https://%s.myshopify.com/admin/oauth/access_token" % SHOP,
    data=parse.urlencode({"grant_type": "client_credentials",
                          "client_id": env["SHOPIFY_CLIENT_ID"],
                          "client_secret": env["SHOPIFY_CLIENT_SECRET"]}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"})))["access_token"]
SH = {"X-Shopify-Access-Token": stok}
orders = []
url = ("https://%s.myshopify.com/admin/api/2026-04/orders.json?status=any&limit=250"
       "&created_at_min=%s&created_at_max=%s" % (SHOP, parse.quote(M_START),
                                                  parse.quote(M_END)))
while url:
    r = request.urlopen(request.Request(url, headers=SH))
    orders += json.load(r).get("orders", [])
    m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link") or "")
    url = m.group(1) if m else None
by_no = {str(o.get("order_number")): o for o in orders}


def sgt_date(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = dt.astimezone().__class__  # noqa
    u = dt - dt.utcoffset() if dt.utcoffset() else dt
    s = u.replace(tzinfo=None) + timedelta(hours=8)
    return "%d %s %d" % (s.day, MON[s.month - 1], s.year)


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


def money(s):
    m = re.search("-?[0-9,]+[.]?[0-9]*", str(s).replace("$", ""))
    return float(m.group().replace(",", "")) if m else 0.0


def tpl(t):
    t = t or "LLL yyyy"
    return t.replace("LLLL", MON_FULL[_mi]).replace("LLL", M.split()[0]).replace("yyyy", str(_yr)).replace("yy", str(_yr)[2:])


reg = vals(REG, "Registry!A:M")
ci = {h.strip().lower(): i for i, h in enumerate(reg[0])}


def g(r, k):
    i = ci.get(k)
    return r[i] if i is not None and i < len(r) else ""


sups = []
for r in reg[1:]:
    nm = g(r, "supplier_name")
    if not nm or g(r, "active").strip().upper() != "TRUE":
        continue
    ref = vals(g(r, "amount_ref_sheet_id"), g(r, "amount_ref_tab_name") + "!A:D") or []
    masters = [master_re(str(x[0]).strip()) for x in ref[1:]
               if x and str(x[0]).strip() and str(x[0]).strip().lower() != "sku"]
    sups.append({"name": nm, "masters": masters,
                 "hints": [h.strip().lower() for h in g(r, "title_hints").split(",") if h.strip()],
                 "excl": [excl_re(x.strip()) for x in g(r, "exclude_skus").split(",") if x.strip()],
                 "wsid": g(r, "walkin_sheet_id"), "wtab": tpl(g(r, "walkin_tab_template")),
                 "runlog": g(r, "run_log_tab")})


def replay(s):
    """(order, sku) -> unit count that the v5 child should write for this supplier."""
    out = {}
    for o in orders:
        for li in o.get("line_items", []):
            skuchk = li.get("sku") or li.get("title") or li.get("name") or ""
            if any(rx.match(skuchk) for rx in s["excl"]):
                continue
            hit = bool(li.get("sku")) and any(rx.match(li["sku"]) for rx in s["masters"])
            if not hit:
                if SHIPPING.search(" ".join([li.get("sku") or "", li.get("title") or "", li.get("name") or ""])):
                    continue
                props = [p for p in (li.get("properties") or [])
                         if not re.search("email|phone|address|contact|name", str(p.get("name") or "").lower())
                         and "@" not in str(p.get("value") or "")]
                hay = " ".join([li.get("title") or "", li.get("variant_title") or "", li.get("name") or "",
                                li.get("vendor") or "",
                                " ".join((str(p.get("name") or "") + " " + str(p.get("value") or "")) for p in props),
                                o.get("note") or "", o.get("tags") or ""]).lower()
                if not any(h in hay for h in s["hints"]):
                    continue
            k = (str(o.get("order_number")), skuchk)
            out[k] = out.get(k, 0) + (li.get("quantity") or 1)
    return out


print("%s Shopify orders: %d" % (M, len(orders)))
dest_tabs = set(tabs(DEST))
print()
print("=" * 112)
print("1) OUTPUT PER SUPPLIER".center(112))
print("=" * 112)
print("%-9s %5s %12s  %-46s %s" % ("supplier", "rows", "takehome", "flags", "checks"))
issues = []
grand_r = 0
grand_t = 0.0
detail = {}
for s in sups:
    tab = M + " " + s["name"] + " n8n"
    if tab not in dest_tabs:
        print("%-9s  *** TAB MISSING ***" % s["name"])
        issues.append("%s: tab missing" % s["name"])
        continue
    rows = vals(DEST, tab + "!A:L") or []
    body = rows[1:]
    tot = sum(money(r[8] if len(r) > 8 else "") for r in body)
    grand_r += len(body)
    grand_t += tot
    fl = {}
    nosale = 0
    for r in body:
        rem = str(r[11] if len(r) > 11 else "")
        if (r[5] if len(r) > 5 else "") == "NO SALE THIS MONTH":
            nosale += 1
        for k in ("TITLE MATCH WEAK", "TITLE MATCH", "REFUND", "CANCELLED", "UNDERPRICED", "MANUAL ENTRY", "CURRENCY"):
            if k in rem:
                fl[k] = fl.get(k, 0) + 1
                break
    # date + month checks on Shopify rows
    bad_date = []
    out_month = []
    actual = {}
    for r in body:
        on = (r[0] if r else "").strip()
        if not on.isdigit():
            continue
        sku = (r[5] if len(r) > 5 else "").strip()
        actual[(on, sku)] = actual.get((on, sku), 0) + 1
        o = by_no.get(on)
        if not o:
            out_month.append(on)
            continue
        want = sgt_date(o["created_at"])
        if (r[1] if len(r) > 1 else "").strip() != want:
            bad_date.append((on, r[1] if len(r) > 1 else "", want))
    exp = replay(s)
    missing = {k: v - actual.get(k, 0) for k, v in exp.items() if v > actual.get(k, 0)}
    extra = {k: v - exp.get(k, 0) for k, v in actual.items() if v > exp.get(k, 0)}
    checks = []
    checks.append("dates %d/%d ok" % (sum(actual.values()) - len(bad_date), sum(actual.values())))
    if out_month:
        checks.append("%d NOT IN MONTH" % len(out_month))
    if missing or extra:
        checks.append("replay: %d missing, %d extra" % (sum(missing.values()), sum(extra.values())))
    else:
        checks.append("replay matches")
    if nosale and len(body) > nosale:
        checks.append("%d STRAY NO SALE" % nosale)
    print("%-9s %5d %12s  %-46s %s" % (s["name"], len(body), "$%.2f" % tot,
                                       ", ".join("%s=%d" % kv for kv in sorted(fl.items())) or "clean",
                                       "; ".join(checks)))
    detail[s["name"]] = {"body": body, "bad_date": bad_date, "out": out_month, "missing": missing, "extra": extra}
    if bad_date: issues.append("%s: %d wrong dates" % (s["name"], len(bad_date)))
    if out_month: issues.append("%s: %d rows from orders outside Sep" % (s["name"], len(out_month)))
    if missing or extra: issues.append("%s: replay mismatch" % s["name"])
    if nosale and len(body) > nosale: issues.append("%s: stray NO SALE" % s["name"])
print("-" * 112)
print("%-9s %5d %12s" % ("TOTAL", grand_r, "$%.2f" % grand_t))

print()
print("=" * 112)
print("2) DISCREPANCIES".center(112))
print("=" * 112)
anyd = False
for n, d in detail.items():
    for on, got, want in d["bad_date"][:10]:
        anyd = True
        print("  %-9s DATE   order %s: sheet %r, Shopify SGT %r" % (n, on, got, want))
    for on in d["out"][:10]:
        anyd = True
        print("  %-9s MONTH  order %s is not a %s order" % (n, on, M))
    for (on, sku), c in list(d["missing"].items())[:15]:
        anyd = True
        print("  %-9s MISSING %dx order %s %s" % (n, c, on, sku[:50]))
    for (on, sku), c in list(d["extra"].items())[:15]:
        anyd = True
        print("  %-9s EXTRA   %dx order %s %s" % (n, c, on, sku[:50]))
if not anyd:
    print("  none -- every Shopify row matches an independent replay, every date is the correct SGT date")

print()
print("=" * 112)
print("3) SPOT CHECKS".center(112))
print("=" * 112)
allrows = [(n, r) for n, d in detail.items() for r in d["body"]]
ship = [(n, r[5]) for n, r in allrows if r and r[0].strip().isdigit() and len(r) > 5 and SHIPPING.search(str(r[5]))]
print("  courier lines credited as revenue : %s" % (ship or "none"))
silver = [r for n, r in allrows if n == "Ryan" and len(r) > 5 and r[5].lower() == "zwq-aerial-silver-blu"]
print("  Ryan zwq-aerial-silver-blu rows   : %d  %s" % (len(silver), [(r[0], r[6], r[8]) for r in silver]))
aer = [r for n, r in allrows if n == "Ryan" and len(r) > 5 and "zwq-aerial" in r[5].lower()]
print("  Ryan Aerial BCAR rows total       : %d  (all at takehome %s)" % (len(aer), sorted({r[8] for r in aer if len(r) > 8})))
weak = [(n, r[0], r[5]) for n, r in allrows if len(r) > 11 and "TITLE MATCH WEAK" in r[11]]
print("  WEAK rows                         : %d" % len(weak))
for w in weak:
    print("       %-9s order %s  %s" % w)
tm_ev = [r for n, r in allrows if len(r) > 11 and "TITLE MATCH [" in r[11]]
tm_old = [r for n, r in allrows if len(r) > 11 and r[11].startswith("TITLE MATCH - add")]
print("  TITLE MATCH rows with evidence    : %d   (old bare format: %d)" % (len(tm_ev), len(tm_old)))

print()
print("=" * 112)
print("4) MANUAL / WALKIN ROWS  (supplier's own month tab vs dest)".center(112))
print("=" * 112)
for s in sups:
    d = detail.get(s["name"])
    if not d:
        continue
    dest_nonnum = [r for r in d["body"] if r and not r[0].strip().isdigit()]
    st = tabs(s["wsid"])
    if s["wtab"] not in st:
        cand = [t for t in st if re.search(M.split()[0][:3], t, re.I)]
        print("  %-9s source tab %-16r NOT FOUND   (Sep-like tabs: %s)   dest non-Shopify rows: %d"
              % (s["name"], s["wtab"], cand or "none", len(dest_nonnum)))
        continue
    src = vals(s["wsid"], s["wtab"] + "!A:L") or []
    src_nonnum = [r for r in src[1:] if r and r[0].strip() and not r[0].strip().isdigit()
                  and not re.search(r"to pay|total|paid", " ".join(r), re.I)]
    src_blank = [r for r in src[1:] if r and not r[0].strip() and len(r) > 5 and str(r[5]).strip()]
    n_src = len(src_nonnum) + len(src_blank)
    mark = "ok" if n_src <= len(dest_nonnum) else "*** dest has FEWER -- check ***"
    print("  %-9s source %-14r non-Shopify rows: %3d   dest: %3d   %s" % (s["name"], s["wtab"], n_src, len(dest_nonnum), mark))
    if n_src > len(dest_nonnum):
        issues.append("%s: dest has fewer manual rows than source" % s["name"])

print()
print("=" * 112)
print("5) RUN LOG  (latest entry per supplier)".center(112))
print("=" * 112)
for s in sups:
    rl = vals(DEST, s["runlog"] + "!A:Z") or []
    if len(rl) < 2:
        print("  %-9s (no run log rows)" % s["name"])
        continue
    h = rl[0]
    last = rl[-1]
    d = dict(zip(h, last))
    print("  %-9s %s  rows_built=%-4s status=%s  format=%s" % (s["name"], d.get("timestamp", "?"), d.get("rows_built", "?"),
                                                          d.get("status", "?"), d.get("format_status", "?")))

print()
print("=" * 112)
print(("ISSUES: %d" % len(issues)).center(112))
print("=" * 112)
for i in issues:
    print("  - " + i)
