#!/usr/bin/env python3
"""LOFL protocol · did:key and eddsa-jcs-2022 helpers · v0.1 · CC-BY-SA-4.0

Shared by validate.py (checking) and sign.py (signing). Standard library only.

- did:key for Ed25519 keys (multicodec 0xed01, base58btc, "z" prefix).
- JCS canonical JSON (RFC 8785) for the records this protocol uses: strings,
  integers, booleans, null, lists and objects. Floats are refused, because the
  protocol has no fractional numbers and JCS number rules are easy to get wrong.
- The eddsa-jcs-2022 hash input (W3C Data Integrity EdDSA Cryptosuites v1.0).
- Ed25519 signature checking, written from RFC 8032 section 6. It only checks;
  it never signs, so it holds no secret and timing does not matter here.
"""
import hashlib, json

# ---------- base58btc ----------
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(b):
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    pad = len(b) - len(b.lstrip(b"\0"))
    return "1" * pad + out


def b58decode(s):
    n = 0
    for c in s:
        i = B58.find(c)
        if i < 0:
            raise ValueError(f"{c!r} is not a base58 character")
        n = n * 58 + i
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\0" * pad + body


# ---------- did:key (Ed25519) ----------
ED25519_PUB = b"\xed\x01"


def did_from_public(pub):
    if len(pub) != 32:
        raise ValueError("an Ed25519 public key is 32 bytes")
    return "did:key:z" + b58encode(ED25519_PUB + pub)


def public_from_did(did):
    """did:key:z6Mk…  or  did:key:z6Mk…#z6Mk…  →  32-byte public key."""
    did = did.split("#", 1)[0]
    if not did.startswith("did:key:z"):
        raise ValueError("not a did:key in base58btc form")
    raw = b58decode(did[len("did:key:z"):])
    if raw[:2] != ED25519_PUB or len(raw) != 34:
        raise ValueError("this did:key is not an Ed25519 key")
    return raw[2:]


def verification_method(did):
    return did + "#" + did[len("did:key:"):]


# ---------- JCS ----------
def _no_floats(v, path="the record"):
    if isinstance(v, float):
        raise ValueError(f"{path} is a fractional number; LOFL records use none.")
    if isinstance(v, dict):
        for k, x in v.items():
            _no_floats(x, f"{path}.{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v):
            _no_floats(x, f"{path}[{i}]")


def jcs(value):
    _no_floats(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


# ---------- eddsa-jcs-2022 ----------
def hash_data(record, proof):
    """The 64 bytes that eddsa-jcs-2022 signs: sha256(proof config) || sha256(document)."""
    doc = {k: v for k, v in record.items() if k != "proof"}
    config = {k: v for k, v in proof.items() if k != "proofValue"}
    if "@context" in doc:
        config["@context"] = doc["@context"]
    return hashlib.sha256(jcs(config)).digest() + hashlib.sha256(jcs(doc)).digest()


# ---------- Ed25519 verify (RFC 8032 §6) ----------
_p = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _recover_x(y, sign):
    if y >= _p:
        return None
    x2 = (y * y - 1) * pow(_d * y * y + 1, _p - 2, _p) % _p
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_p + 3) // 8, _p)
    if (x * x - x2) % _p:
        x = x * _I % _p
    if (x * x - x2) % _p:
        return None
    if (x & 1) != sign:
        x = _p - x
    return x


def _add(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % _p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % _p
    C = 2 * P[3] * Q[3] * _d % _p
    D = 2 * P[2] * Q[2] % _p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _p, G * H % _p, F * G % _p, E * H % _p)


def _mul(s, P):
    Q = (0, 1, 1, 0)
    while s:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _equal(P, Q):
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _decompress(b):
    if len(b) != 32:
        return None
    y = int.from_bytes(b, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % _p)


_gy = 4 * pow(5, _p - 2, _p) % _p
_gx = _recover_x(_gy, 0)
_G = (_gx, _gy, 1, _gx * _gy % _p)


def ed25519_verify(pub, msg, sig):
    if len(pub) != 32 or len(sig) != 64:
        return False
    A = _decompress(pub)
    R = _decompress(sig[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= _L:
        return False
    h = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(), "little") % _L
    return _equal(_mul(s, _G), _add(R, _mul(h, A)))


def check_proof(record):
    """Return a list of plain sentences; empty means the signature is good."""
    proof = record.get("proof") or {}
    vm = proof.get("verificationMethod", "")
    issuer = record.get("issuer", "")
    if proof.get("cryptosuite") != "eddsa-jcs-2022" or not vm.startswith("did:key:"):
        return None  # a kind of signature this tool cannot check
    errs = []
    if vm.split("#", 1)[0] != issuer:
        errs.append("proof.verificationMethod is not the issuer's key — only the issuer signs a promise.")
    try:
        pub = public_from_did(vm)
    except ValueError as e:
        return errs + [f"proof.verificationMethod: {e}."]
    pv = proof.get("proofValue", "")
    if not pv.startswith("z"):
        return errs + ["proof.proofValue must be base58btc (start with 'z')."]
    try:
        sig = b58decode(pv[1:])
        data = hash_data(record, proof)
    except ValueError as e:
        return errs + [f"the signature could not be read ({e})."]
    if not ed25519_verify(pub, data, sig):
        errs.append("the signature does not match — the record changed after signing, or it was "
                    "not signed by this key (run: python3 tools/sign.py <file>).")
    return errs
