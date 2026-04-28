#!/usr/bin/env python3
"""Dump full Mar 2026 n8n contents to find duplicates / extra rows."""
import json, time, base64, subprocess, tempfile, os
from urllib import request, parse

SA_PATH  = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
SHEET_ID = "1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM"

with open(SA_PATH) as f:
    sa = json.load(f)
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
now = int(time.time())
si = b64u(json.dumps({"alg":"RS256","typ":"JWT"},separators=(",",":")).encode()) + "." + \
     b64u(json.dumps({"iss":sa["client_email"],"scope":"https://www.googleapis.com/auth/spreadsheets.readonly",
                      "aud":"https://oauth2.googleapis.com/token","exp":now+3600,"iat":now},
                     separators=(",",":")).encode())
fd, kp = tempfile.mkstemp()
try:
    os.write(fd, sa["private_key"].encode()); os.close(fd)
    sig = subprocess.run(["openssl","dgst","-binary","-sha256","-sign",kp],
                         input=si.encode(), capture_output=True, check=True).stdout
finally:
    os.unlink(kp)
jwt = si + "." + b64u(sig)
tok = json.load(request.urlopen(request.Request("https://oauth2.googleapis.com/token",
    data=parse.urlencode({"grant_type":"urn:ietf:params:oauth:grant-type:jwt-bearer","assertion":jwt}).encode(),
    headers={"Content-Type":"application/x-www-form-urlencoded"})))["access_token"]
range_q = parse.quote("'Mar 2026 n8n'!A:L")
url = "https://sheets.googleapis.com/v4/spreadsheets/" + SHEET_ID + "/values/" + range_q
data = json.load(request.urlopen(request.Request(url, headers={"Authorization":"Bearer " + tok}))).get("values", [])
print("total rows:", len(data))

# Count by Order No.
from collections import Counter
order_counts = Counter()
walkin_count = 0
for r in data[1:]:
    if not r: continue
    on = r[0] if len(r) > 0 else ""
    if on == "Walkin": walkin_count += 1
    else: order_counts[on] += 1

# Top dupes
print("\nWalkin rows:", walkin_count)
print("\nUnique Shopify orders:", len(order_counts))
print("Total Shopify rows:", sum(order_counts.values()))
print("\nTop 15 orders by row count:")
for on, cnt in order_counts.most_common(15):
    print(f"  {on}: {cnt}")
