# 04 · Record envelope · v0.1 (draft)

Licence: CC-BY-SA-4.0 · sha256: see `ledger.json`

## In one sentence

Every LOFL record carries the same small envelope, under the key `lofl`, so a record made by any tool — LOFL's engines, a fork, or by hand — reads the same.

## Fields

| Field | Required | What it holds |
|---|---|---|
| `type` | yes | `promise`, `evidence`, `deliberation`, or `sprint`. |
| `id` | yes | A unique id for this record (a `urn:uuid:` is fine). |
| `parent` | no | The id of the record this one belongs to (for example, the sprint). |
| `created` | yes | Date and time, ISO 8601, with timezone. |
| `license` | yes | Always `CC-BY-SA-4.0`. |
| `provenance.sha256` | yes | The fingerprint of this record (how it is computed is below). |
| `provenance.by` | no | The `did` of whoever made the record. |
| `lang` | no | Language codes of the text, e.g. `["en", "mr"]`. |
| `supersedes` | no | The id of the record this one replaces. |
| `supersededBy` | no | Left empty in the record itself; filled in by whoever renders the chain. |
| `status` | sprint records only | `planned`, `running`, or `completed`. |

## How `provenance.sha256` is computed

1. Take the whole record as JSON.
2. Remove the field `lofl.provenance.sha256` (and `proof`, for a signed promise, since the signature is made after).
3. Write it with keys sorted, no extra spaces (`separators=(",", ":")`), UTF-8.
4. sha256 of those bytes, as 64 lowercase hex characters.

`tools/hash.py --record <file>` does exactly this.

## Rules this document makes

- Nothing is deleted. Corrections are new records with `supersedes`.
- The licence of every record is CC-BY-SA-4.0, whoever made it.
- No envelope field holds personal data about a person being served.

## Not specified (yet)

- Signing records other than promises.
- Where records are stored. A folder of files is enough.

Supersedes: none (v0.1).
