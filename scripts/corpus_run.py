#!/usr/bin/env python3
"""Stage quote translation batches and review evidence without editing the input corpus."""

import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid
from contextlib import contextmanager

from corpus_inventory import EXCLUDED, build_inventory, content_hash, is_user_content, verification_status


ROLES = ("editor", "backtranslation", "fidelity", "adjudicator")
REQUIRED_ROLES = ("editor", "fidelity", "adjudicator")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".corpus-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked_run(path, creating=False):
    path = Path(path).resolve()
    if not creating and not (path / "manifest.json").is_file():
        raise ValueError("run has no manifest; initialize it first")
    path.mkdir(parents=True, exist_ok=True)
    with (path / ".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another coordinator is updating this run") from None
        yield path


def contexts(specifications):
    result = []
    for specification in specifications:
        scope, separator, name = specification.partition("=")
        if not separator:
            scope, name = "*", specification
        path = Path(name).resolve()
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"context must be a nonempty file: {name}")
        result.append({"scope": scope, "path": str(path), "hash": file_hash(path)})
    return result


def relevant_context(manifest, locale, category):
    return [item for item in manifest["contexts"] if item["scope"] in ("*", locale, "category:" + category)]


def snapshot(corpus_path, locales, context_specs, canonical_path, categories):
    corpus_path = Path(corpus_path).resolve()
    corpus = read_json(corpus_path)
    inventory = build_inventory(corpus, locales)
    canonical = None
    if canonical_path:
        path = Path(canonical_path).resolve()
        canonical = {"path": str(path), "hash": file_hash(path), "data": read_json(path)}
    return {
        "schema_version": 1, "source_path": str(corpus_path), "source_hash": file_hash(corpus_path),
        "corpus": corpus, "inventory": {k: v for k, v in inventory.items() if k != "records"},
        "locales": locales, "categories": categories, "contexts": contexts(context_specs),
        "canonical": canonical, "jobs": {}, "batches": {}, "review_packets": {}, "collision_decisions": {},
    }


def verify_inputs(manifest):
    files = [{"path": manifest["source_path"], "hash": manifest["source_hash"]}, *manifest["contexts"]]
    if manifest["canonical"]:
        files.append(manifest["canonical"])
    for item in files:
        if not Path(item["path"]).is_file() or file_hash(item["path"]) != item["hash"]:
            raise ValueError(f"input changed; run sync before continuing: {item['path']}")


def records(manifest):
    return {row["id"]: row for row in manifest["corpus"]["quotes"]}


def content_kind(row):
    if row.get("category") == "religion" and (row.get("source") or {}).get("canonicalReference"):
        return "scripture"
    if (row.get("attribution") or {}).get("name"):
        return "attributed"
    if row.get("verification") in {"authored", "curated"}:
        return "authored"
    return "uncertain"


def canonical_entry(manifest, row, locale):
    reference = (row.get("source") or {}).get("canonicalReference")
    entries = (manifest.get("canonical") or {}).get("data", {}).get("entries", [])
    matches = [entry for entry in entries if entry.get("locale") == locale and entry.get("reference") == reference]
    if len(matches) != 1:
        return None
    entry = matches[0]
    required = ("edition", "text", "source_url", "corpus_sha256")
    if not all(isinstance(entry.get(field), str) and entry[field].strip() for field in required):
        return None
    if entry.get("complete_verses") is not True or len(entry["corpus_sha256"]) != 64:
        return None
    return entry


def make_jobs(manifest):
    source_records = records(manifest)
    jobs = {}
    for group in manifest["inventory"]["groups"]:
        if manifest["categories"] and group["category"] not in manifest["categories"]:
            continue
        if not group["eligible"]:
            continue
        source = source_records[group["source_id"]]
        for locale in group["missing_locales"]:
            key = group["id"] + "::" + locale
            canonical = canonical_entry(manifest, source, locale) if content_kind(source) == "scripture" else None
            fingerprint = content_hash({"source": source, "locale": locale, "group": group["id"],
                                        "context": relevant_context(manifest, locale, group["category"]),
                                        "canonical": canonical})
            jobs[key] = {"group_id": group["id"], "source_id": source["id"], "locale": locale,
                         "category": group["category"], "kind": content_kind(source),
                         "fingerprint": fingerprint, "candidate": None, "reviews": {}}
    return jobs


def initialize(args, directory):
    if (directory / "manifest.json").exists():
        raise ValueError("run already exists; use status or sync")
    manifest = snapshot(args.corpus, args.locales.split(","), args.context, args.canonical,
                        args.categories.split(",") if args.categories else [])
    manifest["jobs"] = make_jobs(manifest)
    write_json(directory / "manifest.json", manifest)
    return summarize(manifest)


def synchronize(args, directory, previous):
    specifications = args.context if args.context is not None else [item["scope"] + "=" + item["path"] for item in previous["contexts"]]
    canonical_path = args.canonical or (previous.get("canonical") or {}).get("path")
    current = snapshot(args.corpus or previous["source_path"], previous["locales"], specifications,
                       canonical_path, previous["categories"])
    if set(records(previous)) - set(records(current)):
        raise ValueError("sync would lose existing record IDs; restore them or start a separately scoped run")
    current["jobs"] = make_jobs(current)
    reused = 0
    for key, job in current["jobs"].items():
        old = previous["jobs"].get(key)
        if old and old["fingerprint"] == job["fingerprint"]:
            current["jobs"][key] = old
            reused += 1
    current["batches"] = previous["batches"]
    current["review_packets"] = previous["review_packets"]
    current["collision_decisions"] = previous.get("collision_decisions", {})
    revision = 1
    while (directory / "history" / f"manifest.{revision}.json").exists():
        revision += 1
    write_json(directory / "history" / f"manifest.{revision}.json", previous)
    write_json(directory / "manifest.json", current)
    return {**summarize(current), "reused_jobs": reused, "invalidated_or_removed_jobs": len(previous["jobs"]) - reused}


def batch_jobs(manifest, batch_id, *, for_review=False):
    batch = manifest["batches"].get(batch_id)
    if batch is None:
        raise ValueError("unknown batch")
    if batch.get("superseded") and not for_review:
        raise ValueError("batch was superseded by an explicit revision batch")
    for key, fingerprint in batch["fingerprints"].items():
        if key not in manifest["jobs"] or manifest["jobs"][key]["fingerprint"] != fingerprint:
            raise ValueError("batch is stale; create a new batch after sync")
    return batch, {opaque: manifest["jobs"][key] for opaque, key in batch["ids"].items()}


def create_batch(args, directory, manifest):
    if not 1 <= args.size <= 40:
        raise ValueError("batch size must be between 1 and 40")
    requested = set(args.job or [])
    if requested - set(manifest["jobs"]):
        raise ValueError("requested job is unknown")
    reserved = set()
    for batch_id in manifest["batches"]:
        try:
            batch, _ = batch_jobs(manifest, batch_id)
        except ValueError:
            continue
        reserved.update(key for key in batch["ids"].values() if manifest["jobs"][key]["candidate"] is None)
    selected = [(key, job) for key, job in sorted(manifest["jobs"].items())
                if job["locale"] == args.locale and (not requested or key in requested) and
                ((args.revise and job["candidate"] is not None) or
                 (not args.revise and job["candidate"] is None and key not in reserved))][:args.size]
    if not selected:
        return {"batch": None, "message": "no unreserved jobs; resume existing packets or use --revise for candidates"}
    batch_id = f"b{len(manifest['batches']) + 1:04d}"
    batch = {"ids": {f"s{i:03d}": key for i, (key, _) in enumerate(selected, 1)},
             "fingerprints": {key: job["fingerprint"] for key, job in selected}, "locale": args.locale,
             "expected_candidates": {key: (job["candidate"] or {}).get("hash") for key, job in selected}}
    batch["hash"] = content_hash(batch)
    if args.revise:
        for previous in manifest["batches"].values():
            if set(previous["ids"].values()) & set(batch["ids"].values()):
                previous["superseded"] = True
    manifest["batches"][batch_id] = batch
    source_records = records(manifest)
    packet = {"batch": batch_id, "batch_hash": batch["hash"], "locale": args.locale,
              "context_files": [item for item in manifest["contexts"] if any(
                  item in relevant_context(manifest, job["locale"], job["category"]) for _, job in selected)], "entries": []}
    for opaque, key in batch["ids"].items():
        job = manifest["jobs"][key]
        source = source_records[job["source_id"]]
        packet["entries"].append({"id": opaque, "source": source, "kind": job["kind"],
                                  "canonical": canonical_entry(manifest, source, args.locale),
                                  "fit": "not_checked", "operation": "draft_missing_counterpart"})
    packet["output_contract"] = {"batch_hash": batch["hash"], "translator": {"id": "actual-agent-id", "model": "actual-model", "effort": "actual-effort"},
                                 "entries": [{"id": "s001", "text": "target text", "notes": "optional uncertainty"}]}
    write_json(directory / "manifest.json", manifest)
    path = directory / batch_id / "coordinator" / "source.json"
    write_json(path, packet)
    return {"batch": batch_id, "packet": str(path), "count": len(selected)}


def identity(value):
    if not isinstance(value, dict) or not all(isinstance(value.get(k), str) and value[k].strip() for k in ("id", "model", "effort")):
        raise ValueError("agent identity requires nonempty id, model and effort (use unknown when not exposed)")
    return {key: value[key] for key in ("id", "model", "effort")}


def exact_entries(data, expected):
    entries = data.get("entries")
    if not isinstance(entries, list) or any(not isinstance(row, dict) for row in entries):
        raise ValueError("entries must be a list of objects")
    ids = [row.get("id") for row in entries]
    if any(not isinstance(key, str) for key in ids) or len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError("entry IDs must match the exact batch: no missing, duplicate or unexpected IDs")
    return entries


def ingest(args, directory, manifest):
    batch, jobs = batch_jobs(manifest, args.batch)
    data = read_json(args.candidates)
    if data.get("batch_hash") != batch["hash"]:
        raise ValueError("candidate batch hash does not match")
    translator = identity(data.get("translator"))
    entries = exact_entries(data, jobs)
    source_records = records(manifest)
    for row in entries:
        if set(row) - {"id", "text", "notes"}:
            raise ValueError("candidate contains unsupported fields; source metadata is coordinator-owned")
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError("candidate text cannot be empty")
        source = source_records[jobs[row["id"]]["source_id"]]
        if source["text"].count("{userName}") != row["text"].count("{userName}"):
            raise ValueError("candidate changes the {userName} placeholder")
        job = jobs[row["id"]]
        current = job["candidate"]
        expected = batch["expected_candidates"][batch["ids"][row["id"]]]
        identical_retry = current and current["text"] == row["text"] and current["translator"] == translator and current["notes"] == row.get("notes", "")
        if (current or {}).get("hash") != expected and not identical_retry:
            raise ValueError("candidate changed after this batch; use an explicit --revise batch")
    changed = 0
    for row in entries:
        job = jobs[row["id"]]
        candidate = {"text": row["text"], "notes": row.get("notes", ""), "translator": translator,
                     "hash": content_hash({"text": row["text"], "notes": row.get("notes", ""),
                                           "translator": translator, "fingerprint": job["fingerprint"]})}
        if job["candidate"] == candidate:
            continue
        job["candidate"] = candidate
        job["reviews"] = {}
        changed += 1
    write_json(directory / "manifest.json", manifest)
    return {"changed_candidates": changed, "reviews_invalidated": changed}


def review_evidence(job):
    return content_hash({role: value for role, value in job["reviews"].items() if role != "adjudicator"})


def review_packet(args, directory, manifest):
    batch, jobs = batch_jobs(manifest, args.batch, for_review=True)
    if any(job["candidate"] is None for job in jobs.values()):
        raise ValueError("all batch candidates must exist before review")
    source_records = records(manifest)
    entries = []
    for opaque, job in jobs.items():
        entry = {"id": opaque, "text": job["candidate"]["text"], "kind": job["kind"], "display_role": "quote card", "fit": "not_checked"}
        if args.role in {"fidelity", "adjudicator"}:
            entry["source"] = source_records[job["source_id"]]
            entry["candidate_hash"] = job["candidate"]["hash"]
            entry["canonical"] = canonical_entry(manifest, entry["source"], job["locale"])
            if args.role == "adjudicator":
                entry["earlier_reviews"] = job["reviews"]
        entries.append(entry)
    packet = {"role": args.role, "locale": batch["locale"], "entries": entries, "revision_token": uuid.uuid4().hex}
    if args.role == "adjudicator":
        packet["scope"] = {"decision": "AI linguistic staging", "release_readiness": "not_checked",
                           "rendered_fit": "not_checked", "human_benchmark": "not_checked"}
    packet_hash = content_hash(packet)
    packet["packet_hash"] = packet_hash
    packet["output_contract"] = {"packet_hash": packet_hash, "reviewer": {"id": "actual-agent-id", "model": "actual-model", "effort": "actual-effort"},
                                  "entries": [{"id": "s001", "verdict": "pass|fail|not_checked", "notes": "findings or diagnostic back-translation"}]}
    manifest["review_packets"][packet_hash] = {"batch": args.batch, "role": args.role,
        "candidates": {opaque: job["candidate"]["hash"] for opaque, job in jobs.items()},
        "fingerprints": batch["fingerprints"],
        "evidence": {opaque: review_evidence(job) for opaque, job in jobs.items()}}
    write_json(directory / "manifest.json", manifest)
    folder = "blind" if args.role in {"editor", "backtranslation"} else "coordinator"
    path = directory / args.batch / folder / (args.role + "." + packet_hash[:12] + ".json")
    write_json(path, packet)
    return {"packet": str(path), "packet_hash": packet_hash, "role": args.role}


def record_review(args, directory, manifest):
    batch, jobs = batch_jobs(manifest, args.batch, for_review=True)
    data = read_json(args.input)
    packet = manifest["review_packets"].get(data.get("packet_hash"))
    if not packet or packet["batch"] != args.batch or packet["role"] != args.role:
        raise ValueError("review requires the exact registered role packet hash")
    entries = exact_entries(data, jobs)
    reviewer = identity(data.get("reviewer"))
    if reviewer["id"] == "unknown":
        raise ValueError("a distinct reviewer identity is required; model/effort may be unknown")
    for row in entries:
        job = jobs[row["id"]]
        if job["fingerprint"] != packet["fingerprints"][batch["ids"][row["id"]]]:
            raise ValueError("review is stale for the current source or context")
        if not job["candidate"] or job["candidate"]["hash"] != packet["candidates"][row["id"]]:
            raise ValueError("review is stale for the current candidate")
        if row.get("verdict") not in {"pass", "fail", "not_checked"} or not isinstance(row.get("notes"), str):
            raise ValueError("review needs verdict and evidence notes for each ID")
        identities = {job["candidate"]["translator"]["id"]} | {value["reviewer"]["id"] for role, value in job["reviews"].items() if role != args.role}
        if reviewer["id"] in identities:
            raise ValueError("translator and each review role must have separate declared identities")
        if args.role == "adjudicator" and any(job["reviews"].get(role, {}).get("verdict") != "pass" for role in ("editor", "fidelity")):
            raise ValueError("adjudication requires passed editorial and fidelity reviews")
        if args.role == "adjudicator" and review_evidence(job) != packet["evidence"][row["id"]]:
            raise ValueError("adjudication is stale for the current earlier reviews")
    for row in entries:
        jobs[row["id"]]["reviews"][args.role] = {"verdict": row["verdict"], "notes": row["notes"], "reviewer": reviewer,
                                                "candidate_hash": jobs[row["id"]]["candidate"]["hash"], "packet_hash": data["packet_hash"]}
        if args.role != "adjudicator":
            jobs[row["id"]]["reviews"].pop("adjudicator", None)
    write_json(directory / "manifest.json", manifest)
    return {"recorded": len(entries), "role": args.role}


def passed(job):
    return job["candidate"] is not None and all(job["reviews"].get(role, {}).get("verdict") == "pass" for role in REQUIRED_ROLES)


def target_collisions(manifest, selected=None):
    selected = list(manifest["jobs"].values()) if selected is None else selected
    targets = {}
    source_records = records(manifest)
    for group in manifest["inventory"]["groups"]:
        for locale, ids in group["members"].items():
            for record_id in ids:
                row = source_records[record_id]
                if isinstance(row.get("text"), str):
                    key = (group["category"], locale, " ".join(row["text"].split()).casefold())
                    targets.setdefault(key, []).append({"group": group["id"], "record": record_id,
                                                        "hash": content_hash(row), "new": False})
    for job in selected:
        if job["candidate"]:
            key = (job["category"], job["locale"], " ".join(job["candidate"]["text"].split()).casefold())
            targets.setdefault(key, []).append({"group": job["group_id"], "hash": job["candidate"]["hash"], "new": True})
    return [{"id": content_hash({"key": key, "members": members}), "locale": key[1],
             "text": key[2], "members": members}
            for key, members in sorted(targets.items())
            if any(member["new"] for member in members) and len({member["group"] for member in members}) > 1]


def acknowledge_collision(args, directory, manifest):
    if not args.reason.strip():
        raise ValueError("a reason for retaining the identical targets separately is required")
    if args.collision not in {item["id"] for item in target_collisions(manifest)}:
        raise ValueError("collision is unknown or stale; inspect status for current collision IDs")
    manifest["collision_decisions"][args.collision] = {"action": "keep_distinct_records", "reason": args.reason}
    write_json(directory / "manifest.json", manifest)
    return {"recorded": args.collision, "action": "keep_distinct_records"}


def summarize(manifest):
    jobs = list(manifest["jobs"].values())
    return {"source_hash": manifest["source_hash"], "existing_records": len(manifest["corpus"]["quotes"]),
            "groups": len(manifest["inventory"]["groups"]), "inventory_issues": manifest["inventory"]["issues"],
            "missing_counterparts": len(jobs), "pending": sum(job["candidate"] is None for job in jobs),
            "awaiting_review": sum(job["candidate"] is not None and not passed(job) for job in jobs),
            "ai_reviewed": sum(passed(job) for job in jobs), "human_review": "not_checked", "rendered_fit": "not_checked",
            "release_readiness": "not_checked", "agent_identity_evidence": "declared, not authenticated",
            "target_collisions": target_collisions(manifest)}


def export_staged(args, directory, manifest):
    destination = Path(args.out).resolve()
    if destination == Path(manifest["source_path"]) or destination.exists() or directory == destination or directory in destination.parents:
        raise ValueError("export requires a new file outside the run and cannot overwrite the source or any existing file")
    categories = args.categories.split(",") if args.categories else sorted({job["category"] for job in manifest["jobs"].values()})
    locales = args.locales.split(",") if args.locales else manifest["locales"]
    if not set(locales) <= set(manifest["locales"]):
        raise ValueError("export locales must belong to this run")
    source_records = records(manifest)
    selected = [job for job in manifest["jobs"].values() if job["category"] in categories and job["locale"] in locales]
    if not selected:
        raise ValueError("no additions selected")
    blockers = []
    for group in manifest["inventory"]["groups"]:
        if group["category"] not in categories:
            continue
        members = [source_records[key] for ids in group["members"].values() for key in ids]
        missing = set(group["missing_locales"]) & set(locales)
        outside_scope = all(verification_status(row) in EXCLUDED or is_user_content(row) for row in members)
        if not group["eligible"] and not outside_scope and missing:
            blockers.append(f"unresolved lineage group: {group['id']}")
        if group["eligible"] and any(group["id"] + "::" + locale not in manifest["jobs"] for locale in missing):
            blockers.append(f"category was not initialized for complete export: {group['category']}")
    for collision in target_collisions(manifest, selected):
        if collision["id"] not in manifest["collision_decisions"]:
            blockers.append(f"distinct sources have identical targets; revise or acknowledge collision {collision['id']}")
    for job in selected:
        if not passed(job):
            blockers.append(f"missing required review: {job['group_id']} / {job['locale']}")
        if not relevant_context(manifest, job["locale"], job["category"]):
            blockers.append("no context evidence for selected job")
        if job["kind"] == "uncertain":
            blockers.append("uncertain authorship needs an explicit content decision")
        if job["kind"] == "scripture":
            canonical = canonical_entry(manifest, source_records[job["source_id"]], job["locale"])
            if not canonical or not job["candidate"] or canonical["text"] != job["candidate"]["text"]:
                blockers.append("scripture must exactly match supplied edition/reference evidence")
    if blockers:
        raise ValueError("staged export blocked:\n" + "\n".join(sorted(set(blockers))))
    corpus = copy.deepcopy(manifest["corpus"])
    for job in selected:
        source = source_records[job["source_id"]]
        addition = copy.deepcopy(source)
        addition["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, "moneyfesting-translation:" + job["group_id"] + ":" + job["locale"])).upper()
        if addition["id"] in source_records:
            raise ValueError("new target ID collides with an existing record")
        addition.update(text=job["candidate"]["text"], language=job["locale"], translationOf=source["id"],
                        translatedFrom=source.get("language", "en"), reviewState="pending_owner_review")
        # A source citation verifies the original, not an AI translation of it.
        if job["kind"] != "scripture" and addition.get("verification") == "sourced":
            addition["verification"] = "sourced_unverified"
        if isinstance(addition.get("source"), dict):
            for field in ("verifiedBy", "verifiedAt", "verifiedOn"):
                addition["source"].pop(field, None)
        addition["translationEvidence"] = {"sourceRecordId": source["id"], "sourceRecordHash": content_hash(source),
                                            "candidateHash": job["candidate"]["hash"], "status": "ai_reviewed"}
        if job["kind"] == "scripture":
            canonical = canonical_entry(manifest, source, job["locale"])
            addition["source"] = {"canonicalReference": canonical["reference"], "title": canonical["edition"],
                                   "url": canonical["source_url"], "corpusSha256": canonical["corpus_sha256"],
                                   "verifiedBy": "supplied_canonical_index"}
            addition["verification"] = "sourced_unverified"
        corpus["quotes"].append(addition)
    if corpus["quotes"][:len(manifest["corpus"]["quotes"])] != manifest["corpus"]["quotes"]:
        raise ValueError("original records changed")
    write_json(destination, corpus)
    return {"out": str(destination), "preserved": len(manifest["corpus"]["quotes"]), "added": len(selected),
            "status": "staged_pending_owner_review", "release_readiness": "not_checked",
            "note": "Not published. Target-language labels, scripture evidence provenance and non-English translationOf compatibility still require app integration checks."}


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("init", "sync", "status", "batch", "ingest", "review-packet", "review", "acknowledge-collision", "export"):
        command = commands.add_parser(name)
        command.add_argument("--run-dir", required=True)
        if name in {"init", "sync"}:
            command.add_argument("--corpus", required=name == "init")
            command.add_argument("--context", action="append", default=[] if name == "init" else None,
                                 help="file or locale=file or category:name=file; repeatable")
            command.add_argument("--canonical", help="edition index JSON with entries")
        if name == "init":
            command.add_argument("--locales", default="en,ro,hu")
            command.add_argument("--categories")
        if name == "batch":
            command.add_argument("--locale", required=True)
            command.add_argument("--size", type=int, default=20)
            command.add_argument("--revise", action="store_true", help="explicitly supersede batches for existing candidates")
            command.add_argument("--job", action="append", help="select a coordinator job ID; repeatable")
        if name == "acknowledge-collision":
            command.add_argument("--collision", required=True)
            command.add_argument("--reason", required=True)
        if name in {"ingest", "review-packet", "review"}:
            command.add_argument("--batch", required=True)
        if name == "ingest":
            command.add_argument("--candidates", required=True)
        if name in {"review-packet", "review"}:
            command.add_argument("--role", choices=ROLES, required=True)
        if name == "review":
            command.add_argument("--input", required=True)
        if name == "export":
            command.add_argument("--out", required=True)
            command.add_argument("--locales")
            command.add_argument("--categories")
    return root


def main():
    args = parser().parse_args()
    try:
        with locked_run(args.run_dir, creating=args.command == "init") as directory:
            if args.command == "init":
                result = initialize(args, directory)
            else:
                manifest = read_json(directory / "manifest.json")
                if args.command == "sync":
                    result = synchronize(args, directory, manifest)
                else:
                    verify_inputs(manifest)
                    operations = {"status": lambda *unused: summarize(manifest), "batch": create_batch,
                                  "ingest": ingest, "review-packet": review_packet, "review": record_review,
                                  "acknowledge-collision": acknowledge_collision,
                                  "export": export_staged}
                    result = operations[args.command](args, directory, manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
