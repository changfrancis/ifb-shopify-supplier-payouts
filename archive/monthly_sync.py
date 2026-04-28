#!/usr/bin/env python3
"""
Full monthly sync: pull Shopify orders for a date range, match against
Amount Reference + title-hint fallback, write rows to target tab.

Usage:  python3 monthly_sync.py <TAB_NAME> <START_ISO> <END_ISO>
Example: python3 monthly_sync.py "test" "2026-03-01T00:00:00+08:00" "2026-03-31T23:59:59+08:00"
"""
import json, time, sys, base64, subprocess, tempfile, os, re
from urllib import request, parse, error

SA_PATH       = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
ENV_PATH      = "/volume1/docker/n8n/.env"
SHEET_ID      = "1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM"
API_VERSION   = "2026-04"
EXCLUDE_SKUS  = [
    "free-gfz-spamf-blaster",
    "free-gfz-3deg-riser-rmr",
    "free-gfz-2deg-riser-extended",
    "free-gfz-talon-mag-bumper",
    "free-gfz-3deg-riser-romeo",
    "free-gfz-talon-mag-duo-connector",
]
TITLE_HINT_PATTERNS = [r"gfz", r"gavin"]

if len(sys.argv) < 4:
    sys.exit("usage: monthly_sync.py TAB START_ISO END_ISO")
TAB, START_ISO, END_ISO = sys.argv[1], sys.argv[2], sys.argv[3]

shopify_env = {}
with open(ENV_PATH) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            shopify_env[k] = v
SHOP          = shopify_env["SHOPIFY_SHOP"]
CLIENT_ID     = shopify_env["SHOPIFY_CLIENT_ID"]
CLIENT_SECRET = shopify_env["SHOPIFY_CLIENT_SECRET"]

with open(SA_PATH) as f:
    sa = json.load(f)
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
now = int(time.time())
sig_input = b64u(json.dumps({"alg":"RS256","typ":"JWT"},separators=(",",":")).encode()) + "." + \
            b64u(json.dumps({"iss":sa["client_email"],"scope":"https://www.googleapis.com/auth/spreadsheets",
                             "aud":"https://oauth2.googleapis.com/token","exp":now+3600,"iat":now},
                            separators=(",",":")).encode())
fd, kp = tempfile.mkstemp(prefix="sa_")
try:
    os.write(fd, sa["private_key"].encode()); os.close(fd)
    sig = subprocess.run(["openssl","dgst","-binary","-sha256","-sign",kp],
                         input=sig_input.encode(), capture_output=True, check=True).stdout
finally:
    os.unlink(kp)
gjwt = sig_input + "." + b64u(sig)
gtok = json.load(request.urlopen(request.Request("https://oauth2.googleapis.com/token",
    data=parse.urlencode({"grant_type":"urn:ietf:params:oauth:grant-type:jwt-bearer","assertion":gjwt}).encode(),
    headers={"Content-Type":"application/x-www-form-urlencoded"})))["access_token"]
print("[ok] google access token obtained")

sresp = json.load(request.urlopen(request.Request(
    "https://" + SHOP + ".myshopify.com/admin/oauth/access_token",
    data=parse.urlencode({"grant_type":"client_credentials","client_id":CLIENT_ID,"client_secret":CLIENT_SECRET}).encode(),
    headers={"Content-Type":"application/x-www-form-urlencoded"})))
stok = sresp["access_token"]
print("[ok] shopify access token obtained")

range_q = parse.quote("'Amount Reference'!A:D")
url = "https://sheets.googleapis.com/v4/spreadsheets/" + SHEET_ID + "/values/" + range_q
ref = json.load(request.urlopen(request.Request(url, headers={"Authorization":"Bearer " + gtok})))
ref_rows = ref.get("values", [])
ref_headers = ref_rows[0] if ref_rows else []
ref_data = ref_rows[1:] if len(ref_rows) > 1 else []

def col(row, name):
    if name in ref_headers:
        i = ref_headers.index(name)
        return row[i] if i < len(row) else ""
    return ""

def parse_price(s):
    if not s: return 0
    m = re.search(r"-?\d+(?:\.\d+)?", str(s).replace("$","").replace(",","").replace(" ",""))
    return float(m.group(0)) if m else 0

masters = []
for r in ref_data:
    sku = (col(r, "SKU") or "").strip()
    if not sku: continue
    listing  = parse_price(col(r, "Listing Price"))
    fee      = parse_price(col(r, "3DPS + Stripe Fee (3.4%)"))
    takehome = parse_price(col(r, "Gavin Amount (Takehome)"))
    if "COLOUR" in sku:
        pat = "^" + re.escape(sku).replace("COLOUR", ".+") + "$"
    else:
        pat = "^" + re.escape(sku) + "$"
    masters.append({"sku":sku,"listing":listing,"fee":fee,"takehome":takehome,"re":re.compile(pat, re.IGNORECASE)})
print("[ok] amount reference loaded: " + str(len(masters)) + " masters")

url = ("https://" + SHOP + ".myshopify.com/admin/api/" + API_VERSION + "/orders.json"
       "?status=any&limit=250"
       "&created_at_min=" + parse.quote(START_ISO) +
       "&created_at_max=" + parse.quote(END_ISO))
all_orders = []
page = 0
while url and page < 50:
    page += 1
    req = request.Request(url, headers={"X-Shopify-Access-Token": stok})
    resp = request.urlopen(req)
    data = json.loads(resp.read().decode())
    if isinstance(data.get("orders"), list):
        all_orders.extend(data["orders"])
    link = resp.headers.get("Link") or resp.headers.get("link") or ""
    m = re.search(r'<([^>]+)>;\s*rel="next"', link)
    url = m.group(1) if m else None
print("[ok] fetched " + str(len(all_orders)) + " orders across " + str(page) + " page(s)")

exclude_res = []
for pat in EXCLUDE_SKUS:
    p = re.escape(pat).replace(r"\*", ".*")
    exclude_res.append(re.compile("^" + p + "$", re.IGNORECASE))

title_hint_re = re.compile("|".join(TITLE_HINT_PATTERNS), re.IGNORECASE)
MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fmt_date(iso):
    if not iso: return ""
    iso2 = iso.replace("Z","+00:00")
    try:
        from datetime import datetime
        d = datetime.fromisoformat(iso2)
        return str(d.day) + " " + MON[d.month-1] + " " + str(d.year)
    except Exception:
        return iso.split("T")[0]

def fmt_sgd(n):
    return "$" + ("%.2f" % float(n))

def is_excluded(sku):
    return sku and any(r.match(sku) for r in exclude_res)

def find_master(sku):
    if not sku: return None
    for m in masters:
        if m["re"].match(sku): return m
    return None

def title_hint(li):
    t = (li.get("title","") or "") + " " + (li.get("variant_title","") or "")
    return bool(title_hint_re.search(t.lower()))

rows = []
for o in all_orders:
    for li in (o.get("line_items") or []):
        sku = li.get("sku") or ""
        if is_excluded(sku): continue
        m = find_master(sku)
        title_hit = (not m) and title_hint(li)
        if not m and not title_hit: continue

        first = (o.get("customer") or {}).get("first_name") or ""
        last  = (o.get("customer") or {}).get("last_name") or ""
        name  = (first + " " + last).strip() or "Guest"
        order_no = str(o.get("order_number") or (o.get("name") or "").lstrip("#"))
        qty = li.get("quantity") or 1

        if m:
            listing  = fmt_sgd(m["listing"])
            fee      = fmt_sgd(m["fee"])
            takehome = fmt_sgd(m["takehome"])
            remarks  = ""
        else:
            li_price = float(li.get("price") or 0)
            listing  = fmt_sgd(li_price * qty)
            fee      = ""
            takehome = ""
            remarks  = "TITLE MATCH - add to Amount Reference?"

        rows.append([
            order_no, fmt_date(o.get("created_at")), name, o.get("email") or "", "",
            sku, listing, fee, takehome, "", "", remarks
        ])

print("[ok] built " + str(len(rows)) + " rows")

clear_range = "'" + TAB + "'!A2:L"
clear_url = "https://sheets.googleapis.com/v4/spreadsheets/" + SHEET_ID + "/values/" + parse.quote(clear_range) + ":clear"
request.urlopen(request.Request(clear_url, data=b"{}", method="POST",
    headers={"Authorization":"Bearer " + gtok, "Content-Type":"application/json"}))
print("[ok] cleared " + clear_range)

if rows:
    range_n = "'" + TAB + "'!A2"
    upd_url = ("https://sheets.googleapis.com/v4/spreadsheets/" + SHEET_ID +
               "/values/" + parse.quote(range_n) + ":append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS")
    body = json.dumps({"range":range_n,"majorDimension":"ROWS","values":rows}).encode()
    resp = json.load(request.urlopen(request.Request(upd_url, data=body, method="POST",
        headers={"Authorization":"Bearer " + gtok, "Content-Type":"application/json"})))
    print("[ok] appended " + str(resp.get("updates",{}).get("updatedRows", "?")) + " rows to " + TAB)

print("[done]")
