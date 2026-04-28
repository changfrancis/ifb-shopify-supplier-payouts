#!/usr/bin/env python3
"""Re-set SMTP credential with port=465, secure=true. Preserves password from existing cred."""
import json, subprocess, sys

# Read existing credentials to grab the current password
out = subprocess.run(
    ["sudo", "-n", "/usr/local/bin/docker", "exec", "n8n", "n8n", "export:credentials", "--all", "--decrypted"],
    capture_output=True, check=True
).stdout.decode()
creds = json.loads(out)
existing = next((c for c in creds if c["type"] == "smtp"), None)
if not existing:
    sys.exit("[err] no existing SMTP credential to preserve password from")

cred_id = existing["id"]
cred_name = existing["name"]
data = dict(existing["data"])
# Force the right fields
data["host"] = "smtp.gmail.com"
data["port"] = 465
data["secure"] = True
data["user"] = "ai.idealmachinefactory@gmail.com"
# password preserved from existing
# hostName preserved from existing

corrected = [{"id": cred_id, "name": cred_name, "type": "smtp", "data": data}]
with open("/tmp/smtp-fix.json", "w") as f:
    json.dump(corrected, f)

print(f"[ok] writing corrected credential: id={cred_id}")
print(f"     host={data['host']}, port={data['port']}, secure={data['secure']}, user={data['user']}, password length={len(data['password'])}")
