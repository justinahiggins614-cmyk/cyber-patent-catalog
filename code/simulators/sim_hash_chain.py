#!/usr/bin/env python3
"""
Forensic hash-chain simulator (educational).
Covers CPC G06F21/64 (data integrity / audit): every evidence item
is appended to a tamper-evident log where each entry commits to the
previous entry's hash. Any alteration breaks the chain and is
detectable during audit.
"""
import hashlib
import json
from dataclasses import dataclass, field


def _digest(entry: dict) -> str:
    return hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()


@dataclass
class EvidenceChain:
    chain: list = field(default_factory=list)

    def append(self, evidence_id: str, description: str, collector: str):
        prev = self.chain[-1]["hash"] if self.chain else "GENESIS"
        entry = {"index": len(self.chain), "evidence_id": evidence_id,
                 "description": description, "collector": collector,
                 "prev_hash": prev}
        entry["hash"] = _digest(entry)
        self.chain.append(entry)
        print(f"logged #{entry['index']}: {evidence_id} ({entry['hash'][:12]}...)")

    def audit(self) -> bool:
        prev = "GENESIS"
        for entry in self.chain:
            if entry["prev_hash"] != prev:
                print(f"CHAIN BROKEN at #{entry['index']}: prev link mismatch")
                return False
            check = dict(entry)
            h = check.pop("hash")
            if _digest(check) != h:
                print(f"CHAIN BROKEN at #{entry['index']}: entry tampered")
                return False
            prev = h
        print(f"audit OK: {len(self.chain)} entries, chain intact")
        return True


def demo():
    log = EvidenceChain()
    log.append("DISK-001", "laptop SSD image", "forensics-team")
    log.append("LOG-002", "firewall export 2026-09-27", "forensics-team")
    log.append("MEM-003", "memory dump web-srv-02", "ir-lead")
    assert log.audit() is True
    # attacker alters one entry in place
    log.chain[1]["description"] = "firewall export (sanitized)"
    assert log.audit() is False
    print("tampering detected as expected")
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
