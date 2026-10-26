# GZD Agent-to-EndNote

An English GZDLab agent skill for delivering editable native EndNote manuscripts and maintaining citations across manuscript revisions. The skill name is `gzd-agent2endnote`; it continues the earlier `agent-endnote` workflow.

It guides an agent through source identities, citation-group mapping, native Word/EndNote conversion and acceptance, library reconciliation, and versioned reference snapshots. It also includes a read-only Python snapshot helper. The helper audits existing native fields; it does not create or repair them.

## Install

Clone this repository into your personal skills directory. For the default Codex directory:

```bash
git clone https://github.com/Shipeng-Guo/gzd-agent2endnote.git ~/.codex/skills/gzd-agent2endnote
```

PowerShell:

```powershell
git clone https://github.com/Shipeng-Guo/gzd-agent2endnote.git "$env:USERPROFILE/.codex/skills/gzd-agent2endnote"
```

If you use a custom skills directory, clone there instead. Keep the `SKILL.md`, `agents`, `references`, and `scripts` paths together. When migrating an existing installation, preserve any local changes and move the old `agent-endnote` directory outside the active skills directory after the new installation is ready. Update its callers to use `$gzd-agent2endnote`.

## Use

Example requests:

> Use $gzd-agent2endnote to prepare a native EndNote handoff for this manuscript. Verify the source registry, every citation group, native formatting, and the saved Word file before creating the release snapshot.

> Use $gzd-agent2endnote to add these two verified papers to my existing native manuscript. Reuse existing library records where possible, preserve current citation fields, and report the changed citation groups.

> Use $gzd-agent2endnote to compare the current cited set with the previous release without changing the Word document or importing anything into my library.

Native delivery needs an installed, working Word/EndNote integration and a supported way for the agent to interact with it. This repository does not supply Word, EndNote, application licenses, or an automation connector. Instructions are written in English; source metadata and author names retain their original language and spelling.

The skill works independently. [gzd-review-writing](https://github.com/Shipeng-Guo/gzd-review-writing) is an optional companion for evidence-led biomedical review writing, not a required sibling installation.

## Read-only snapshot helper

The helper requires **Python 3.10+** and **lxml**. Install the dependency in the Python environment you will use:

```bash
python -m pip install lxml
```

From this repository's directory:

```bash
python scripts/refresh_snapshot.py --help
python scripts/refresh_snapshot.py --manuscript manuscript_native.docx --library-xml library_export.xml --output-dir release_02/reference_snapshot --previous-registry release_01/reference_snapshot/reference_registry.json
```

Omit `--previous-registry` for a first snapshot. The output directory must be new or empty. See [the helper guide](scripts/README.md) for identity decisions, all outputs, and validation details.

The current helper supports native EndNote **Journal Article type 17** records with dedicated verified DOIs, and citation ordering in the main body and tables. It stops on unsupported reference types or citation stories, ambiguous identities, missing records, and metadata conflicts. Do not remove legitimate sources to fit those limits; use another supported audit or extend the helper for the task.

It writes cited-set XML/RIS, source and group registries, a change report, and hashes. It does not modify the manuscript or EndNote library, perform native formatting, or assess whether a source supports a scientific claim. A source newly cited in the manuscript may already exist in the author's library; the generated additions file is not automatically a target-library import delta.

## Workflow guides

- [Skill entry point](SKILL.md)
- [First native delivery and validation](references/native-delivery.md)
- [Reference changes and library snapshots](references/library-maintenance.md)
- [Snapshot helper interface and scope](scripts/README.md)
- [Release history](CHANGELOG.md)

The repository contains instructions and the snapshot utility. It does not include private manuscripts, personal libraries, historical project fixtures, or a packaged native-application conversion engine.
