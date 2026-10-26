# Reference changes and library snapshots

## Define the maintained sets

Maintain three related sets explicitly: the broad research library, the manuscript's currently cited subset, and each immutable release snapshot. A work removed from all citation groups leaves the cited subset; it can remain in the research library for future use. A per-version RIS is a text exchange snapshot of a stated set. It is not the live EndNote library and does not update when Word changes. EndNote supports RIS export through its RefMan (RIS) Export style and a separate XML export format. [Clarivate export formats](https://docs.endnote.com/docs/endnote/2025/v1/windows/en/content/15independentbibs_export/supported_formats.htm)

For collaboration, reconcile edits to the native manuscript with edits to the working EndNote library before release. A stale agent registry must not overwrite the author's corrections. Read back the current cited records, map them to source IDs, compare metadata revisions, and resolve conflicts against primary sources.

If the target library cannot be inspected, continue independent work on the embedded native master and its cited-set snapshot. Mark local-library binding and `new_to_target_library` as unverified, not empty. A current exported library inventory may support identity comparison but does not prove native insertion, binding or metadata propagation. Request only the material required for an operation that depends on the target library, while continuing other manuscript work.

## Change operations

| Requested change | Manuscript/library operation | Release effect |
|---|---|---|
| Add a citation to a work already in the library | Reuse that verified record and insert through EndNote | Add/update group; no new library import |
| Add a genuinely new work | Verify metadata, allocate a source ID, check the target library, import only if absent, then insert natively | Add source/group; include only genuinely absent works in an import delta |
| Remove one citation | Remove the intended occurrence with Edit & Manage Citation(s); update | Update group and mention count; source remains cited if used elsewhere |
| Remove all citations to a work | Remove its occurrences and update | Remove from cited snapshot; retain research-library record by default |
| Correct source metadata | Update the verified record and refresh/reconcile its native citation occurrences | Retain source ID; record corrected fields and regenerate snapshots |
| Reorder paragraphs | Move content with its fields intact and update | Retain source/group identities; record new display order and numbering |

Do not delete and reimport a working record simply to change its metadata. EndNote assigns a new record number to a reimported reference, so old numeric identities cannot safely be reused. A library record deleted while still cited may remain visible through Traveling Library; disappearance from the library therefore does not establish removal from the manuscript. [Clarivate reference editing and record numbers](https://docs.endnote.com/docs/endnote/2025/v1/windows/en/content/09word/finding_editing_deleting_ref_library.htm)

Embedded native records and locally bound records can coexist. For an existing embedded-only citation, an edit to a same-DOI record in the local library is not proof that its embedded data changed. Record the actual native update/reinsertion command, target library identity and observed record number, and the before/after value at every affected occurrence, including copies originating from different libraries. Save and reopen, update, and verify the displayed bibliography. If the operation cannot reliably propagate the correction, report that part as incomplete; do not certify a global update from one sample or fabricate a binding. Re-run bounded native tests after substantive citation changes.

Do not routinely Convert to Unformatted Citations as an editing or portability step. It removes Traveling Library and requires corresponding library records for subsequent formatting. [Clarivate unformatting documentation](https://docs.endnote.com/docs/endnote/2025/v1/windows/en/content/09word/unformatting_citations.htm)

## Import deltas rather than repeating the full snapshot

Before import, compare stable source IDs/aliases and verified DOI or alternative identity with the actual target library. A new manuscript citation may already exist there. `added_to_cited_set` and `new_to_target_library` are different sets.

For new works, create a small checked ENW/RIS import delta and record the baseline snapshot/library used to compute it. For corrected existing works, use a change list keyed by stable ID and verified DOI, then update existing records. A reimport is not an upsert and must not be presented as a metadata-refresh mechanism. For removed cited works, list them in the change manifest; do not include library deletion instructions by default.

Full imports are appropriate for a new empty library or a deliberate recovery. Repeatedly importing the full snapshot may create duplicates. EndNote's duplicate options help but depend on metadata-based criteria; they do not replace stable-identity reconciliation and should not be assumed to update an old record. [Clarivate import duplicate handling](https://docs.endnote.com/docs/endnote/2025/v1/windows/en/content/02library/importing_endnote_libs.htm)

Bibliography-level duplicate merging is a separate feature. Its fixed identity criteria include type, authors, year, title, journal, volume, issue and pages; a shared DOI alone does not guarantee merging when those values differ. Reconcile the actual records before interpreting a duplicate bibliography entry. [Clarivate bibliography duplicate rules](https://docs.endnote.com/docs/endnote/2025/v1/windows/en/content/21prefs/formatting.htm)

## Freeze each release

Export the current cited subset after native update and identity reconciliation. Prefer a cited-set RIS plus EndNote XML and the stable mapping; supply per-reference files when requested. Retain metadata-rich registry/provenance for the agent, but do not call it a native `.enl` library. A full working-library backup, when needed and authorized, is distinct from the cited subset and from text export; do not package unrelated personal references or attachments by default.

Record scope, generation source/method, date, counts, stable-ID set and SHA-256 hashes. Label an export produced from verified structured metadata as agent-generated; reserve native-export claims for files actually exported by EndNote. XML exports can include a selected subset and create a new snapshot file rather than a live link. [Clarivate XML export](https://docs.endnote.com/docs/endnote/2025/v1/windows/en/content/15independentbibs_export/exporting_to_endnote_xml.htm)

The change manifest distinguishes added/removed cited IDs, newly imported library IDs, metadata-corrected IDs and changed groups. When all are empty, state that the new version has no reference changes; do not create a misleading import delta. Append the concise result to the manuscript's version history as part of release assembly.

## Snapshot helper boundary

When the project supplies `refresh_snapshot.py`, inspect its actual interface and use it to read the native DOCX plus a verified EndNote XML export, then write the cited snapshot and change report. It is a read-only consumer of those inputs: it neither edits the working library nor inserts citations into Word. Its checks do not replace native application or visual acceptance. An output describing additions to this manuscript's cited set is not a ready-to-import target-library delta; inspect the target library separately before importing any such records.
