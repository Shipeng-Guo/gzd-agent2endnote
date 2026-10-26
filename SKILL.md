---
name: gzd-agent2endnote
description: "Deliver and maintain agent-written manuscripts as genuinely editable EndNote Word documents, with stable source identities, native citation validation and versioned library exports. Use for managed-citation handoff or subsequent reference changes; ordinary prose edits do not require reconversion."
metadata:
  version: "1.0.0"
---

# GZD Agent-to-EndNote

Deliver one usable native Word master and maintain enough source and citation mapping to revise it without depending on old bibliography numbers. This skill works independently for scholarly manuscripts and can provide the reference-management capability for [gzd-review-writing](https://github.com/Shipeng-Guo/gzd-review-writing) when that optional skill is available. Discover the current Word/EndNote tools and installed capabilities rather than assuming a particular host or sibling directory.

## Keep four identities separate

| Identity | Role | Persistence |
|---|---|---|
| Project source ID | Identifies a work throughout research, writing and releases | Immutable; retain aliases if a DOI or metadata is corrected |
| DOI/PMID or verified bibliographic identity | Identifies the published source | Verified external metadata; detect absent/conflicting identifiers |
| EndNote record number and library identity | Identifies a record in a particular library | Record numbers can differ across libraries; read actual values, never invent them |
| Rendered citation number | Displays the citation under the selected style | Recomputed from the current manuscript and style |

An EndNote Label may mirror the project source ID, but a populated Label does not prove that temporary-citation matching works. Keep the source-ID mapping outside proprietary fields. If migrating existing project labels, retain them as aliases rather than replacing all identities.

## Start with sources and citation groups

Before assigning numbered citations, maintain a verified source registry and ordered citation-group map. A source record carries the complete ordered authors, canonical citation metadata, identifiers, provenance and metadata revision. A group has its own stable ID, document scope/location, attached claim, ordered source IDs and any locator/prefix/suffix. Group IDs and paragraph numbers are different: preserve group IDs when text moves, then refresh location/context after editing. Audit that each source supports its attached claim as part of the manuscript's evidence review.

Read [native delivery](references/native-delivery.md) for a first handoff or conversion. Prefer genuine application-generated fields. Text that resembles `{Author, year #…}`, superscript numbers or a valid RIS file is not proof of editable native citations.

For an already working native manuscript, preserve the native master and change citations with EndNote. Do not rebuild or unformat an entire manuscript simply because a new version is being released. Read [library maintenance](references/library-maintenance.md) for additions, removals, metadata changes and snapshots.

## Acceptance and user handoff

The agent performs conversion and tests on owned copies. A normal first handoff is already formatted and verified in the stated application environment: opening the native master and using Update Citations and Bibliography needs no citation initialization there. State untested destination environments separately. Do not shift hundreds of matching confirmations or repeated diagnostic experiments to the author. First-time creation of a personal EndNote library, if desired, is a separate one-time import; an existing matching library should be reused.

If the target library is unavailable, continue work that can be completed using embedded records, including the native master and cited-set snapshot. Do not certify a target-library import difference or local binding without evidence. Obtain the necessary library material only when a requested operation actually depends on it; missing library access must not stop unrelated manuscript work.

Validate the full source set and every citation group, native batch update, style change and return, saved-file reopen, and a disposable editing test. Inspect the final rendered manuscript. Report exact validation scope, including whether actual insertion was tested or an authentic existing field was copied. Embedded Traveling Library data supports portability; it is not proof of binding to a particular local library or of an actual test on another computer.

Each released version needs a dated reference snapshot and a concise change entry: source IDs added, removed from the cited set, or metadata-corrected; group/mention/source counts; manuscript/export hashes; native test and visual-QA status. RIS/XML exports are snapshots, not a live connection to Word. Preserve uncited records in the broader research library unless the user explicitly requests deletion.

If native validation cannot be completed, accurately label the remaining state and preserve completed work. A verified import or temporary-citation draft must not be called a fully editable native master. Keep disposable tests and conversion logs outside the author release.

## Read-only snapshot tool

For native Journal Article citations with verified dedicated DOIs, [scripts/refresh_snapshot.py](scripts/refresh_snapshot.py) extracts the cited set and compares it to a complete EndNote XML export. Read [its supported scope and interface](scripts/README.md) before use. It fails on unrecognised identities or metadata conflicts and never modifies Word or the library. Other reference types or citation stories require a supported extension or an explicit alternative audit; do not drop them to satisfy the helper.

Its extracted group ordinals/locations are snapshot positions, not persistent group identities or scientific claim–source validation. For semantic continuity after a manuscript edit, maintain the claim/unit-to-group mapping and current supported spans separately. When coordinating with an available `gzd-review-writing` skill, use its reference-manager bridge to exchange those evidence mappings; the standalone workflow does not require that skill.
