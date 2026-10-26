# EndNote cited-reference snapshot helper

`refresh_snapshot.py` creates a versioned, read-only reference snapshot from a **saved, genuine EndNote DOCX** and a complete EndNote XML export. It requires Python 3.10+ and `lxml`. It never edits the DOCX, opens Word, writes the EndNote database or imports records. It does not turn placeholder text into native citations.

## Run

```powershell
python refresh_snapshot.py `
  --manuscript "manuscript_native.docx" `
  --library-xml "current_library_export.xml" `
  --previous-registry "previous_version/reference_registry.json" `
  --output-dir "new_version/reference_snapshot"
```

Omit `--previous-registry` for the first snapshot. The output directory must be new or empty; previous releases are never overwritten. The previous registry must use this helper's `endnote-cited-registry/2` schema. Keep the registry alongside each delivered version.

Before running: finish the intended citation edits, update the bibliography in EndNote, save Word, and export the relevant current library as EndNote XML. The XML may include uncited journal papers. A saved native field and its matching exported record must agree in author order, title, year, journal, volume, issue and pages. Only a trailing title period is normalised; substantive inconsistencies block the snapshot. DOI is required as a dedicated field on both sides. Duplicate DOIs or Labels, missing sources, unsupported types and ambiguous identities produce a `validation_report.json` and stop exchange-file generation. Only EndNote **Journal Article type 17** is currently supported.

## Identity and change handling

DOI identifies the current source for matching; it is not the permanent project ID. `stable_id` reuses an existing registry mapping, otherwise adopts a unique existing Label, otherwise generates a `SRC_…` ID once. DOI, Label, any `Rxxx` source alias, first-appearance ordinal, usage count, complete ordered metadata and unmodified record XML remain separate. A library record number is provenance only.

When a corrected DOI retains a unique previous Label, the project ID survives and `changes.json` records `doi_corrected`. If unmatched new DOIs coexist with missing prior identities, the helper refuses to guess whether they are additions/deletions or corrections. After independently checking the source, an agent or author may supply `--identity-decisions decisions.json`:

```json
{
  "schema": "endnote-identity-decisions/1",
  "decisions": [
    {"doi": "10.1234/new-paper", "action": "new", "reason": "Verified distinct paper; cite its source here."},
    {"doi": "10.1234/corrected-doi", "action": "reuse", "stable_id": "existing-project-id", "reason": "Verified DOI correction for the same paper; cite evidence here."}
  ]
}
```

These are illustrative values, not records to import. A reused ID must already exist; identity decisions cannot override a conflicting unique DOI/Label mapping. Never use this option merely to bypass a conflict without checking the source.

## Outputs

| File | Purpose |
|---|---|
| `cited_references.xml` | Complete cloned EndNote records for cited sources, in first-appearance order; preserves all author and export metadata |
| `cited_references.ris` | Journal-article exchange snapshot; each author is a separate AU line; pagination/article IDs are not invented |
| `reference_registry.json` | Permanent project identity, current DOI, aliases, occurrence counts, metadata and provenance |
| `citation_groups.json` | Every body/table citation group and ordered source identity, including inline XML and native outer `fldData` representations |
| `changes.json` | Separate additions, no-longer-cited papers, metadata changes, DOI corrections and uncited library papers |
| `additions_only.ris` | Sources newly cited relative to the prior snapshot; **not necessarily absent from the personal library** |
| `validation_report.json` | Input/output SHA-256 hashes, counts, read-only checks and exact validation scope |

The XML is the complete archival exchange record; RIS does not represent every EndNote-specific field. RIS changes do not synchronize Word or update existing library records automatically. Never re-import the whole snapshot to upgrade metadata, never delete library entries just because they are no longer cited, and check the existing library before importing an additions file. With no previous baseline, `additions_only.ris` contains all cited papers and is not an instruction to import them again.

`metadata_changed` compares full metadata while ignoring local record IDs, database bindings, timestamps, XML indentation and a final title period. The exact record XML is still retained. Changes in source metadata that disagree with native citation records must be deliberately reconciled before a new release.

Only the main document body and tables are ordered here. If native citations occur in footnotes, endnotes, headers or footers, the helper stops rather than silently omitting them. Nested `EN.CITE.DATA` fields are storage helpers and are never double-counted.

The `group` numbers and OOXML paths in `citation_groups.json` describe this snapshot's order and location. They are not persistent semantic group IDs, and the output contains no exact scientific claim span/hash or claim-unit bridge. Keep those mappings in the review evidence records; after text moves, splits or edits, resolve continuity using source identity and actual context rather than an ordinal alone. This helper cannot certify whether a cited paper supports rewritten prose.

## Historical validation

The original implementation was checked in an isolated manuscript project with thirteen static tests. The original test report covered 281 citation groups, 462 mentions, 242 papers and 45 table groups, including both outer-base64 and inline-XML storage. Export-field checks compared complete author order, DOI, LB Label, PMID and bibliographic fields with the source XML; no ID tag substituted for LB. Other cases covered repeat-use deduplication, version differences, DOI correction with stable identity, ambiguity/conflict rejection, missing/duplicate sources, author/page mismatches, no-overwrite behaviour and unchanged source hashes.

These are historical results from private project fixtures, which are not distributed in this repository. They are not evidence that an arbitrary new manuscript or installation has passed. The fixtures changed ordinary XML or already-parsed Python data only and did not manufacture native Word fields. Static snapshot validation and native Word/EndNote formatting or editing acceptance are separate checks; perform the latter in the actual delivery environment.
