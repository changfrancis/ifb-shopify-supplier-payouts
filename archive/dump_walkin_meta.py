#!/usr/bin/env python3
"""Dump Walkin sheet metadata so we know the tab name and gid."""
import json, time, base64, subprocess, tempfile, os
from urllib import request, parse

SA_PATH  = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
SHEET_ID = "1X0Ddth8Uc05eVn7KEvJJR6nAkqeysPmVXhse3hQjHQU"

with open(SA_PATH) as f:
    sa = json.load(f)
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
now = int(time.time())
si = b64u(json.dumps({"alg":"RS256","typ":"JWT"},separators=(",",":")).encode()) + "." + \
     b64u(json.dumps({"iss":sa["client_email"],"scope":"https://www.googleapis.com/auth/spreadsheets.readonly",
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

url = "https://sheets.googleapis.com/v4/spreadsheets/" + SHEET_ID + "?fields=sheets.properties"
meta = json.load(request.urlopen(request.Request(url, headers={"Authorization":"Bearer " + tok})))
print("=== Walkin source tabs ===")
for s in meta.get("sheets", []):
    p = s["properties"]
    print("  title=" + p["title"] + "  sheetId=" + str(p["sheetId"]))
