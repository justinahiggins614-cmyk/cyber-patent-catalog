#!/usr/bin/env python3
"""
Signature-based IDS simulator (educational).
Covers CPC H04L63/14 / G06F21/56 (intrusion detection, malware
detection): inspect traffic against a signature database, raise
alerts with severity, track offender reputation.
"""
from dataclasses import dataclass, field


@dataclass
class Signature:
    sid: str
    pattern: bytes
    severity: str
    description: str


@dataclass
class IDS:
    signatures: list = field(default_factory=list)
    alerts: list = field(default_factory=list)
    reputation: dict = field(default_factory=dict)

    def add_signature(self, sig: Signature):
        self.signatures.append(sig)

    def inspect(self, src: str, payload: bytes):
        hits = []
        for sig in self.signatures:
            if sig.pattern in payload:
                hits.append(sig)
                self.alerts.append({"src": src, "sid": sig.sid,
                                    "severity": sig.severity,
                                    "desc": sig.description})
        self.reputation[src] = self.reputation.get(src, 0) + len(hits)
        return hits

    def blocked(self, src: str, threshold: int = 2) -> bool:
        return self.reputation.get(src, 0) >= threshold


def demo():
    ids = IDS()
    ids.add_signature(Signature("S-001", b"../../etc/passwd", "high", "path traversal probe"))
    ids.add_signature(Signature("S-002", b"<script>", "medium", "XSS attempt"))
    ids.add_signature(Signature("S-003", b"UNION SELECT", "high", "SQL injection"))

    traffic = [
        ("10.0.0.8", b"GET /index.html HTTP/1.1"),
        ("203.0.113.7", b"GET /../../etc/passwd HTTP/1.1"),
        ("203.0.113.7", b"GET /?q=<script>alert(1)</script>"),
        ("198.51.100.3", b"POST /login u=' UNION SELECT * FROM users"),
    ]
    for src, payload in traffic:
        hits = ids.inspect(src, payload)
        print(f"{src}: {'ALERT ' + ','.join(s.sid for s in hits) if hits else 'clean'}")
    print("Alerts:", len(ids.alerts))
    print("203.0.113.7 blocked:", ids.blocked("203.0.113.7"))
    print("10.0.0.8 blocked:", ids.blocked("10.0.0.8"))
    assert len(ids.alerts) == 3
    assert ids.blocked("203.0.113.7") and not ids.blocked("10.0.0.8")
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
