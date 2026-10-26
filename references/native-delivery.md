# Native delivery and validation

## Data prepared while writing

Use one project registry rather than reconstructing references from a rendered bibliography. Preserve full supplied names, suffixes, collective authors and diacritics; do not infer missing full names. Keep journal, year, volume, issue and pages/article number as separate fields. Verify DOI and PMID independently where available. Record absent fields as absent, not guessed.

Minimum reusable records:

| Record | Required content |
|---|---|
| Source | `source_id`, aliases/Label, type, ordered authors, title, journal, year, volume, issue, pages/article number, identifiers, provenance, metadata revision |
| Citation group | `group_id`, manuscript scope, ordered source IDs, claim/location context, optional locator/prefix/suffix |
| Library mapping | `source_id`, observed library identity and record number, observed metadata hash and date; null when unbound |
| Release snapshot | version, cited-source set, counts, file hashes, change categories, validation scope |

DOI normalization supports comparisons, but do not silently merge distinct versions of a work or replace an immutable source ID when correcting a DOI. Paragraph indices, XML paths and bookmarks are location evidence, not universal permanent addresses. Re-identify groups after edits and fail on ambiguous matches.

## Produce native fields

Native EndNote insertion is preferred when it can be executed reliably. For an agent-generated manuscript, another supported batch route is to populate genuine Word bibliographic Sources and Word CITATION fields, then run the installed EndNote **Convert Word Citations to EndNote** command and native formatting. The official feature distinguishes Word Sources from EndNote CWYW fields. [Clarivate conversion documentation](https://docs.endnote.com/docs/endnote/2025/v1/windows/en/content/09word/convrting_word_citestoen.htm)

Use exact source/group maps and a reversible intermediate; verify that replacing citations has not altered scientific prose, tables or graphics. In the observed EndNote 2025 project, input containing Sources plus CITATION fields and no Word BIBLIOGRAPHY field converted successfully; EndNote created the final bibliography afterward. This is a tested implementation choice for that environment, not a universal rule about valid Word documents. Application commands and automation entry points must be verified for the installed version.

The final document must contain genuine application-created citation and bibliography fields. Do not write invented EN.CITE shells, assign guessed record numbers or fabricate database IDs. A generated import with valid syntax and a visually correct numbered bibliography do not establish native editability.

## Inspect actual embedded records

EndNote native fields carry the cited reference data used by Traveling Library. This is why a formatted document can be used when the original library is unavailable. Notes, Research Notes, Abstract, Figure and Caption are excluded from ordinary Traveling Library data; an identifier copied into Notes alone is therefore insufficient. Clarivate recommends preserving the fields and avoiding direct field-code edits. [Clarivate field-code documentation](https://docs.endnote.com/docs/endnote/2025/v1/windows/en/content/09word/field_codes.htm)

Inspect every occurrence against the source registry, including tables, legends and supplement scopes. The observed version stored records both as inline XML and nested encoded EN.CITE.DATA; an audit that reads only inline records is incomplete. Compare complete ordered authors and bibliographic fields, plus dedicated DOI, URL, Label and PMID when available. Distinguish metadata completeness from whether the chosen style displays it.

If a converter omits metadata, prefer native record correction or reinsertion. Direct metadata repair is an exceptional controlled operation on a copy of fields already created by EndNote, not the normal construction route and not an official API. Preserve native structure and identities; change only independently verified missing/corrected data and verify every affected occurrence. Prove EndNote consumes it through native formatting using a style that displays the relevant field. That result does not establish local-library binding or prove that later library updates cannot overwrite the repair. If preservation or native verification is unavailable, leave the gap explicit instead of declaring the handoff complete.

## Acceptance checks

1. Verify import records against primary metadata and, if imported, export back for comparison. Export-XML DTD validity does not validate the different CWYW storage schema.
2. Audit every native group against its expected ordered source IDs, including multiple citations and table cells. Check unique cited sources, mentions and bibliographies; remove no legitimate multi-bibliography structure merely to force one count.
3. Update the whole manuscript through EndNote without per-reference matching. Switch to a diagnostic style that reveals required metadata and return to the intended style.
4. Save, close, reopen in a fresh application instance and update. Test a disposable copy with addition, removal, duplicate-source handling and surviving-source renumbering. Report exactly how addition was exercised.
5. Compare non-citation text and display items with the intended source; render the final file and inspect all pages. Bind the tests and visual review to the final file hash.

Use a task-owned document/application instance when available, leaving live user documents and the working library intact during tests. Stop repeated identical stalled calls; inspect the actual file state before choosing a bounded alternative. Automation failure alone does not diagnose an application or licensing defect.

## First delivery

Deliver one recommended native master, versioned bibliographic imports, a source/group map and a short handoff. Keep tests, intermediate Word-source files and alternate temporary-citation candidates out of the release. In the validated environment, the author should not need to convert the document, change Label matching preferences or manually approve each source. Record the tested application versions; do not turn local acceptance into an unconditional promise for other computers.

When no personal library exists, a verified export may be imported once for future searching and insertion. Existing native citations still use their embedded data; imported record IDs are not automatically equivalent to the document's prior IDs. If local-library binding is needed for metadata maintenance, establish it through native commands and verify propagation rather than guessing it.
