#!/usr/bin/env python3
"""
DDoS mitigation simulator (educational).
Covers CPC H04L63/14 (denial-of-service defense): token-bucket rate
limiter per source IP plus a global SYN-flood detector. Legitimate
clients pass; flooding sources get throttled then blackholed.
"""
import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    rate: float      # tokens per second
    capacity: float
    tokens: float = 0
    last: float = 0

    def allow(self, now: float) -> bool:
        if self.last == 0:
            self.last = now
            self.tokens = self.capacity
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


@dataclass
class DDoSMitigator:
    per_ip_rate: float = 20.0
    buckets: dict = field(default_factory=dict)
    blacklist: set = field(default_factory=set)
    violations: dict = field(default_factory=dict)

    def handle(self, src: str, now: float) -> str:
        if src in self.blacklist:
            return "DROP (blacklisted)"
        bucket = self.buckets.setdefault(
            src, TokenBucket(rate=self.per_ip_rate, capacity=self.per_ip_rate))
        if bucket.allow(now):
            self.violations[src] = 0
            return "ALLOW"
        self.violations[src] = self.violations.get(src, 0) + 1
        if self.violations[src] >= 5:
            self.blacklist.add(src)
            return "DROP (blacklisted: flood detected)"
        return "DROP (rate limited)"


def demo():
    fw = DDoSMitigator(per_ip_rate=10.0)
    t = 1000.0
    # legitimate client: 5 requests, well spaced
    legit = [fw.handle("10.0.0.5", t + i * 0.5) for i in range(5)]
    print("legit client:", legit)
    assert all(v == "ALLOW" for v in legit)
    # attacker: 60 requests in 1 second
    results = [fw.handle("203.0.113.9", t + i * 0.016) for i in range(60)]
    allowed = sum(1 for v in results if v == "ALLOW")
    print(f"attacker: {allowed}/60 allowed, final verdict: {results[-1]}")
    assert allowed <= 12, "rate limiter must throttle the flood"
    assert "blacklisted" in results[-1]
    # blacklisted source stays dropped
    assert fw.handle("203.0.113.9", t + 100) == "DROP (blacklisted)"
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
