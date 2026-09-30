#!/usr/bin/env python3
"""Build a Hungarian scripture index from a pinned Károli 1908 OSIS file."""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path


EDITION = "Revideált Károli Biblia 1908"
PINNED_SHA256 = "d54b72e4a0f7d63f464835a2ee0a988f386eccd40c0bc1dc56dec41e00b2b7bd"
PINNED_SOURCE_URL = (
    "https://raw.githubusercontent.com/krisek/HunKar/"
    "0e244494dd190e4a6b132c1afddfa307e73792f8/hunkaroli_rev.osis.xml"
)
BOOK_IDS = {
    "Genesis": "Gen", "Exodus": "Exod", "Leviticus": "Lev", "Numbers": "Num",
    "Deuteronomy": "Deut", "Joshua": "Josh", "Judges": "Judg", "Ruth": "Ruth",
    "1 Samuel": "1Sam", "2 Samuel": "2Sam", "1 Kings": "1Kgs", "2 Kings": "2Kgs",
    "1 Chronicles": "1Chr", "2 Chronicles": "2Chr", "Ezra": "Ezra", "Nehemiah": "Neh",
    "Esther": "Esth", "Job": "Job", "Psalms": "Ps", "Proverbs": "Prov",
    "Ecclesiastes": "Eccl", "Song of Songs": "Song", "Isaiah": "Isa",
    "Jeremiah": "Jer", "Lamentations": "Lam", "Ezekiel": "Ezek", "Daniel": "Dan",
    "Hosea": "Hos", "Joel": "Joel", "Amos": "Amos", "Obadiah": "Obad",
    "Jonah": "Jonah", "Micah": "Mic", "Nahum": "Nah", "Habakkuk": "Hab",
    "Zephaniah": "Zeph", "Haggai": "Hag", "Zechariah": "Zech", "Malachi": "Mal",
    "Matthew": "Matt", "Mark": "Mark", "Luke": "Luke", "John": "John",
    "Acts": "Acts", "Romans": "Rom", "1 Corinthians": "1Cor", "2 Corinthians": "2Cor",
    "Galatians": "Gal", "Ephesians": "Eph", "Philippians": "Phil",
    "Colossians": "Col", "1 Thessalonians": "1Thess", "2 Thessalonians": "2Thess",
    "1 Timothy": "1Tim", "2 Timothy": "2Tim", "Titus": "Titus", "Philemon": "Phlm",
    "Hebrews": "Heb", "James": "Jas", "1 Peter": "1Pet", "2 Peter": "2Pet",
    "1 John": "1John", "2 John": "2John", "3 John": "3John", "Jude": "Jude",
    "Revelation": "Rev",
}
REFERENCE = re.compile(r"^(.+) ([1-9]\d*):([1-9]\d*)(?:-([1-9]\d*))?$")
OSIS_VERSE = re.compile(r"^([1-3]?[A-Za-z]+)\.([1-9]\d*)\.([1-9]\d*)$")
SKIP_TAGS = {"note", "title", "reference"}


def local_name(element):
    return element.tag.rsplit("}", 1)[-1]


def normalized(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def inline_text(element):
    parts = [element.text or ""]
    for child in element:
        if local_name(child) not in SKIP_TAGS:
            parts.append(inline_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def parse_osis(path):
    verses = {}
    for element in ET.parse(path).iter():
        if local_name(element) != "verse":
            continue
        verse_id = element.get("osisID")
        if not verse_id:
            raise ValueError("OSIS verse without osisID; milestone verses need separate support")
        if not OSIS_VERSE.fullmatch(verse_id):
            raise ValueError(f"ambiguous OSIS verse ID: {verse_id}")
        if verse_id in verses:
            raise ValueError(f"duplicate OSIS verse ID: {verse_id}")
        text = normalized(inline_text(element))
        if not text:
            raise ValueError(f"empty OSIS verse: {verse_id}")
        verses[verse_id] = text
    if not verses:
        raise ValueError("no OSIS verses found")
    return verses


def requested_references(corpus_path, named):
    references = list(named)
    without_reference = 0
    if corpus_path:
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        for row in corpus["quotes"]:
            if row.get("category") == "religion":
                reference = (row.get("source") or {}).get("canonicalReference")
                if reference:
                    references.append(reference)
                else:
                    without_reference += 1
    if not references:
        raise ValueError("supply --reference or a corpus with scripture references")
    unique = list(dict.fromkeys(references))
    return unique, len(references) - len(unique), without_reference


def source_keys(reference):
    match = REFERENCE.fullmatch(reference)
    if not match or match[1] not in BOOK_IDS:
        raise ValueError(f"unsupported canonical reference: {reference}")
    book, chapter, first, last = match.groups()
    start = int(first)
    end = int(last) if last else start
    if end < start:
        raise ValueError(f"reversed canonical range: {reference}")
    return [f"{BOOK_IDS[book]}.{chapter}.{verse}" for verse in range(start, end + 1)]


def verify_source(osis_path, metadata):
    source_hash = hashlib.sha256(osis_path.read_bytes()).hexdigest()
    if source_hash != PINNED_SHA256:
        raise ValueError("OSIS file does not match the inspected Károli 1908 source hash")
    if metadata.get("locale") != "hu" or metadata.get("edition") != EDITION:
        raise ValueError("metadata does not identify the inspected Hungarian edition")
    if metadata.get("sha256") != source_hash or Path(metadata.get("file", "")).resolve() != osis_path:
        raise ValueError("source file does not match pinned metadata")
    if metadata.get("source_url") != PINNED_SOURCE_URL:
        raise ValueError("metadata does not identify the pinned source URL")
    return source_hash


def select_verses(verses, references, source_hash):
    entries = []
    unmatched = []
    fit_findings = []
    for reference in references:
        try:
            keys = source_keys(reference)
        except ValueError as error:
            unmatched.append({"reference": reference, "reason": str(error)})
            continue
        missing = [key for key in keys if key not in verses]
        if missing:
            unmatched.append({"reference": reference, "reason": "missing verses", "verse_ids": missing})
            continue
        text = normalized(" ".join(verses[key] for key in keys))
        entries.append({"locale": "hu", "reference": reference, "edition": EDITION, "text": text,
                        "source_url": PINNED_SOURCE_URL, "corpus_sha256": source_hash,
                        "complete_verses": True})
        if not 25 <= len(text) <= 300:
            fit_findings.append({"reference": reference, "characters": len(text),
                                 "reason": "short" if len(text) < 25 else "long"})
    return {"entries": entries, "requested": len(references), "matched": len(entries),
            "unmatched": unmatched, "fit_findings": fit_findings,
            "source_verses": len(verses)}


def build_index(osis_path, references, metadata):
    source_hash = verify_source(osis_path, metadata)
    return select_verses(parse_osis(osis_path), references, source_hash)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--osis", required=True, type=Path)
    parser.add_argument("--source-metadata", required=True, type=Path,
                        help="pinned source JSON with file, sha256, edition and source_url")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--corpus", type=Path, help="quote JSON whose religion records supply references")
    parser.add_argument("--reference", action="append", default=[], help="canonical English reference; repeatable")
    args = parser.parse_args()
    try:
        osis_path = args.osis.resolve(strict=True)
        destination = args.out.resolve()
        inputs = {osis_path, args.source_metadata.resolve(strict=True)}
        if args.corpus:
            inputs.add(args.corpus.resolve(strict=True))
        if destination.exists() or destination in inputs:
            raise ValueError("output must be a new file separate from all inputs")
        metadata = json.loads(args.source_metadata.read_text(encoding="utf-8"))
        references, repeated, without_reference = requested_references(args.corpus, args.reference)
        result = build_index(osis_path, references, metadata)
        result["repeated_references"] = repeated
        result["religion_rows_without_reference"] = without_reference
        print(json.dumps({key: value for key, value in result.items() if key != "entries"}, ensure_ascii=False, indent=2))
        if result["unmatched"]:
            return 1
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (ValueError, OSError, ET.ParseError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
