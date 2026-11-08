#!/usr/bin/env python3
"""LOFL protocol hasher · v0.1 · CC-BY-SA-4.0

    python3 tools/hash.py                     write ledger.json: every file, its sha256, bytes, licence
    python3 tools/hash.py --check             confirm ledger.json still matches every file
    python3 tools/hash.py --record FILE       print a record's provenance hash (spec/04-envelope.md)
    python3 tools/hash.py --record FILE --write   ...and write it into lofl.provenance.sha256

Run from the protocol folder. No extra packages needed.
"""
import hashlib, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LEDGER = os.path.join(ROOT, "ledger.json")
SKIP_DIRS = {".git", "__pycache__", "test-fixtures"}
SKIP_FILES = {"ledger.json", ".DS_Store", "START-HERE.md"}  # START-HERE: the steward's working note, kept beside the repo, not published


def files():
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = sorted(d for d in dn if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(fn):
            if f in SKIP_FILES or f.endswith(" alias"):
                continue
            yield os.path.relpath(os.path.join(dp, f), ROOT)


def sha(path):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, path), "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def build():
    rows = [{"path": p, "sha256": sha(p), "bytes": os.path.getsize(os.path.join(ROOT, p)),
             "license": "CC-BY-SA-4.0"} for p in files()]
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump({"protocol": "lofl-protocol", "files": rows}, f, indent=2)
        f.write("\n")
    print(f"ledger.json written: {len(rows)} files.")
    return 0


def check():
    if not os.path.exists(LEDGER):
        print("There is no ledger.json yet. Run: python3 tools/hash.py")
        return 1
    with open(LEDGER, encoding="utf-8") as f:
        led = {r["path"]: r["sha256"] for r in json.load(f)["files"]}
    now = set(files())
    bad = 0
    for p in sorted(now | set(led)):
        if p not in led:
            print(f"✗ {p} is new and not in the ledger."); bad += 1
        elif p not in now:
            print(f"✗ {p} is in the ledger but missing from the folder."); bad += 1
        elif sha(p) != led[p]:
            print(f"✗ {p} has changed since the ledger was written."); bad += 1
    print("The ledger matches every file." if not bad else f"{bad} differences. Re-run hash.py after checking them.")
    return 1 if bad else 0


def record(fp, write):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from validate import record_hash
    with open(fp, encoding="utf-8") as f:
        rec = json.load(f)
    h = record_hash(rec)
    print(h)
    if write:
        rec.setdefault("lofl", {}).setdefault("provenance", {})["sha256"] = h
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Written into {fp}.")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--check" in a:
        sys.exit(check())
    if "--record" in a:
        i = a.index("--record")
        sys.exit(record(a[i + 1], "--write" in a))
    sys.exit(build())
