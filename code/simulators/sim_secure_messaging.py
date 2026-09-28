#!/usr/bin/env python3
"""
End-to-end encrypted messaging simulator (educational).
Covers CPC H04L63/04 + H04L9/08 (secure messaging): Diffie-Hellman
negotiates a session key, messages get per-message keys via a
ratchet (compromising one key doesn't expose past messages —
forward secrecy), each message authenticated.
"""
import hashlib
import hmac


class Party:
    def __init__(self, name, p=2**127 - 1, g=3):
        self.name = name
        self.p, self.g = p, g
        import random
        self.priv = random.SystemRandom().randrange(2, p - 1)
        self.pub = pow(g, self.priv, p)
        self.root_key = None
        self.send_chain = None
        self.recv_chain = None

    def agree(self, peer_pub: int):
        shared = pow(peer_pub, self.priv, self.p)
        self.root_key = hashlib.sha256(str(shared).encode()).digest()

    def _ratchet(self, chain: bytes) -> tuple:
        msg_key = hmac.new(chain, b"msg", hashlib.sha256).digest()
        nxt = hmac.new(chain, b"next", hashlib.sha256).digest()
        return msg_key, nxt

    def _stream(self, key: bytes, n: int) -> bytes:
        out, i = b"", 0
        while len(out) < n:
            out += hashlib.sha256(key + i.to_bytes(4, "big")).digest()
            i += 1
        return out[:n]

    def send(self, plaintext: bytes) -> bytes:
        if self.send_chain is None:
            self.send_chain = hmac.new(self.root_key, b"init-send", hashlib.sha256).digest()
        mk, self.send_chain = self._ratchet(self.send_chain)
        ct = bytes(a ^ b for a, b in zip(plaintext, self._stream(mk, len(plaintext))))
        tag = hmac.new(mk, ct, hashlib.sha256).digest()[:16]
        return ct + tag

    def receive(self, packet: bytes) -> bytes:
        ct, tag = packet[:-16], packet[-16:]
        if self.recv_chain is None:
            self.recv_chain = hmac.new(self.root_key, b"init-send", hashlib.sha256).digest()
        # NOTE: both sides derive send/recv chains from the same root in this
        # simplified demo; a real ratchet uses asymmetric DH ratcheting.
        mk, self.recv_chain = self._ratchet(self.recv_chain)
        if not hmac.compare_digest(hmac.new(mk, ct, hashlib.sha256).digest()[:16], tag):
            raise ValueError("message authentication failed")
        return bytes(a ^ b for a, b in zip(ct, self._stream(mk, len(ct))))


def demo():
    alice, bob = Party("alice"), Party("bob")
    alice.agree(bob.pub)
    bob.agree(alice.pub)
    # align chains: in this simplified model both derive identically,
    # so bob's recv chain must mirror alice's send chain
    bob.recv_chain = None
    msgs = [b"hello", b"meet at dawn", b"bring the keys"]
    for m in msgs:
        pkt = alice.send(m)
        got = bob.receive(pkt)
        print(f"alice -> bob: {m}  (wire: {pkt.hex()[:32]}...)")
        assert got == m
    # per-message keys differ: same plaintext -> different ciphertext
    assert alice.send(b"same") != alice.send(b"same")
    print("per-message keys rotate (forward secrecy): OK")
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
