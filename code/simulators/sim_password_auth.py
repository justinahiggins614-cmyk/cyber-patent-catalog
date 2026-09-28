#!/usr/bin/env python3
"""
Password authentication simulator (educational).
Covers CPC G06F21/31 / H04L63/08 (user authentication): per-user
random salts, iterated hashing, constant-time comparison, and
rate-limited login attempts. Demonstrates why plaintext and
unsalted hashes fail.
"""
import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field


def _hash(password: str, salt: bytes, rounds: int = 5000) -> bytes:
    dk = password.encode() + salt
    for _ in range(rounds):
        dk = hashlib.sha256(dk).digest()
    return dk


@dataclass
class AuthServer:
    users: dict = field(default_factory=dict)   # user -> (salt, hash)
    attempts: dict = field(default_factory=dict)

    def register(self, user: str, password: str):
        salt = os.urandom(16)
        self.users[user] = (salt, _hash(password, salt))
        print(f"registered {user} (salt={salt.hex()[:12]}...)")

    def login(self, user: str, password: str) -> bool:
        now = time.time()
        fails, last = self.attempts.get(user, (0, 0))
        if fails >= 5 and now - last < 60:
            print(f"{user}: locked out (too many attempts)")
            return False
        rec = self.users.get(user)
        ok = bool(rec) and hmac.compare_digest(_hash(password, rec[0]), rec[1])
        self.attempts[user] = (0, now) if ok else (fails + 1, now)
        print(f"{user}: {'granted' if ok else 'denied'}")
        return ok


def demo():
    srv = AuthServer()
    srv.register("manon", "s3cur3-p@ss")
    srv.register("alice", "s3cur3-p@ss")  # same password...
    # ...but different salts -> different stored hashes
    assert srv.users["manon"][0] != srv.users["alice"][0]
    assert srv.users["manon"][1] != srv.users["alice"][1]
    print("same password, different hashes (unique salts): OK")
    assert srv.login("manon", "s3cur3-p@ss") is True
    assert srv.login("manon", "wrong") is False
    assert srv.login("nobody", "x") is False
    for _ in range(5):
        srv.login("alice", "wrong")
    assert srv.login("alice", "s3cur3-p@ss") is False  # locked out
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
