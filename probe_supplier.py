#!/usr/bin/env python3
"""Why did each row in a supplier's monthly tab get attributed to that supplier?

Replicates the v5 child's exact matcher (incl. the property filter that drops
email/phone/address/contact/name props) and reports, per row, the EXACT field and
the EXACT hint substring that caused the match -- so title-hint false positives can
be judged against the real Shopify line item instead of guessed at.

Run on the NAS (needs the SA key and Shopify creds that live there):
    python3 probe_supplier.py <SupplierName> "<MMM YYYY>"
"""
import json, time, base64, subprocess, tempfile, os, re, socket, sys
from urllib import request, parse

socket.setdefaulttimeout(30)
SA = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
DEST = "1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM"
REG = "1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs"
SUPPLIER = sys.argv[1] if len(sys.argv) > 1 else "Vitae"
MONTH = sys.argv[2] if len(sys.argv) > 2 else "Aug 2026"
ENVF = "/volume1/docker/n8n/.env"
BSL = chr(92)

# ---------- google token ----------
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
gtok = json.load(request.urlopen(request.Request(
    "https://oauth2.googleapis.com/token",
    data=parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                          "assertion": si + "." + b(sg)}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"})))["access_token"]
GH = {"Authorization": "Bearer " + gtok}


def vals(sid, rng, tries=4):
    u = "https://sheets.googleapis.com/v4/spreadsheets/" + sid + "/values/" + parse.quote(rng)
    for _ in range(tries):
        try:
            return json.load(request.urlopen(request.Request(u, headers=GH), timeout=30)).get("values", [])
        except Exception:
            time.sleep(2)
    raise RuntimeError("read failed: " + rng)


# ---------- shopify token ----------
env = {}
for line in open(ENVF):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
stok = json.load(request.urlopen(request.Request(
    "https://%s.myshopify.com/admin/oauth/access_token" % env["SHOPIFY_SHOP"],
    data=parse.urlencode({"grant_type": "client_credentials",
                          "client_id": env["SHOPIFY_CLIENT_ID"],
                          "client_secret": env["SHOPIFY_CLIENT_SECRET"]}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"})))["access_token"]
SH = {"X-Shopify-Access-Token": stok}
SHOP = env["SHOPIFY_SHOP"]


def get_order(no):
    u = ("https://%s.myshopify.com/admin/api/2026-04/orders.json?status=any&name=%s&limit=5"
         % (SHOP, no))
    for o in json.load(request.urlopen(request.Request(u, headers=SH))).get("orders", []):
        if str(o.get("order_number")) == str(no):
            return o
    return None


# ---------- registry: this supplier's row ----------
reg = vals(REG, "Registry!A:M")
ci = {h.strip().lower(): i for i, h in enumerate(reg[0])}


def g(r, k):
    i = ci.get(k)
    return r[i] if i is not None and i < len(r) else ""


vrow = next(r for r in reg[1:] if g(r, "supplier_name") == SUPPLIER)

hints_raw = g(vrow, "title_hints")
HINTS = [h.strip().lower() for h in hints_raw.split(",") if h.strip()]
EXCL = [x.strip() for x in g(vrow, "exclude_skus").split(",") if x.strip()]

allh = {}
for r in reg[1:]:
    nm = g(r, "supplier_name")
    if nm and g(r, "active").strip().upper() == "TRUE":
        allh[nm] = [h.strip().lower() for h in g(r, "title_hints").split(",") if h.strip()]

# ---------- supplier amount reference ----------
ref = vals(g(vrow, "amount_ref_sheet_id"), g(vrow, "amount_ref_tab_name") + "!A:D")
ref_skus = [r[0].strip() for r in ref[1:] if r and str(r[0]).strip() and str(r[0]).strip().lower() != "sku"]

SPECIAL = set(".+?^${}()|[]" + BSL)


def esc(s):
    return "".join((BSL + ch) if ch in SPECIAL else ch for ch in s)


def wf_re(sku):
    p = esc(sku).replace("COLOUR", ".+").replace("XXX", ".+")
    p = re.sub("[-_]", "[-_]", p)
    return re.compile("^" + p + "$", re.I)


MATCHERS = [(s, wf_re(s)) for s in ref_skus]

print("=" * 96)
print(("%s - %s attribution audit" % (SUPPLIER, MONTH)).center(96))
print("=" * 96)
print()
print("  Registry title_hints  : %s" % (hints_raw or "(empty)"))
print("  Registry exclude_skus : %s" % (", ".join(EXCL) or "(empty)"))
print("  Amount Reference tab  : %s  (%d SKUs)" % (g(vrow, "amount_ref_tab_name"), len(ref_skus)))
print("  Reference SKUs        : %s" % (", ".join(ref_skus) or "(none)"))
print()

data = vals(DEST, MONTH + " " + SUPPLIER + " n8n!A:L")
rows = data[1:]
print("  %s %s n8n rows: %d" % (MONTH, SUPPLIER, len(rows)))
print()

seen = []
for r in rows:
    on = (r[0] if len(r) > 0 else "").strip()
    sku = (r[5] if len(r) > 5 else "").strip()
    rem = (r[11] if len(r) > 11 else "").strip()
    lp = (r[6] if len(r) > 6 else "").strip()
    seen.append((on, sku, lp, rem))

FIELDS = ["li.title", "li.variant_title", "li.name", "li.vendor",
          "properties(filtered)", "order.note", "order.tags"]

order_cache = {}
for on, sku, lp, rem in seen:
    print("-" * 96)
    print("ROW  order=%s  sku=%r  listing=%s" % (on, sku, lp))
    print("     remarks: %s" % (rem or "(none)"))

    hit = next((s for s, rx in MATCHERS if rx.match(sku)), None)
    if hit:
        print("     -> matched %s Amount Reference entry %r  (legitimate, price-based)" % (SUPPLIER, hit))
        print()
        continue

    if not on.isdigit():
        print("     -> non-Shopify row (Walkin/Manual) - came straight from the supplier's own sheet")
        print()
        continue

    o = order_cache.get(on)
    if o is None:
        o = get_order(on)
        order_cache[on] = o
    if not o:
        print("     -> ORDER NOT FOUND in Shopify")
        print()
        continue

    li = None
    for cand in o.get("line_items", []):
        if (cand.get("sku") or cand.get("title") or cand.get("name") or "").strip() == sku:
            li = cand
            break
    if li is None:
        for cand in o.get("line_items", []):
            if sku.lower() in ((cand.get("sku") or "") + " " + (cand.get("title") or "")).lower():
                li = cand
                break
    if li is None:
        print("     -> line item not found in order")
        print()
        continue

    props = li.get("properties") or []
    filtered = [p for p in props
                if not re.search("email|phone|address|contact|name", str(p.get("name") or "").lower())
                and "@" not in str(p.get("value") or "")]
    dropped = [p for p in props if p not in filtered]

    vals_by_field = [
        li.get("title") or "",
        li.get("variant_title") or "",
        li.get("name") or "",
        li.get("vendor") or "",
        " ".join((str(p.get("name") or "") + " " + str(p.get("value") or "")) for p in filtered),
        o.get("note") or "",
        o.get("tags") or "",
    ]

    print("     -> NOT in %s's Amount Reference. Attributed by TITLE HINT. Which field?" % SUPPLIER)
    print()
    print("        %-22s | %s" % ("FIELD", "VALUE"))
    fired_any = False
    for fname, fval in zip(FIELDS, vals_by_field):
        low = fval.lower()
        fired = [h for h in HINTS if h in low]
        mark = ("  <== FIRES: " + ", ".join(repr(x) for x in fired)) if fired else ""
        if fired:
            fired_any = True
        print("        %-22s | %s%s" % (fname, (fval[:70] or "(empty)"), mark))
    if dropped:
        print("        %-22s | %s" % ("properties(DROPPED)",
              "; ".join("%s=%s" % (p.get("name"), str(p.get("value"))[:30]) for p in dropped)))
    if not fired_any:
        print("        !! NO %s hint fires on current data - stale row, or hints changed since the run" % SUPPLIER)
    print()
    hay = " ".join(vals_by_field).lower()
    others = []
    for nm, hs in allh.items():
        if nm == SUPPLIER:
            continue
        f = [h for h in hs if h in hay]
        if f:
            others.append("%s%s" % (nm, f))
    print("        Shopify vendor field : %s" % (li.get("vendor") or "(empty)"))
    print("        other suppliers' hints also firing: %s" % (", ".join(others) or "none"))
    print()
