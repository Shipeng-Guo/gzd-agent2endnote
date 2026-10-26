# Changelog

## 1.0.0 — 2026-10-26

First English public release under the name `gzd-agent2endnote`, continuing the earlier `agent-endnote` skill.

- Updated the skill identity and added English invocation metadata, installation instructions, and examples.
- Made the review-writing integration optional and removed the assumption of a sibling directory.
- Preserved native-field verification, stable source and citation-group identities, library reconciliation, and cited-set snapshot boundaries.
- Retained `scripts/refresh_snapshot.py` without algorithm changes. Its registry schema remains `endnote-cited-registry/2` for compatibility with existing snapshots.
- Generalized project-specific example filenames and separated historical private-fixture validation from acceptance of a new manuscript.

This release changes packaging and instructions. It does not claim a new native Word/EndNote application test or expanded snapshot-parser coverage.
