#!/usr/bin/env python3
"""
PKI certificate-chain simulator (educational).
Covers CPC H04L63/08 / H04L9/32 (authentication, digital
certificates): a root CA signs intermediate certs, intermediates
sign leaf certs; validation walks the chain checking signatures,
expiry, and revocation.
"""
import hashlib
import time
from dataclasses import dataclass, field


def _sign(payload: bytes, key: str) -> str:
    return hashlib.sha256(key.encode() + payload).hexdigest()


@dataclass
class Cert:
    subject: str
    issuer: str
    pubkey: str
    not_after: float
    signature: str = ""
    serial: int = 0

    def body(self) -> bytes:
        return f"{self.subject}|{self.issuer}|{self.pubkey}|{self.not_after}|{self.serial}".encode()


@dataclass
class PKI:
    revoked: set = field(default_factory=set)

    def issue(self, subject, issuer, issuer_key, pubkey, days=365, serial=1) -> Cert:
        c = Cert(subject, issuer, pubkey, time.time() + days * 86400, serial=serial)
        c.signature = _sign(c.body(), issuer_key)
        return c

    def verify_chain(self, chain, trust_anchors: dict) -> tuple:
        """chain: [leaf, ..., root-ish]. trust_anchors: {name: key}."""
        for i, cert in enumerate(chain):
            if cert.serial in self.revoked:
                return False, f"revoked: {cert.subject}"
            if cert.not_after < time.time():
                return False, f"expired: {cert.subject}"
            issuer_key = trust_anchors.get(cert.issuer)
            if issuer_key is None and i + 1 < len(chain):
                issuer_key = "key-of-" + chain[i + 1].subject
            if issuer_key is None:
                return False, f"unknown issuer: {cert.issuer}"
            if _sign(cert.body(), issuer_key) != cert.signature:
                return False, f"bad signature: {cert.subject}"
        return True, "chain valid"


def demo():
    pki = PKI()
    anchors = {"Root CA": "key-of-Root CA"}
    root = pki.issue("Root CA", "Root CA", "key-of-Root CA", "pub-root", serial=1)
    inter = pki.issue("Inter CA", "Root CA", "key-of-Root CA", "pub-inter", serial=2)
    leaf = pki.issue("example.com", "Inter CA", "key-of-Inter CA", "pub-leaf", serial=3)

    ok, msg = pki.verify_chain([leaf, inter, root], anchors)
    print("valid chain:", ok, "-", msg)
    assert ok

    pki.revoked.add(3)
    ok, msg = pki.verify_chain([leaf, inter, root], anchors)
    print("revoked leaf:", ok, "-", msg)
    assert not ok
    pki.revoked.clear()

    evil = pki.issue("example.com", "Inter CA", "attacker-key", "pub-evil", serial=4)
    ok, msg = pki.verify_chain([evil, inter, root], anchors)
    print("forged cert:", ok, "-", msg)
    assert not ok
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
