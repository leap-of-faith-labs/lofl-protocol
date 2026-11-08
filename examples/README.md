# examples/

The first public example is **M's own real promise** (publish guide, step 4): a real record with a real signature, or the protocol launches as a drawing.

`promise-m-2026-11.json` starts as a blank form. To fill and sign it, on your own computer:

1. Replace every `WRITE:` text. Leave the `fill-on-sign` values alone.
2. `python3 tools/sign.py --new-key` (once). Your key goes in `~/.lofl-node/`, never in this folder.
3. `python3 tools/sign.py examples/promise-m-2026-11.json`. This fills in your did, the id and the time, writes the hash, then signs. It will not sign while any `WRITE:` is left.
4. `python3 tools/validate.py examples` must end with "All N records pass." The promise line must say "signature good".

After it is public, never edit it. A change is a new promise with `supersedes` set to this one's id.

Synthetic test records live in `tools/test-fixtures/` and are never published as examples.
