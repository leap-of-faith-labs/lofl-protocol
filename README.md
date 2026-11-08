# LOFL Protocol · v0.1.0 (draft)

**Everything in this repository is CC-BY-SA-4.0. The engines that implement it are not here; see CHARTER.md for how they become open.**

## What this is

A plain way to write down good work so anyone can check it:

- **a promise** — a person or organisation saying what *they* will do (never what someone else's outcome will be);
- **evidence** — what was done, what it left behind, and who checked it;
- **a deliberation record** — the reasons for and against, with disagreement kept, never deleted;
- **an envelope** — the few fields every record carries, so records from different tools read the same.

Each has a plain-English spec in `spec/` and a machine schema in `schema/`. **If the two disagree, the plain-English spec is right** and the schema gets fixed.

## The three layers of LOFL

| Layer | What | Rule |
|---|---|---|
| 1. Protocol | this repository | Open now, CC-BY-SA-4.0. Build on it without asking. |
| 2. Engines | the software that runs it | Private until any organisation meets the public gate in CHARTER.md; then open to all. |
| 3. Service | what Leap of Faith Labs runs for organisations | Operated by LOFL, paid. Your records can always leave it as files in this format. |

## Rules every record keeps

- **No numbers that rank.** No field anywhere is called `score`, `rank`, `rating`, `points`, or a `level` other than the evidence verification level (L0–L3). Records are shown together as a set, never sorted into a league.
- **Promises are about yourself.** No one signs another person's promise.
- **Nothing is deleted.** A record is corrected by a newer record that supersedes it.
- **No personal data about the people being served.** No names, photos or details of students, parents, patients or community members — in any field.

## Use it

```
python3 tools/validate.py <folder>   # checks every .json record; prints sentences, not codes
python3 tools/hash.py                # writes ledger.json: every file, its sha256, its licence
python3 tools/hash.py --check        # confirms ledger.json still matches the files
python3 tools/sign.py --new-key      # makes your did:key; the private key stays in ~/.lofl-node
python3 tools/sign.py <promise.json> # signs a promise (eddsa-jcs-2022)
```

Python 3.8+. Checking needs no extra packages: `validate.py` also checks a promise's signature when it is `eddsa-jcs-2022` from a `did:key`. Only signing needs one package, `cryptography`.

## Status

v0.1.0, published 2026-11-08. The specs are drafts: they will change, but only by new versions that supersede this one. Steward until the charter's trigger fires: Leap of Faith Labs (OPC) Private Limited.
