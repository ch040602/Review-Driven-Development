<!-- review-driven-development:context-bootstrap:begin -->
## review-driven-development fast context

Before planning or editing in this repository:
- Run `python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary` when `.codex/review-driven-development/context-pack.md` is missing or stale.
- Read `.codex/review-driven-development/context-pack.md` before opening broad source trees.
- Run `python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search "<query>"` to rank likely files before broad search.
- Use `.codex/review-driven-development/context-semantic-index.json` for file, symbol, term, and optional dense-vector lookup.
- Default ranking uses scikit-learn TF-IDF when installed, then lexical overlap; dense sentence-transformers ranking is opt-in with `--embeddings`.
- Open the full source files referenced by the active TODO before editing; the semantic index is a locator, not proof.
- Keep validation evidence, independent review, and documentation status in the TODO ledger before completion.
<!-- review-driven-development:context-bootstrap:end -->
