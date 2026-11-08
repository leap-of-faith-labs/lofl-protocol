# 03 · Deliberation record · v0.1 (draft)

Licence: CC-BY-SA-4.0 · sha256: see `ledger.json`

## In one sentence

A deliberation record writes down a decision's reasons — for and against — and keeps the disagreement.

## The five fields, all required

| Field | What it holds |
|---|---|
| `position` | What is being proposed or claimed. |
| `evidence` | What supports it. |
| `counter` | The strongest argument against it, written fairly — as its best defender would say it. |
| `consensus` | Where the people deliberating agree. |
| `dissent` | What is still disputed, and by whom (a role, not a served person's name). **Never empty.** If no one disagrees, write who was not asked. |

Plus `scale`: `intra-personal` (one person reasoning with themselves), `team`, or `community`.

## Rules this document makes

- Dissent is kept. It is never averaged, voted away, or deleted.
- A later decision supersedes an earlier record; the earlier record stays readable.
- No field holds a score or a vote count presented as a result.

## Not specified (yet)

- How many people make a "community" deliberation.
- How dissent is attributed when the dissenter wants to stay anonymous.

Supersedes: none (v0.1).
