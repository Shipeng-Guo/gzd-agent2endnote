#!/usr/bin/env python3
"""Read-only cited-reference snapshots from genuine EndNote Word fields.

Does not edit Word, EndNote databases, or source exports. RIS is an exchange
snapshot, not a synchronization mechanism. Python 3.10+ and lxml are required.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from lxml import etree as ET

SCHEMA = "endnote-cited-registry/2"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS = {"w": W[1:-1]}
XML_PARSER = ET.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False)
CORE_PATHS = {
    "title": "titles/title", "year": "dates/year",
    "journal": "titles/secondary-title", "volume": "volume",
    "issue": "number", "pages": "pages", "reference_type": "ref-type",
}
LOCAL_ONLY_TAGS = {"rec-number", "foreign-keys", "source-app", "database", "last-updated"}


class SnapshotError(Exception):
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.problem = {"code": code, "message": message, **details}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def value(node, path):
    child = node.find(path)
    return "" if child is None else "".join(child.itertext()).strip()


def canonical_doi(raw):
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", raw.strip(), flags=re.I)
    if not re.fullmatch(r"10\.\d{4,9}/\S+", doi):
        raise SnapshotError("invalid_or_missing_doi", "A dedicated valid DOI is required; no identity guessing is permitted.", value=raw)
    return doi.lower()


def metadata(rec):
    core = {k: value(rec, p) for k, p in CORE_PATHS.items()}
    core["authors"] = ["".join(a.itertext()).strip() for a in rec.findall("contributors/authors/author")]
    core.update({
        "doi": canonical_doi(value(rec, "electronic-resource-num")),
        "label": value(rec, "label"), "pmid": value(rec, "accession-num"),
        "urls": ["".join(u.itertext()).strip() for u in rec.findall("urls//url")],
    })
    return core


def canonical_full_metadata(rec):
    """All XML metadata, excluding library-local identifiers and timestamps.

    The unmodified full XML record is separately retained in the registry/export.
    XML indentation and element order alone do not count as metadata changes.
    """
    def entry(n):
        if n.tag in LOCAL_ONLY_TAGS or n.tag == "timestamp":
            return None
        children = [x for c in n if (x := entry(c)) is not None]
        if n.tag not in {"authors", "secondary-authors", "tertiary-authors", "subsidiary-authors"}:
            children.sort(key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True))
        text = (n.text or "").strip()
        if n.tag == "electronic-resource-num":
            text = canonical_doi(text)
        if n.tag == "title":
            text = text.rstrip(".")
        return {"tag": n.tag, "attributes": dict(sorted(n.attrib.items())), "text": text,
                "tail": (n.tail or "").strip(), "children": children}
    return entry(rec)


def parse_fields(doc):
    fields, stack = [], []
    tree = doc.getroottree()
    for n in doc.iter():
        if n.tag == W + "fldSimple" and re.match(r"^ADDIN\s+EN\.CITE(?:\s|$)", n.get(W + "instr", "").strip()):
            raise SnapshotError("unsupported_simple_field", "Native citation in fldSimple is not supported by this parser.")
        if n.tag == W + "fldChar":
            typ = n.get(W + "fldCharType")
            if typ == "begin":
                stack.append({"code": "", "display": "", "phase": "code", "fielddata": [],
                              "xpath": tree.getpath(n), "in_table": any(a.tag == W + "tc" for a in n.iterancestors())})
            elif typ == "separate":
                if not stack:
                    raise SnapshotError("unbalanced_fields", "A field separator has no opening field.")
                stack[-1]["phase"] = "display"
            elif typ == "end":
                if not stack:
                    raise SnapshotError("unbalanced_fields", "A field end has no opening field.")
                f = stack.pop()
                f.pop("phase")
                fields.append(f)
        elif n.tag == W + "fldData" and stack:
            stack[-1]["fielddata"].append(n.text or "")
        elif n.tag == W + "instrText" and stack:
            stack[-1]["code"] += n.text or ""
        elif n.tag == W + "t" and stack and stack[-1]["phase"] == "display":
            stack[-1]["display"] += n.text or ""
    if stack:
        raise SnapshotError("unbalanced_fields", "Unclosed Word fields remain.", count=len(stack))
    # EN.CITE.DATA is a nested storage helper, never a separate citation group.
    return [f for f in fields if re.match(r"^ADDIN\s+EN\.CITE(?:\s|$)", f["code"].strip())]


def payload(field):
    code = field["code"]
    if "<EndNote>" in code:
        start = code.index("<EndNote>")
        end = code.rfind("</EndNote>") + len("</EndNote>")
        if end < start or code[end:].strip():
            raise SnapshotError("unsupported_payload", "Unexpected material after inline native XML.")
        raw = code[start:end].encode("utf-8")
        representation = "inline_xml"
    else:
        if len(field["fielddata"]) != 1:
            raise SnapshotError("unsupported_payload", "Expected exactly one outer native fldData payload.", count=len(field["fielddata"]))
        try:
            encoded = re.sub(r"\s+", "", field["fielddata"][0])
            raw = base64.b64decode(encoded, validate=True).rstrip(b"\0")
        except Exception as ex:
            raise SnapshotError("unsupported_payload", "Invalid native field-data base64.", detail=str(ex)) from ex
        representation = "base64_field_data"
    try:
        en = ET.fromstring(raw, XML_PARSER)
    except ET.XMLSyntaxError as ex:
        raise SnapshotError("invalid_citation_xml", "Native citation XML cannot be parsed.", detail=str(ex)) from ex
    if en.tag != "EndNote":
        raise SnapshotError("unsupported_payload", "Expected an EndNote XML root.")
    return en, representation


def read_citation_groups(raw):
    with ZipFile(BytesIO(raw)) as z:
        doc = ET.fromstring(z.read("word/document.xml"), XML_PARSER)
        for name in z.namelist():
            if re.fullmatch(r"word/(?:footnotes|endnotes|header\d+|footer\d+)\.xml", name):
                if parse_fields(ET.fromstring(z.read(name), XML_PARSER)):
                    raise SnapshotError("unsupported_story", "Citation ordering outside the main body/tables requires explicit support.", part=name)
    fields = parse_fields(doc)
    if not fields:
        raise SnapshotError("no_native_citations", "No genuine EN.CITE fields were found; temporary text is not an editable EndNote master.")
    groups = []
    for ordinal, field in enumerate(fields, 1):
        en, representation = payload(field)
        mentions = []
        for mention_index, cite in enumerate(en.findall("Cite"), 1):
            records = cite.findall("record")
            if len(records) != 1:
                raise SnapshotError("missing_or_multiple_embedded_records", "Each Cite must embed exactly one record.", group=ordinal, mention=mention_index)
            rec = records[0]
            m = metadata(rec)
            year = value(cite, "Year")
            if year and year != m["year"]:
                raise SnapshotError("citation_year_conflict", "Cite.Year disagrees with its embedded record.", group=ordinal, mention=mention_index)
            mentions.append({"doi": m["doi"], "embedded_metadata": m})
        if not mentions:
            raise SnapshotError("empty_citation_group", "Native citation group has no Cite entries.", group=ordinal)
        groups.append({"group": ordinal, "part": "word/document.xml", "xpath": field["xpath"],
                       "in_table": field["in_table"], "display": field["display"],
                       "representation": representation, "mentions": mentions})
    return groups


def read_library(raw):
    try:
        tree = ET.fromstring(raw, XML_PARSER)
    except ET.XMLSyntaxError as ex:
        raise SnapshotError("invalid_library_xml", "EndNote export XML cannot be parsed.", detail=str(ex)) from ex
    containers = tree.findall(".//records") if tree.tag != "records" else [tree]
    if len(containers) != 1:
        raise SnapshotError("unsupported_library_structure", "Exactly one records container is required.")
    records = containers[0].findall("record")
    if not records:
        raise SnapshotError("empty_library", "The export contains no records.")
    bydoi = OrderedDict()
    for index, rec in enumerate(records, 1):
        m = metadata(rec)
        if m["reference_type"] != "17":
            raise SnapshotError("unsupported_reference_type", "RIS export currently supports Journal Article type 17 only.", export_record=index, doi=m["doi"], reference_type=m["reference_type"])
        if not m["authors"] or not m["title"] or not m["year"] or not m["journal"]:
            raise SnapshotError("incomplete_core_metadata", "Authors, title, year and journal are required.", export_record=index, doi=m["doi"])
        if m["doi"] in bydoi:
            raise SnapshotError("duplicate_library_doi", "DOI maps to multiple export records; resolve duplicates before creating snapshots.", doi=m["doi"], export_records=[bydoi[m["doi"]]["export_ordinal"], index])
        bydoi[m["doi"]] = {"record": rec, "metadata": m, "export_ordinal": index}
    return tree, containers[0], bydoi


def compare_core(embedded, library):
    mismatches = {}
    for key in [*CORE_PATHS, "authors", "doi"]:
        a, b = embedded[key], library[key]
        if key == "title":
            a, b = a.rstrip("."), b.rstrip(".")
        if a != b:
            mismatches[key] = {"embedded": embedded[key], "library_export": library[key]}
    # Dedicated identifiers must agree when both records supply them.
    for key in ["pmid", "label"]:
        if embedded.get(key) and library.get(key) and embedded[key] != library[key]:
            mismatches[key] = {"embedded": embedded[key], "library_export": library[key]}
    return mismatches


def previous_index(previous):
    if previous is None:
        return {}, {}, {}
    if previous.get("schema") != SCHEMA:
        raise SnapshotError("unsupported_previous_registry", "Previous registry schema must match this tool.")
    bydoi, byid, bylabel = {}, {}, {}
    for r in previous.get("references", []):
        doi = canonical_doi(r["doi"])
        sid = r.get("stable_id")
        if doi in bydoi or not sid or sid in byid or not r.get("metadata_sha256"):
            raise SnapshotError("invalid_previous_registry", "Previous registry has ambiguous identity or missing metadata fingerprint.", doi=doi)
        bydoi[doi], byid[sid] = r, r
        label = r.get("label") or r.get("metadata", {}).get("label")
        if label:
            if label in bylabel:
                raise SnapshotError("invalid_previous_registry", "Previous labels must be unique.", label=label)
            bylabel[label] = r
    return bydoi, byid, bylabel


def identity_assignments(first, bydoi, previous, decisions=None):
    olddoi, oldid, oldlabel = previous_index(previous)
    labels = {}
    for doi, item in bydoi.items():
        label = item["metadata"]["label"]
        if label:
            if label in labels:
                raise SnapshotError("duplicate_library_label", "A library Label is shared by different DOIs; resolve identity before snapshotting.", label=label, dois=[labels[label], doi])
            labels[label] = doi
    choices = {}
    if decisions is not None:
        if decisions.get("schema") != "endnote-identity-decisions/1":
            raise SnapshotError("invalid_identity_decisions", "Identity decisions have an unsupported schema.")
        for decision in decisions.get("decisions", []):
            doi = canonical_doi(decision["doi"])
            if doi in choices or doi not in first or not decision.get("reason", "").strip() or decision.get("action") not in {"new", "reuse"}:
                raise SnapshotError("invalid_identity_decisions", "Decision needs a unique cited DOI, action and explicit evidence/reason.", doi=doi)
            choices[doi] = decision
    assigned, bases, used_old, unmatched = {}, {}, set(), []
    for doi in first:
        label = bydoi[doi]["metadata"]["label"]
        doi_old, label_old = olddoi.get(doi), oldlabel.get(label)
        if doi_old and label_old and doi_old["stable_id"] != label_old["stable_id"]:
            raise SnapshotError("identity_review_required", "DOI and Label point to different previous identities.", doi=doi, label=label)
        old = doi_old or label_old
        decision = choices.get(doi)
        if old:
            if decision and (decision["action"] != "reuse" or decision.get("stable_id") != old["stable_id"]):
                raise SnapshotError("invalid_identity_decisions", "Explicit decision conflicts with a unique existing mapping.", doi=doi)
            assigned[doi] = old["stable_id"]
            bases[doi] = "previous_registry_doi" if doi_old else "previous_registry_unique_label"
            used_old.add(old["stable_id"])
        elif decision and decision["action"] == "reuse":
            sid = decision.get("stable_id")
            if sid not in oldid:
                raise SnapshotError("invalid_identity_decisions", "Reused identity must exist in the previous registry.", doi=doi, stable_id=sid)
            assigned[doi], bases[doi] = sid, "explicit_evidence_based_identity_decision"
            used_old.add(sid)
        else:
            assigned[doi] = label or "SRC_" + sha(doi.encode("utf-8"))[:20]
            bases[doi] = "unique_library_label" if label else "new_once_generated_project_id"
            if not decision:
                unmatched.append(doi)
    disappeared = [sid for sid in oldid if sid not in used_old]
    if previous is not None and disappeared and unmatched:
        raise SnapshotError("identity_review_required", "Unmapped new DOIs coexist with missing prior identities. They could be additions/deletions or DOI corrections; do not guess. Supply explicit new/reuse decisions with evidence.", unmapped_current_dois=unmatched, unmatched_previous_stable_ids=disappeared)
    duplicates = [sid for sid, n in Counter(assigned.values()).items() if n > 1]
    if duplicates:
        raise SnapshotError("identity_review_required", "Multiple current DOIs map to the same stable project ID.", stable_ids=duplicates)
    return assigned, bases


def build_registry(groups, bydoi, input_hashes, previous=None, identity_decisions=None):
    first, counts, mismatches = OrderedDict(), Counter(), []
    for group in groups:
        for index, mention in enumerate(group["mentions"], 1):
            doi = canonical_doi(mention["doi"])
            if doi not in bydoi:
                raise SnapshotError("missing_library_record", "Cited DOI is absent from the export.", group=group["group"], mention=index, doi=doi)
            conflict = compare_core(mention["embedded_metadata"], bydoi[doi]["metadata"])
            if conflict:
                mismatches.append({"group": group["group"], "mention": index, "doi": doi, "fields": conflict})
            counts[doi] += 1
            if doi not in first:
                first[doi] = len(first) + 1
    if mismatches:
        raise SnapshotError("metadata_conflict", "Embedded citations and library metadata disagree. Resolve deliberately; re-importing the whole library is not an update strategy.", mismatches=mismatches)
    assigned, bases = identity_assignments(first, bydoi, previous, identity_decisions)
    references = []
    for doi, ordinal in first.items():
        item = bydoi[doi]
        rec = item["record"]
        full = canonical_full_metadata(rec)
        references.append({
            "stable_id": assigned[doi], "identity_basis": bases[doi], "doi": doi,
            "label": item["metadata"]["label"] or None,
            "source_id": (re.search(r"Review source ID:\s*([A-Za-z]+\d+)", value(rec, "notes")).group(1)
                          if re.search(r"Review source ID:\s*([A-Za-z]+\d+)", value(rec, "notes")) else None),
            "first_appearance_ordinal": ordinal,
            "used_count": counts[doi], "metadata": item["metadata"], "full_metadata": full,
            "metadata_sha256": sha(json.dumps(full, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")),
            "library_local_id": value(rec, "rec-number") or None,
            "library_export_ordinal": item["export_ordinal"],
            "library_local_id_role": "provenance_only_never_identity_matching",
            "record_xml": ET.tostring(rec, encoding="unicode", with_tail=False),
        })
    return {"schema": SCHEMA, "input_sha256": input_hashes,
            "citation_group_count": len(groups), "reference_mentions": sum(counts.values()),
            "unique_reference_count": len(references), "references": references}


def changes_between(current, previous, library_dois):
    cur = {r["stable_id"]: r for r in current["references"]}
    _, old, _ = previous_index(previous)
    added = [r["doi"] for sid, r in cur.items() if sid not in old]
    removed = [r["doi"] for sid, r in old.items() if sid not in cur]
    modified = [{"doi": r["doi"], "stable_id": sid,
                 "previous_metadata_sha256": old[sid]["metadata_sha256"],
                 "current_metadata_sha256": r["metadata_sha256"]}
                for sid, r in cur.items() if sid in old and r["metadata_sha256"] != old[sid]["metadata_sha256"]]
    doi_corrected = [{"stable_id": sid, "previous_doi": old[sid]["doi"], "current_doi": r["doi"]}
                     for sid, r in cur.items() if sid in old and r["doi"] != old[sid]["doi"]]
    cited_dois = {r["doi"] for r in cur.values()}
    return {"baseline_available": previous is not None, "added": added, "no_longer_cited": removed,
            "metadata_changed": modified, "doi_corrected": doi_corrected,
            "uncited_library": [d for d in library_dois if d not in cited_dois],
            "meaning": {"added": "Newly cited relative to this previous snapshot; may already exist in the user's library.",
                        "no_longer_cited": "Removed from manuscript citations only; never delete the library record automatically.",
                        "metadata_changed": "Full metadata changed; review and explicitly refresh native records. Re-importing all RIS records is not synchronization.",
                        "uncited_library": "Present in the supplied export but not cited; preserve these library records."}}


def ris_text(records):
    blocks = []
    for rec in records:
        m = metadata(rec)
        if m["reference_type"] != "17":
            raise SnapshotError("unsupported_reference_type", "RIS supports Journal Article type 17 only.", doi=m["doi"])
        lines = ["TY  - JOUR"]
        def add(tag, text):
            if text:
                # Continuation text is folded; XML retains the exact full record.
                lines.append(tag + "  - " + re.sub(r"[\r\n]+", " ", text))
        for author in m["authors"]:
            add("AU", author)
        for tag, key in [("TI", "title"), ("PY", "year"), ("T2", "journal"), ("VL", "volume"), ("IS", "issue")]:
            add(tag, m[key])
        pages = m["pages"]
        pair = re.fullmatch(r"([A-Za-z]*\d+)\s*[-–]\s*([A-Za-z]*\d+)", pages)
        if pair:
            add("SP", pair.group(1)); add("EP", pair.group(2))
        else:
            add("SP", pages)  # Article numbers/composite pagination remain literal.
        add("DO", m["doi"])
        for url in m["urls"]:
            add("UR", url)
        # LB is the EndNote Label tag. ID is a reference-manager record identity
        # and must not be used for the permanent project Label.
        add("LB", m["label"])
        add("AN", m["pmid"])
        for tag, path in [("SN", "isbn"), ("PB", "publisher"), ("CY", "pub-location"), ("LA", "language"), ("AB", "abstract"), ("N1", "notes")]:
            add(tag, value(rec, path))
        for kw in rec.findall("keywords/keyword"):
            add("KW", "".join(kw.itertext()).strip())
        lines.append("ER  - ")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + ("\n\n" if blocks else "")


def cloned_export(tree, selected_records):
    root = copy.deepcopy(tree)
    container = root if root.tag == "records" else root.find(".//records")
    for rec in list(container.findall("record")):
        container.remove(rec)
    for rec in selected_records:
        container.append(copy.deepcopy(rec))
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True, pretty_print=True)


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refresh(manuscript, library_xml, output_dir, previous_registry=None, identity_decisions=None):
    manuscript, library_xml, output_dir = map(Path, (manuscript, library_xml, output_dir))
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise SnapshotError("output_not_empty", "Output directory must be new or empty; previous snapshots are never overwritten.")
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = {"manuscript": manuscript, "library_xml": library_xml}
    if previous_registry:
        sources["previous_registry"] = Path(previous_registry)
    if identity_decisions:
        sources["identity_decisions"] = Path(identity_decisions)
    try:
        original = {k: p.read_bytes() for k, p in sources.items()}
    except OSError as ex:
        problem = {"code": "input_read_error", "message": "An input file could not be read.", "detail": str(ex)}
        write_json(output_dir / "validation_report.json", {"status": "blocked", "problem": problem,
                   "native_word_or_endnote_execution": False})
        raise SnapshotError(**problem) from ex
    hashes = {k: sha(raw) for k, raw in original.items()}
    try:
        groups = read_citation_groups(original["manuscript"])
        tree, _, bydoi = read_library(original["library_xml"])
        previous = json.loads(original["previous_registry"]) if previous_registry else None
        decisions = json.loads(original["identity_decisions"]) if identity_decisions else None
        registry = build_registry(groups, bydoi, hashes, previous, decisions)
        registry_by_doi = {r["doi"]: r for r in registry["references"]}
        for group in groups:
            for mention in group["mentions"]:
                r = registry_by_doi[mention["doi"]]
                mention["stable_id"] = r["stable_id"]
                mention["first_appearance_ordinal"] = r["first_appearance_ordinal"]
        changes = changes_between(registry, previous, list(bydoi))
        selected = [bydoi[r["doi"]]["record"] for r in registry["references"]]
        added = [bydoi[d]["record"] for d in changes["added"]]
        for key, path in sources.items():
            if sha(path.read_bytes()) != hashes[key]:
                raise SnapshotError("input_changed_during_read", "An input changed while the snapshot was being built; retry from a stable saved release.", input=key)
        # Do all semantic checks before writing exchange files.
        xml_out = cloned_export(tree, selected)
        ris_out, ris_added = ris_text(selected), ris_text(added)
        (output_dir / "cited_references.xml").write_bytes(xml_out)
        (output_dir / "cited_references.ris").write_text(ris_out, encoding="utf-8", newline="\n")
        (output_dir / "additions_only.ris").write_text(ris_added, encoding="utf-8", newline="\n")
        write_json(output_dir / "reference_registry.json", registry)
        write_json(output_dir / "citation_groups.json", {"input_sha256": hashes, "groups": groups})
        write_json(output_dir / "changes.json", changes)
        report = {"status": "passed_static_snapshot_validation", "input_sha256": hashes,
                  "source_files_unchanged": True, "native_word_or_endnote_execution": False,
                  "counts": {"citation_groups": len(groups), "reference_mentions": registry["reference_mentions"],
                             "unique_cited_references": len(selected), "library_records": len(bydoi),
                             "table_citation_groups": sum(g["in_table"] for g in groups)},
                  "representations": dict(Counter(g["representation"] for g in groups)),
                  "outputs": {p.name: sha(p.read_bytes()) for p in output_dir.iterdir() if p.is_file()},
                  "scope": "Read-only static parsing and metadata verification. No library writes, no Word edits, no native-formatting test."}
        write_json(output_dir / "validation_report.json", report)
        return report
    except Exception as ex:
        problem = ex.problem if isinstance(ex, SnapshotError) else {"code": "unexpected_input_error", "message": str(ex), "exception_type": type(ex).__name__}
        report = {"status": "blocked", "input_sha256": hashes, "problem": problem,
                  "source_files_unchanged": all(p.exists() and sha(p.read_bytes()) == hashes[k] for k, p in sources.items()),
                  "native_word_or_endnote_execution": False}
        write_json(output_dir / "validation_report.json", report)
        if isinstance(ex, SnapshotError):
            raise
        raise SnapshotError(**problem) from ex


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manuscript", type=Path, required=True)
    ap.add_argument("--library-xml", type=Path, required=True)
    ap.add_argument("--previous-registry", type=Path)
    ap.add_argument("--identity-decisions", type=Path, help="Explicit evidence-based new/reuse decisions for otherwise ambiguous identity changes.")
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = refresh(args.manuscript, args.library_xml, args.output_dir, args.previous_registry, args.identity_decisions)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except SnapshotError as ex:
        print(json.dumps({"status": "blocked", "problem": ex.problem}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
