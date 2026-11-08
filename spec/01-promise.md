# 01 · Promise · v0.1 (draft)

Licence: CC-BY-SA-4.0 · sha256: see `ledger.json`

## In one sentence

A promise is a signed statement, by one person or organisation, about **their own** behaviour — with the evidence it rests on and the reasons against it written down.

## The rule underneath

You can only promise about yourself. You cannot promise what a student will learn or what a village will do. You can promise what *you* will do, and show what you did. No one else signs your promise — not a funder, not LOFL, not a witness.

## The Core — seven fields, all required

| # | Field | What it holds |
|---|---|---|
| 1 | `issuer` | Who is promising: a `did:` identifier the issuer controls (did:key recommended). |
| 2 | `credentialSubject.claim` | The promise itself. One clear statement about the issuer's own behaviour. |
| 3 | `credentialSubject.evidencePointer` | What grounds the claim: `trace` (a link or a hash of the thing the issuer holds), optional `irisNoun` (an IRIS+ metric name, as a noun), optional `sdg` (a list of SDG targets, e.g. `"4.4"`). |
| 4 | `credentialSubject.selfDeliberation` | The reasons, in five parts — Position, Evidence, Counter, Consensus, Dissent — as in `03-deliberation.md`. Dissent may not be empty. |
| 5 | `validFrom` + `credentialSubject.cycle` | When it was issued, and which cycle or season it belongs to. |
| 6 | `proof` | The issuer's own signature over everything above. |
| 7 | `credentialSubject.supersedes` | The id of the promise this one replaces, or `null`. A promise that is later replaced gets a `supersededBy` pointer **in the newer record's chain**, never an edit to the old one. |

The Core is complete on its own. One person, alone, can make one.

## Shape

A promise is a W3C Verifiable Credential (v2) that the issuer issues **about themselves**: `issuer` and `credentialSubject.id` are the same.

```json
{
  "@context": ["https://www.w3.org/ns/credentials/v2"],
  "type": ["VerifiableCredential", "LOFLPromise"],
  "id": "urn:uuid:…",
  "issuer": "did:key:z6Mk…",
  "validFrom": "2026-10-24T18:00:00+05:30",
  "credentialSubject": {
    "id": "did:key:z6Mk…",
    "claim": "I will …",
    "cycle": "2026-Q4",
    "evidencePointer": { "trace": "sha256:…", "irisNoun": "…", "sdg": ["4.4"] },
    "selfDeliberation": { "position": "…", "evidence": "…", "counter": "…", "consensus": "…", "dissent": "…" },
    "supersedes": null
  },
  "proof": { "type": "DataIntegrityProof", "cryptosuite": "eddsa-jcs-2022", "verificationMethod": "did:key:z6Mk…#z6Mk…", "proofPurpose": "assertionMethod", "proofValue": "z…" },
  "lofl": { "…": "the envelope — see 04-envelope.md" }
}
```

## The Envelope — optional, wraps the Core

Two different things share the word "envelope". The **promise envelope** (this section) sits under the key `envelope` and is about coordination. The **record envelope** (`04-envelope.md`) sits under the key `lofl` and is the bookkeeping every record carries.

- `presentation` — what the issuer chooses to show, and to whom.
- `complements` — ids of other people's promises that fit with this one ("I will fund X" ↔ "I will do X"). This is how an exchange works here: promises that fit, with no price.
- `assessments` — ids of witnesses' **own** promises about having seen this one. A witness never signs your promise; they sign their own, and link to yours.

A promise may have a Core and no Envelope. It may never have an Envelope and no Core.

## Rules this document makes

- The claim is about the issuer's own behaviour. A claim about someone else's outcome is not a promise.
- No field holds personal data about a person being served. If the evidence would show one, point at a hash of it instead.
- No field holds a score, rank or rating.
- A promise with no evidence pointer is allowed but is plain testimony; the trace field must then say `"none — testimony only"`.

## Not specified (yet)

- Where a `did` is kept, and how a lost key is recovered.
- Which signature tool to use; any tool that produces a W3C Data Integrity proof will do. This repository ships one: `tools/sign.py` makes an `eddsa-jcs-2022` proof from a `did:key` (Ed25519), and `tools/validate.py` checks proofs of that kind. It was tested against the W3C test vectors.
- Public anchoring (for example a Merkle root on a public chain). Optional, outside v0.1.

Supersedes: none (v0.1).
