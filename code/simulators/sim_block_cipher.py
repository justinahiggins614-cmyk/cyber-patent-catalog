#!/usr/bin/env python3
"""
Feistel block cipher simulator (educational).
Covers CPC H04L9/06 (block ciphers: DES/AES family concepts).
NOT real crypto — demonstrates the Feistel structure every
block-cipher patent builds on: split block, round function,
swap, repeat; decryption runs rounds in reverse.
"""
import hashlib


def _round_key(master: bytes, rnd: int) -> int:
    return int.from_bytes(hashlib.sha256(master + bytes([rnd])).digest()[:4], "big")


def _f(half: int, key: int) -> int:
    # toy round function: keyed mixing of a 32-bit half-block
    x = (half ^ key) & 0xFFFFFFFF
    x = ((x << 7) | (x >> 25)) & 0xFFFFFFFF  # rotate
    x = (x * 0x9E3779B1) & 0xFFFFFFFF        # avalanche multiply
    return x ^ (x >> 16)


def encrypt_block(block: bytes, key: bytes, rounds: int = 8) -> bytes:
    assert len(block) == 8
    left = int.from_bytes(block[:4], "big")
    right = int.from_bytes(block[4:], "big")
    for r in range(rounds):
        left, right = right, left ^ _f(right, _round_key(key, r))
    return left.to_bytes(4, "big") + right.to_bytes(4, "big")


def decrypt_block(block: bytes, key: bytes, rounds: int = 8) -> bytes:
    assert len(block) == 8
    left = int.from_bytes(block[:4], "big")
    right = int.from_bytes(block[4:], "big")
    for r in reversed(range(rounds)):
        left, right = right ^ _f(left, _round_key(key, r)), left
    return left.to_bytes(4, "big") + right.to_bytes(4, "big")


def demo():
    key = b"demo-key-16-bytes!"
    pt = b"SECRETM!"
    ct = encrypt_block(pt, key)
    rt = decrypt_block(ct, key)
    print(f"plaintext : {pt}")
    print(f"ciphertext: {ct.hex()}")
    print(f"recovered : {rt}")
    assert rt == pt
    # flipping one plaintext bit avalanches the ciphertext
    pt2 = b"SECRETM\""
    ct2 = encrypt_block(pt2, key)
    diff = bin(int.from_bytes(ct, "big") ^ int.from_bytes(ct2, "big")).count("1")
    print(f"1-bit plaintext flip -> {diff}/64 ciphertext bits changed (avalanche)")
    assert diff > 20
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
