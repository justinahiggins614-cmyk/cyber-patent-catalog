#!/usr/bin/env python3
"""
WPA2 4-way handshake simulator (educational).
Covers CPC H04W12/06 (wireless authentication): from a pre-shared
key and nonces, both sides derive the Pairwise Transient Key (PTK),
confirm it with message integrity codes, and install it — without
ever transmitting the PSK itself.
"""
import hashlib
import hmac


def prf(key: bytes, label: bytes, data: bytes, out_len: int = 64) -> bytes:
    out = b""
    i = 0
    while len(out) < out_len:
        out += hmac.new(key, label + bytes([i]) + data, hashlib.sha256).digest()
        i += 1
    return out[:out_len]


def mic(key: bytes, msg: bytes) -> str:
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:32]


def demo():
    psk = b"correct-horse-battery-staple"
    pmk = hashlib.sha256(b"PMK" + psk).digest()          # normally PBKDF2; simplified
    anonce = bytes.fromhex("aa" * 32)                    # AP nonce
    snonce = bytes.fromhex("bb" * 32)                    # client nonce
    ap_mac, cli_mac = b"AP-MAC-00", b"CLI-MAC-00"

    # Both sides derive the same PTK from PMK + nonces + MACs
    data = min(anonce, snonce) + max(anonce, snonce) + min(ap_mac, cli_mac) + max(ap_mac, cli_mac)
    ptk_ap = prf(pmk, b"Pairwise key expansion", data)
    ptk_cli = prf(pmk, b"Pairwise key expansion", data)
    print("PTK match:", ptk_ap == ptk_cli)
    assert ptk_ap == ptk_cli

    kck = ptk_ap[:16]  # key confirmation key
    # Message 2: client proves it derived the PTK via MIC over its SNonce
    m2_mic = mic(kck, b"msg2" + snonce)
    assert mic(kck, b"msg2" + snonce) == m2_mic
    print("message 2 MIC verified:", m2_mic)
    # Attacker without the PSK derives a different PTK -> MIC fails
    evil_pmk = hashlib.sha256(b"PMK" + b"wrong-password").digest()
    evil_ptk = prf(evil_pmk, b"Pairwise key expansion", data)
    assert evil_ptk != ptk_ap
    assert mic(evil_ptk[:16], b"msg2" + snonce) != m2_mic
    print("attacker with wrong PSK: MIC rejected")
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
