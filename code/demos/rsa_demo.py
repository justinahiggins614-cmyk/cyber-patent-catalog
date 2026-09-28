#!/usr/bin/env python3
"""
RSA public-key cryptosystem — working demonstration.
Related patent: US 4,405,829 "Cryptographic Communications System and
Method" (Rivest, Shamir, Adleman / MIT). Patent expired 2000; the
algorithm is public domain. Educational demo with small primes —
NOT for real security.
"""


def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def modinv(a, m):
    g, x, _ = egcd(a, m)
    assert g == 1, "no modular inverse"
    return x % m


def rsa_demo(p=61, q=53, e=17, message=65):
    n = p * q
    phi = (p - 1) * (q - 1)
    d = modinv(e, phi)
    print(f"Primes p={p}, q={q}")
    print(f"Modulus n = p*q = {n}")
    print(f"Public key:  (e={e}, n={n})")
    print(f"Private key: (d={d}, n={n})")

    c = pow(message, e, n)          # encrypt with public key
    m = pow(c, d, n)               # decrypt with private key
    print(f"Plaintext {message} -> ciphertext {c} -> decrypted {m}")
    assert m == message, "RSA round-trip failed"
    print("Round-trip OK: only the private-key holder can decrypt.")
    return c, m


if __name__ == "__main__":
    rsa_demo()
    print("Self-test: PASS")
