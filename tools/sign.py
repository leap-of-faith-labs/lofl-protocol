#!/usr/bin/env python3
"""LOFL protocol signer · v0.1 · CC-BY-SA-4.0

    python3 tools/sign.py --new-key        make your signing key (once), print your did:key
    python3 tools/sign.py --did            print your did:key
    python3 tools/sign.py FILE             sign a promise: fills your did, the id and the time,
                                           writes the provenance hash, then the proof

Run it on your own computer. The private key lives in ~/.lofl-node/did-key.json
(or the path in LOFL_KEY), never in this folder. Back that file up with the rest
of ~/.lofl-node. If it is lost, your old promises still check, but you cannot
sign as that did again: you make a new key and a new promise that supersedes.

The signature is a W3C Data Integrity proof, cryptosuite eddsa-jcs-2022, from
a did:key (Ed25519). validate.py checks it with no extra packages. Signing needs
the 'cryptography' package (python3 -m pip install cryptography).
"""
import datetime, json, os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import didkey  # noqa: E402
from validate import record_hash, validate_file  # noqa: E402

KEY = os.path.expanduser(os.environ.get("LOFL_KEY", "~/.lofl-node/did-key.json"))
FILL = "fill-on-sign"
PLACEHOLDER_DID = "did:key:" + FILL
WRITE = "WRITE:"


def crypto():
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        return Ed25519PrivateKey, serialization
    except ImportError:
        sys.exit("Signing needs the 'cryptography' package: python3 -m pip install cryptography")


def guard_key_path():
    if os.path.realpath(KEY).startswith(os.path.realpath(ROOT) + os.sep):
        sys.exit(f"The key path {KEY} is inside the protocol folder. Keep the private key out of it.")


def now():
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def new_key():
    guard_key_path()
    if os.path.exists(KEY):
        sys.exit(f"A key already exists at {KEY}. Not overwriting it.\nYour did: {load()[1]}")
    Ed25519PrivateKey, ser = crypto()
    sk = Ed25519PrivateKey.generate()
    seed = sk.private_bytes(ser.Encoding.Raw, ser.PrivateFormat.Raw, ser.NoEncryption())
    pub = sk.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)
    did = didkey.did_from_public(pub)
    os.makedirs(os.path.dirname(KEY), mode=0o700, exist_ok=True)
    fd = os.open(KEY, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump({"kind": "lofl-did-key/v0", "did": did, "created": now(),
                   "ed25519_seed_hex": seed.hex()}, f, indent=2)
        f.write("\n")
    print(f"Key made: {KEY} (only you can read it).\nYour did: {did}\n"
          f"Back up {os.path.dirname(KEY)} now. This did is public; the file is not.")
    return 0


def load():
    if not os.path.exists(KEY):
        sys.exit(f"No key at {KEY}. Make one first: python3 tools/sign.py --new-key")
    with open(KEY) as f:
        k = json.load(f)
    return bytes.fromhex(k["ed25519_seed_hex"]), k["did"]


def unwritten(v, path=""):
    if isinstance(v, str) and v.strip().startswith(WRITE):
        yield path or "the record"
    elif isinstance(v, dict):
        for k, x in v.items():
            yield from unwritten(x, f"{path}.{k}" if path else k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from unwritten(x, f"{path}[{i}]")


def sign(fp):
    guard_key_path()
    Ed25519PrivateKey, ser = crypto()
    seed, did = load()
    sk = Ed25519PrivateKey.from_private_bytes(seed)
    pub = sk.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)
    if didkey.did_from_public(pub) != did:
        sys.exit(f"The key file at {KEY} does not match its own did. Not signing.")

    with open(fp, encoding="utf-8") as f:
        rec = json.load(f)
    left = list(unwritten({k: v for k, v in rec.items() if k != "proof"}))
    if left:
        sys.exit("Not signed. These fields still say WRITE: — fill them in first:\n  - " + "\n  - ".join(left))

    cs = rec.setdefault("credentialSubject", {})
    lofl = rec.setdefault("lofl", {})
    prov = lofl.setdefault("provenance", {})
    for where, get, put in (
        ("issuer", lambda: rec.get("issuer"), lambda v: rec.__setitem__("issuer", v)),
        ("credentialSubject.id", lambda: cs.get("id"), lambda v: cs.__setitem__("id", v)),
        ("lofl.provenance.by", lambda: prov.get("by"), lambda v: prov.__setitem__("by", v)),
    ):
        cur = get()
        if cur in (None, PLACEHOLDER_DID):
            put(did)
        elif cur != did:
            sys.exit(f"{where} is {cur}, but your key is {did}. A promise is signed only by its issuer.")
    if rec.get("id") in (None, "urn:uuid:" + FILL):
        rec["id"] = "urn:uuid:" + str(uuid.uuid4())
    if lofl.get("id") in (None, "urn:uuid:" + FILL):
        lofl["id"] = rec["id"]
    stamp = now()
    if rec.get("validFrom") in (None, FILL):
        rec["validFrom"] = stamp
    if lofl.get("created") in (None, FILL):
        lofl["created"] = stamp

    was_signed = str(rec.get("proof", {}).get("proofValue", "")).startswith("z")
    rec.pop("proof", None)
    prov["sha256"] = record_hash(rec)
    proof = {"type": "DataIntegrityProof", "cryptosuite": "eddsa-jcs-2022", "created": stamp,
             "verificationMethod": didkey.verification_method(did), "proofPurpose": "assertionMethod"}
    if "@context" in rec:
        proof["@context"] = rec["@context"]
    proof["proofValue"] = "z" + didkey.b58encode(sk.sign(didkey.hash_data(rec, proof)))
    rec["proof"] = proof

    tmp = fp + ".signing"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
        f.write("\n")
    _, errs = validate_file(tmp)
    if errs:
        os.remove(tmp)
        sys.exit("Signed, but the record does not pass, so nothing was written:\n  - " + "\n  - ".join(errs))
    os.replace(tmp, fp)
    print(f"Signed {fp}\n  issuer  {did}\n  id      {rec['id']}\n  sha256  {prov['sha256']}")
    if was_signed:
        print("  (It was signed before. Fine while unpublished; once public, change it only by a new "
              "promise that supersedes it.)")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--new-key"]:
        sys.exit(new_key())
    if a == ["--did"]:
        print(load()[1])
        sys.exit(0)
    if len(a) == 1 and not a[0].startswith("-"):
        sys.exit(sign(a[0]))
    print(__doc__)
    sys.exit(1)
