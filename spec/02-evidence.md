# 02 · Evidence · v0.1 (draft)

Licence: CC-BY-SA-4.0 · sha256: see `ledger.json`

## In one sentence

An evidence record says what was done, what it left behind, who checked it and how far, and what happens next.

## The four parts

| Part | Field | What it holds |
|---|---|---|
| Activity | `activity` | What was done, in plain words. |
| Evidence | `evidence` | What it left behind: `kind` (photo, file, log, attendance, artefact, link, other), `pointer` (where it is, or `"private"`), `sha256` (the fingerprint of the thing itself). |
| Verification | `verification` | `level` (L0–L3, below), `by` (the `did` of whoever checked), `promiseId` (the id of the checker's own promise, for L1 and above). |
| Regeneration | `regeneration` | What the practice does next because of this — what is kept, changed or handed on. |

## Verification levels

| Level | Plain words | What must exist |
|---|---|---|
| **L0** | "I say I did it." | The doer's own record. `by` is the doer. |
| **L1** | "Someone else who was there says it happened." | One **assessment-promise**: a promise, self-signed by a witness who is not the doer, saying they observed it, and naming the evidence by its `sha256`. `by` is the witness; `promiseId` is the witness's promise. |
| **L2** | "Someone independent checked it." | An assessment-promise by a witness with no stake in the work (not a colleague, funder or family member of the doer). |
| **L3** | "It meets an outside standard." | Checked against an external framework (for example India's Social Stock Exchange rules), with the framework named. |

`level` is the only field in the whole protocol named "level". It describes *how* something was checked, not *how good* it was.

## Rules this document makes

- Use the lowest level that is enough for what is at stake. Climb only when it matters.
- The evidence itself may stay private. Its `sha256` is enough for a witness to name it.
- No evidence record carries a person-being-served's name, face, voice, or any detail that identifies them.
- A wrong record is corrected by a newer record that supersedes it (see `04-envelope.md`).

## Not specified (yet)

- How a witness proves they were present.
- How L2 independence is checked. In v0.1 the witness states it in their own promise; it is not tested.

Supersedes: none (v0.1).
