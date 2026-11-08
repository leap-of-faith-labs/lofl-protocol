#!/usr/bin/env python3
"""LOFL protocol validator · v0.1 · CC-BY-SA-4.0

    python3 tools/validate.py <folder-or-file> [...]

Checks every .json record against the LOFL schemas and the protocol's rules,
and checks a promise's signature when it is eddsa-jcs-2022 from a did:key.
Prints one plain sentence per problem. Exit code 0 = all pass, 1 = something failed.
No extra packages needed (it implements the small part of JSON Schema the LOFL schemas use).
"""
import hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import didkey  # noqa: E402  (same folder; standard library only)
SCHEMA_DIR = os.path.join(HERE, "..", "schema")
FORBIDDEN = {"score", "scores", "rank", "ranking", "rating", "ratings", "points", "leaderboard"}


def load_schemas():
    out = {}
    for name in ("envelope", "promise", "evidence", "deliberation"):
        with open(os.path.join(SCHEMA_DIR, f"{name}.schema.json"), encoding="utf-8") as f:
            out[f"{name}.schema.json"] = json.load(f)
    return out


SCHEMAS = load_schemas()
TYPES = {"string": str, "object": dict, "array": list, "boolean": bool, "null": type(None)}


def is_type(v, t):
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    return isinstance(v, TYPES[t])


def check(value, schema, path, errs):
    if "$ref" in schema:
        return check(value, SCHEMAS[schema["$ref"]], path, errs)
    where = path or "the record"
    if "const" in schema and value != schema["const"]:
        errs.append(f"{where} must be exactly {schema['const']!r}, but it is {value!r}.")
        return
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{where} must be one of {', '.join(map(str, schema['enum']))}, but it is {value!r}.")
        return
    t = schema.get("type")
    if t:
        ts = t if isinstance(t, list) else [t]
        if not any(is_type(value, x) for x in ts):
            errs.append(f"{where} should be {' or '.join(ts)}, but it is {type(value).__name__}.")
            return
    if isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            errs.append(f"{where} is empty; it must say something.")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append(f"{where} is not in the expected form ({value!r}).")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                errs.append(f"{where} is missing the required field '{k}'.")
        props = schema.get("properties", {})
        for k, v in value.items():
            p = f"{path}.{k}" if path else k
            if k in props:
                check(v, props[k], p, errs)
            elif schema.get("additionalProperties") is False:
                errs.append(f"{p} is not a field the protocol allows here.")
    if isinstance(value, list) and "items" in schema:
        for i, v in enumerate(value):
            check(v, schema["items"], f"{path}[{i}]", errs)


def forbidden_keys(value, path, errs):
    if isinstance(value, dict):
        for k, v in value.items():
            p = f"{path}.{k}" if path else k
            if k.lower() in FORBIDDEN:
                errs.append(f"{p}: the protocol has no '{k}' field — nothing is scored or ranked.")
            if k.lower() == "level" and not path.endswith("verification"):
                errs.append(f"{p}: 'level' is only allowed as the evidence verification level (L0–L3).")
            forbidden_keys(v, p, errs)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            forbidden_keys(v, f"{path}[{i}]", errs)


def record_hash(rec):
    r = json.loads(json.dumps(rec))
    r.pop("proof", None)
    r.get("lofl", {}).get("provenance", {}).pop("sha256", None)
    b = json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def which_schema(rec):
    if isinstance(rec, dict) and "credentialSubject" in rec:
        return "promise.schema.json"
    t = rec.get("lofl", {}).get("type") if isinstance(rec, dict) else None
    return {"evidence": "evidence.schema.json", "deliberation": "deliberation.schema.json",
            "promise": "promise.schema.json"}.get(t)


def validate_file(fp):
    errs = []
    try:
        with open(fp, encoding="utf-8") as f:
            rec = json.load(f)
    except Exception as e:
        return None, [f"it is not readable JSON ({e})."]
    if not isinstance(rec, dict):
        return None, ["a record must be a JSON object."]
    name = which_schema(rec)
    if name:
        check(rec, SCHEMAS[name], "", errs)
    elif rec.get("lofl", {}).get("type") == "sprint":
        name = "envelope.schema.json (sprint)"
        check(rec.get("lofl"), SCHEMAS["envelope.schema.json"], "lofl", errs)
    else:
        return None, ["it is not a LOFL record (no 'lofl' envelope with a known type)."]
    forbidden_keys(rec, "", errs)
    if name.startswith("promise"):
        cs = rec.get("credentialSubject", {})
        if rec.get("issuer") and cs.get("id") and rec["issuer"] != cs["id"]:
            errs.append("issuer and credentialSubject.id differ — a promise can only be about the issuer.")
        if rec.get("lofl", {}).get("type") not in (None, "promise"):
            errs.append("lofl.type must be 'promise' for a promise.")
        if isinstance(rec.get("proof"), dict):
            proof_errs = didkey.check_proof(rec)
            if proof_errs is None:
                name += "; signature not checked — this tool checks eddsa-jcs-2022 from a did:key"
            else:
                errs += proof_errs
                if not proof_errs:
                    name += "; signature good"
    if name.startswith("evidence"):
        v = rec.get("verification", {})
        if v.get("level") in ("L1", "L2", "L3") and not v.get("promiseId"):
            errs.append(f"verification at {v.get('level')} needs promiseId — the witness's own promise.")
    stated = rec.get("lofl", {}).get("provenance", {}).get("sha256")
    if stated and stated != record_hash(rec):
        errs.append("lofl.provenance.sha256 does not match the record — it changed after hashing "
                    "(run: python3 tools/hash.py --record <file> --write).")
    return name, errs


def main(args):
    if not args:
        print(__doc__)
        return 1
    files = []
    for a in args:
        if os.path.isdir(a):
            for dp, dn, fn in os.walk(a):
                dn[:] = [d for d in dn if not d.startswith(".")]
                files += [os.path.join(dp, f) for f in sorted(fn) if f.endswith(".json")]
        else:
            files.append(a)
    if not files:
        print("No .json records found.")
        return 1
    bad = 0
    for fp in files:
        name, errs = validate_file(fp)
        if errs:
            bad += 1
            print(f"✗ {fp}" + (f"  (checked as {name})" if name else ""))
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"✓ {fp}  (matches {name})")
    print()
    print(f"All {len(files)} records pass." if not bad else f"{bad} of {len(files)} records need fixing.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
