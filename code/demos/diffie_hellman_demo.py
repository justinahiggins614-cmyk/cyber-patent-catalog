#!/usr/bin/env python3
"""
Diffie-Hellman-Merkle key exchange — working demonstration.
Related patent: US 4,200,770 "Cryptographic Apparatus and Method"
(Hellman, Diffie, Merkle / Stanford). Patent expired 1997; the
algorithm is public domain. This is an educational demo with a
small prime — NOT for real security.
"""
import hashlib


def dh_demo(p: int = 23, g: int = 5, alice_secret: int = 6, bob_secret: int = 15):
    # Public parameters (agreed openly)
    print(f"Public prime p = {p}, generator g = {g}")

    # Each side picks a private secret
    A = pow(g, alice_secret, p)  # Alice's public value
    B = pow(g, bob_secret, p)    # Bob's public value
    print(f"Alice sends A = g^a mod p = {A}")
    print(f"Bob   sends B = g^b mod p = {B}")

    # Each side computes the shared secret from the other's public value
    alice_shared = pow(B, alice_secret, p)
    bob_shared = pow(A, bob_secret, p)
    print(f"Alice computes shared = B^a mod p = {alice_shared}")
    print(f"Bob   computes shared = A^b mod p = {bob_shared}")

    assert alice_shared == bob_shared, "shared secrets must match"
    key = hashlib.sha256(str(alice_shared).encode()).hexdigest()[:32]
    print(f"Shared secret established: {alice_shared}")
    print(f"Derived session key (SHA-256, truncated): {key}")
    print("An eavesdropper sees only p, g, A, B — recovering the")
    print("secret requires solving the discrete logarithm problem.")
    return alice_shared


if __name__ == "__main__":
    dh_demo()
    print("\nSelf-test: PASS")
