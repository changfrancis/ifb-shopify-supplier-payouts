#!/usr/bin/env python3
"""Apply the user's Aerial BCAR rule to Sep 2026 Ryan, then move his reference to MSRP.

Rule (user, 2026-10-01):
  order < #6464  (promo, up to 21 Sep 18:10 SGT): IFB $9.40, takehome $45.60
  order >= #6464 (MSRP):                           IFB $9.71, takehome $55.29
  Listing Price = the actual Shopify sale value (SGD shop money).

Step 1 rewrites G/H/I/L of the Aerial rows in 'Sep 2026 Ryan n8n'.
Step 2 sets the three zwq-aerial-*-blu reference rows to $65.00 / $9.71 / $55.29
       so October onward is MSRP with no manual correction.
Usage: aerial_fix.py [--apply]
"""
import json, time, base64, subprocess, tempfile, os, re, socket, sys
from urllib import request, parse, error

socket.setdefaulttimeout(60)
SA = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
DEST = "1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM"
REG = "1oIoc5l6AJxbREujV72P0aVICMwrDSRFcgzvPv781xhs"
TAB = "Sep 2026 Ryan n8n"
BOUNDARY = 6464
PROMO = (9.40, 45.60)
MSRP = (9.71, 55.29)
REF_SKUS = ["zwq-aerial-black-blu", "zwq-aerial-orange-blu", "zwq-aerial-silver-blu"]
APPLY = "--apply" in sys.argv

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


env = {}
for line in open("/volume1/docker/n8n/.env"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
SHOP = env["SHOPIFY_SHOP"]
stok = json.load(request.urlopen(request.Request(
    "https://%s.myshopify.com/admin/oauth/access_token" % SHOP,
    data=parse.urlencode({"grant_type": "client_credentials", "client_id": env["SHOPIFY_CLIENT_ID"],
                          "client_secret": env["SHOPIFY_CLIENT_SECRET"]}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"})))["access_token"]
SH = {"X-Shopify-Access-Token": stok}
orders = {}
url = ("https://%s.myshopify.com/admin/api/2026-04/orders.json?status=any&limit=250"
       "&created_at_min=%s&created_at_max=%s" % (SHOP, parse.quote("2026-09-01T00:00:00+08:00"),
                                                  parse.quote("2026-09-30T23:59:59+08:00")))
while url:
    r = request.urlopen(request.Request(url, headers=SH))
    for o in json.load(r).get("orders", []):
        orders[str(o["order_number"])] = o
    m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link") or "")
    url = m.group(1) if m else None


def money(s):
    m = re.search("-?[0-9,]+[.]?[0-9]*", str(s).replace("$", ""))
    return float(m.group().replace(",", "")) if m else 0.0


print("=" * 118)
print(("STEP 1 - AERIAL ROWS IN %s  (%s)" % (TAB, "LIVE" if APPLY else "DRY RUN")).center(118))
print("=" * 118)
rows = req(DEST, "/values/" + parse.quote(TAB) + "!A:L").get("values", [])
tot_before = sum(money(r[8] if len(r) > 8 else "") for r in rows[1:])
updates = []
print("%-6s %-7s %-22s %-5s %9s %8s %9s   ->  %9s %8s %9s  %s"
      % ("line", "order", "sku", "ccy", "listing", "fee", "take", "listing", "fee", "take", "period"))
for i, r in enumerate(rows[1:], start=2):
    sku = (r[5] if len(r) > 5 else "").strip()
    if not sku.lower().startswith("zwq-aerial"):
        continue
    on = (r[0] if r else "").strip()
    o = orders.get(on)
    li = next((x for x in (o or {}).get("line_items", []) if (x.get("sku") or "").lower() == sku.lower()), None)
    if not li:
        print("  *** line %d order %s %s: Shopify line not found - ABORTING ***" % (i, on, sku))
        sys.exit(1)
    sale = round(float(li.get("price") or 0), 2)
    ccy = o.get("presentment_currency") or "SGD"
    promo = int(on) < BOUNDARY
    fee, take = PROMO if promo else MSRP
    period = "promo" if promo else "MSRP"
    old_rem = (r[11] if len(r) > 11 else "").strip()
    tag = ("AERIAL %s pricing (order %s #%d): IFB $%.2f, takehome $%.2f; listing = Shopify sale value"
           % (period, "before" if promo else "from", BOUNDARY, fee, take))
    if ccy != "SGD":
        tag += " (%s order - listing exceeds fee+takehome by FX)" % ccy
    elif promo and sale > 55.01:
        tag += " -- VERIFY: charged MSRP $%.2f inside promo order range (created %s, updated %s)" % (
            sale, o.get("created_at"), o.get("updated_at"))
        print("  !! order %s: promo by order number but charged $%.2f; created %s, updated %s"
              % (on, sale, o.get("created_at"), o.get("updated_at")))
    rem = (old_rem + " | " + tag) if old_rem and "AERIAL" not in old_rem else (old_rem if "AERIAL" in old_rem else tag)
    print("%-6d %-7s %-22s %-5s %9s %8s %9s   ->  %9s %8s %9s  %s"
          % (i, on, sku[:22], ccy, r[6] if len(r) > 6 else "", r[7] if len(r) > 7 else "", r[8] if len(r) > 8 else "",
             "$%.2f" % sale, "$%.2f" % fee, "$%.2f" % take, period))
    updates.append({"range": "'%s'!G%d:I%d" % (TAB, i, i), "values": [["$%.2f" % sale, "$%.2f" % fee, "$%.2f" % take]]})
    updates.append({"range": "'%s'!L%d" % (TAB, i), "values": [[rem]]})
n = len(updates) // 2
np_ = sum(1 for u in updates[0::2] if u["values"][0][2] == "$45.60")
nm = n - np_
delta = nm * (MSRP[1] - 45.60)
print()
print("  %d Aerial rows: %d promo @ $45.60, %d MSRP @ $55.29" % (n, np_, nm))
print("  Ryan Sep takehome: $%.2f -> $%.2f  (%+.2f)" % (tot_before, tot_before + delta, delta))

print()
print("=" * 118)
print(("STEP 2 - RYAN AMOUNT REFERENCE -> MSRP  (%s)" % ("LIVE" if APPLY else "DRY RUN")).center(118))
print("=" * 118)
reg = req(REG, "/values/Registry!A:M").get("values", [])
ci = {h.strip().lower(): k for k, h in enumerate(reg[0])}
rr = next(x for x in reg[1:] if x[ci["supplier_name"]] == "Ryan")
RSID, RTAB = rr[ci["amount_ref_sheet_id"]], rr[ci["amount_ref_tab_name"]]
ref = req(RSID, "/values/" + parse.quote(RTAB) + "!A:D").get("values", [])
ref_updates = []
for i, r in enumerate(ref[1:], start=2):
    if r and str(r[0]).strip().lower() in REF_SKUS:
        print("  row %-3d %-24s %s  ->  ['$65.00', '$9.71', '$55.29']" % (i, r[0], r[1:4]))
        ref_updates.append({"range": "'%s'!B%d:D%d" % (RTAB, i, i), "values": [["$65.00", "$9.71", "$55.29"]]})
if len(ref_updates) != 3:
    print("  *** expected 3 reference rows, found %d - ABORTING ***" % len(ref_updates))
    sys.exit(1)

if not APPLY:
    print()
    print("  DRY RUN - re-run with --apply")
    sys.exit(0)

req(DEST, "/values:batchUpdate", data=json.dumps({"valueInputOption": "RAW", "data": updates}).encode(), method="POST")
req(RSID, "/values:batchUpdate", data=json.dumps({"valueInputOption": "RAW", "data": ref_updates}).encode(), method="POST")
rows = req(DEST, "/values/" + parse.quote(TAB) + "!A:L").get("values", [])
aer = [r for r in rows[1:] if len(r) > 5 and r[5].lower().startswith("zwq-aerial")]
print()
print("  APPLIED. Ryan Sep: %d rows, takehome $%.2f" % (len(rows) - 1, sum(money(r[8] if len(r) > 8 else "") for r in rows[1:])))
print("  Aerial takehome values now: %s" % sorted({(r[8]) for r in aer}))
ref = req(RSID, "/values/" + parse.quote(RTAB) + "!A:D").get("values", [])
for r in ref[1:]:
    if r and str(r[0]).strip().lower() in REF_SKUS:
        print("  reference: %s" % r[:4])
