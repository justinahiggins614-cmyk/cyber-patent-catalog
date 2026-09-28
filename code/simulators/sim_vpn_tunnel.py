#!/usr/bin/env python3
"""
VPN tunnel simulator (educational).
Covers CPC H04L63/04 / H04L12 (virtual private networks): a shared
secret negotiated per session, every packet encrypted + authenticated
(encapsulated) before crossing the untrusted network, decapsulated
on arrival. Replay window rejects duplicate packets.
"""
import hashlib
import hmac
import os


def _kdf(secret: bytes, label: bytes) -> bytes:
    return hashlib.sha256(label + secret).digest()


class VPNTunnel:
    def __init__(self, psk: bytes):
        self.enc_key = _kdf(psk, b"enc")
        self.mac_key = _kdf(psk, b"mac")
        self.send_seq = 0
        self.recv_window = set()

    def _keystream(self, seq: int, n: int) -> bytes:
        out = b""
        ctr = 0
        while len(out) < n:
            out += hashlib.sha256(self.enc_key + seq.to_bytes(8, "big")
                                  + ctr.to_bytes(4, "big")).digest()
            ctr += 1
        return out[:n]

    def encapsulate(self, plaintext: bytes) -> bytes:
        seq = self.send_seq
        self.send_seq += 1
        ct = bytes(a ^ b for a, b in zip(plaintext, self._keystream(seq, len(plaintext))))
        tag = hmac.new(self.mac_key, seq.to_bytes(8, "big") + ct, hashlib.sha256).digest()[:16]
        return seq.to_bytes(8, "big") + ct + tag

    def decapsulate(self, packet: bytes) -> bytes:
        seq = int.from_bytes(packet[:8], "big")
        ct, tag = packet[8:-16], packet[-16:]
        expect = hmac.new(self.mac_key, packet[:8] + ct, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(tag, expect):
            raise ValueError("auth failed: packet forged or corrupted")
        if seq in self.recv_window:
            raise ValueError("replay rejected")
        self.recv_window.add(seq)
        return bytes(a ^ b for a, b in zip(ct, self._keystream(seq, len(ct))))


def demo():
    alice = VPNTunnel(b"shared-secret")
    bob = VPNTunnel(b"shared-secret")
    pkt = alice.encapsulate(b"GET /secret HTTP/1.1")
    print("tunnel packet:", pkt.hex()[:64], "...")
    print("decapsulated:", bob.decapsulate(pkt))
    assert bob.decapsulate(alice.encapsulate(b"ping")) == b"ping"
    # replay the first packet -> rejected
    try:
        bob.decapsulate(pkt)
        raise AssertionError("replay should have been rejected")
    except ValueError as e:
        print("replay correctly rejected:", e)
    # tamper -> auth fails
    bad = bytearray(alice.encapsulate(b"data"))
    bad[10] ^= 0xFF
    try:
        bob.decapsulate(bytes(bad))
        raise AssertionError("forgery should have failed")
    except ValueError as e:
        print("forgery correctly rejected:", e)
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
