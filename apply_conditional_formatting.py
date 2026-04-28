#!/usr/bin/env python3
"""
Apply standard conditional formatting rules + move tab to leftmost position.

Rules:
- Orange  fill: Order No. = "Walkin"  (manual entries)
- Yellow  fill: Remarks contains "TITLE MATCH" or "UNDERPRICED"  (warnings)
- Red     fill: Remarks contains "REFUND" or "CURRENCY"           (errors)

Also: moves the tab to index 0 (leftmost in tab strip).

Usage:  python3 apply_conditional_formatting.py "Mar 2026 n8n"
"""
import json, time, sys, base64, subprocess, tempfile, os
from urllib import request, parse

SA_PATH  = "/volume1/docker/n8n/ifb-n8n-integration-ad058ce853d2.json"
SHEET_ID = "1Fgs7XfYZ3_YCinVF4PoPpqALA4quciOANNZ3SYixBNM"

if len(sys.argv) < 2:
    sys.exit("usage: apply_conditional_formatting.py 'TAB NAME'")
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
target_id = None
for s in meta.get("sheets", []):
    if s["properties"]["title"] == TAB:
        target_id = s["properties"]["sheetId"]; break
if target_id is None:
    sys.exit("[err] tab not found: " + TAB)
print("[ok] target sheetId=" + str(target_id))

# Color values (R, G, B as 0..1)
ORANGE = {"red": 1.0,  "green": 0.78, "blue": 0.49}   # #FFC785
YELLOW = {"red": 1.0,  "green": 0.94, "blue": 0.62}   # #FFEF9F
RED    = {"red": 1.0,  "green": 0.78, "blue": 0.78}   # #FFC8C8

# Range for rules: A2:L (skip header)
def make_range():
    return {
        "sheetId": target_id,
        "startRowIndex": 1,
        "startColumnIndex": 0,
        "endColumnIndex": 12,
    }

requests_payload = []

# Move tab to index 0 (leftmost)
requests_payload.append({"updateSheetProperties": {
    "properties": {"sheetId": target_id, "index": 0},
    "fields": "index",
}})

# Delete existing conditional format rules first (idempotent run)
# We need to know how many exist. Get sheet's existing rules.
rules_meta = json.load(request.urlopen(request.Request(
    base + "?ranges='" + parse.quote(TAB) + "'!A1&fields=sheets.conditionalFormats",
    headers={"Authorization":"Bearer " + tok})))
existing_rules = []
for s in rules_meta.get("sheets", []):
    cf = s.get("conditionalFormats", [])
    if cf:
        existing_rules = cf
# Delete in reverse order
for i in range(len(existing_rules) - 1, -1, -1):
    requests_payload.append({"deleteConditionalFormatRule": {"sheetId": target_id, "index": i}})

# Add 3 rules — order matters: orange (Walkin) takes priority, then yellow, then red
requests_payload.append({"addConditionalFormatRule": {
    "rule": {
        "ranges": [make_range()],
        "booleanRule": {
            "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=$A2="Walkin"'}]},
            "format": {"backgroundColor": ORANGE},
        },
    },
    "index": 0,
}})

requests_payload.append({"addConditionalFormatRule": {
    "rule": {
        "ranges": [make_range()],
        "booleanRule": {
            "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=OR(REGEXMATCH($L2,"TITLE MATCH"),REGEXMATCH($L2,"UNDERPRICED"))'}]},
            "format": {"backgroundColor": YELLOW},
        },
    },
    "index": 1,
}})

requests_payload.append({"addConditionalFormatRule": {
    "rule": {
        "ranges": [make_range()],
        "booleanRule": {
            "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=OR(REGEXMATCH($L2,"REFUND"),REGEXMATCH($L2,"CURRENCY"))'}]},
            "format": {"backgroundColor": RED},
        },
    },
    "index": 2,
}})

resp = json.load(request.urlopen(request.Request(
    base + ":batchUpdate",
    data=json.dumps({"requests": requests_payload}).encode(),
    headers={"Authorization":"Bearer " + tok, "Content-Type":"application/json"})))
print("[ok] applied " + str(len(requests_payload)) + " rule update requests")
print("[done]")
