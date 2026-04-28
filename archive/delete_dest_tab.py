#!/usr/bin/env python3
"""Delete a tab from the IFB destination sheet. Usage: delete_dest_tab.py 'TAB NAME'"""
import json, time, sys, base64, subprocess, tempfile, os
from urllib import request, parse, error

SA_PATH  = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
SHEET_ID = "1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM"

if len(sys.argv) < 2:
    sys.exit("usage: delete_dest_tab.py 'TAB NAME'")
TAB = sys.argv[1]

with open(SA_PATH) as f:
    sa = json.load(f)
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
now = int(time.time())
si = b64u(json.dumps({"alg":"RS256","typ":"JWT"},separators=(",",":")).encode()) + "." + \
     b64u(json.dumps({"iss":sa["client_email"],"scope":"https://www.googleapis.com/auth/spreadsheets",
                      "aud":"https://oauth2.googleapis.com/token","exp":now+3600,"iat":now},
                     separators=(",",":")).encode())
fd, kp = tempfile.mkstemp(prefix="sa_")
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
base = "https://sheets.googleapis.com/v4/spreadsheets/" + SHEET_ID
meta = json.load(request.urlopen(request.Request(base + "?fields=sheets.properties",
    headers={"Authorization":"Bearer " + tok})))
existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
if TAB in existing:
    request.urlopen(request.Request(base + ":batchUpdate",
        data=json.dumps({"requests": [{"deleteSheet": {"sheetId": existing[TAB]}}]}).encode(),
        headers={"Authorization":"Bearer " + tok, "Content-Type":"application/json"}))
    print("[ok] deleted: " + TAB)
else:
    print("[ok] not present: " + TAB)
