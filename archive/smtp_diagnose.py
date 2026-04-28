#!/usr/bin/env python3
"""Diagnose SMTP send by reading credential from n8n + testing connection.
Does NOT print the password."""
import json, subprocess, sys, smtplib

# Read credential via n8n CLI (decrypted dump)
out = subprocess.run(
    ["sudo", "-n", "/usr/local/bin/docker", "exec", "n8n", "n8n", "export:credentials", "--all", "--decrypted"],
    capture_output=True, check=True
).stdout.decode()
creds = json.loads(out)
smtp = next((c for c in creds if c["type"] == "smtp"), None)
if not smtp:
    sys.exit("[err] no SMTP credential found")
d = smtp["data"]
host = d["host"]; port = int(d["port"]); user = d["user"]; pw = d["password"]; secure = d.get("secure", False)
print(f"[info] host={host} port={port} user={user} secure={secure}")
print(f"[info] password: length={len(pw)}, no-spaces={' ' not in pw}")

print("[step 1] connecting...")
try:
    if secure:
        srv = smtplib.SMTP_SSL(host, port, timeout=15)
    else:
        srv = smtplib.SMTP(host, port, timeout=15)
    srv.set_debuglevel(1)
    print("[step 2] EHLO...")
    srv.ehlo()
    if not secure:
        print("[step 3] STARTTLS...")
        srv.starttls()
        srv.ehlo()
    print("[step 4] LOGIN...")
    srv.login(user, pw)
    print("[ok] AUTH SUCCESS — credentials are accepted by Gmail")
    print("[step 5] sending test message...")
    msg = f"From: {user}\r\nTo: {user}\r\nSubject: n8n SMTP test\r\n\r\nIf you can read this, SMTP works.\r\n"
    srv.sendmail(user, [user], msg)
    print("[ok] test message sent to " + user)
    srv.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"[ERROR] AUTH REJECTED — {e.smtp_code} {e.smtp_error}")
    print("Most likely: app password wrong, 2SV not enabled, or account flagged.")
except smtplib.SMTPException as e:
    print(f"[ERROR] SMTP error: {type(e).__name__}: {e}")
except Exception as e:
    print(f"[ERROR] Connection error: {type(e).__name__}: {e}")
