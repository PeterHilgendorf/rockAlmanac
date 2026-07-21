#!/usr/bin/env python3
"""Rock Almanac data validator.

The schema folder is the contract; this script enforces it. It reads the
field definitions straight out of schema/*.yaml (plus EVENT_TYPES.md and
relationship.yaml's rel_types list), then checks every record in data/
against them:

  - required fields present, unknown fields rejected
  - types: slugs, dates, enums, integers, booleans, urls, lists
  - every *_date has its *_precision partner (and vice versa)
  - IDs unique, every cross-reference resolves
  - person: death_date and current_residence are mutually exclusive
  - membership stints for one person+artist don't overlap
  - MEMBER_JOIN/EXIT/RETURN events agree with membership records
  - MARRIAGE/DIVORCE events agree with MARRIED_TO relationships
  - generated event types (ALBUM_RELEASE, TOUR_START, TOUR_END) are
    rejected in hand-entered data
  - web sources carry accessed_date
  - warnings for orphan venues and unused sources

Exit 0 = data is valid (warnings allowed). Exit 1 = errors.
"""

import datetime
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schema"
DATA_DIR = ROOT / "data"

# entity name -> data file name
DATA_FILES = {
    "source": "sources.yaml",
    "person": "people.yaml",
    "artist": "artists.yaml",
    "membership": "memberships.yaml",
    "album": "albums.yaml",
    "track": "tracks.yaml",
    "event": "events.yaml",
    "tour": "tours.yaml",
    "venue": "venues.yaml",
    "relationship": "relationships.yaml",
}

GENERATED_EVENT_TYPES = {"ALBUM_RELEASE", "TOUR_START", "TOUR_END"}
WEB_SOURCE_TYPES = {"musicbrainz", "discogs", "wikipedia", "wikidata", "website"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PRECISIONS = ["year", "month", "day"]

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


# ---------------------------------------------------------------- schema

def load_schemas():
    """Parse each schema/*.yaml into {entity: {field: spec_dict}}."""
    schemas = {}
    for entity, _ in DATA_FILES.items():
        path = SCHEMA_DIR / (entity + ".yaml")
        # "type: enum [a, b]" is contract shorthand, not valid YAML flow
        # syntax — quote it so the file parses.
        text = re.sub(r"enum \[([^\]]+)\]", r'"enum [\1]"', path.read_text())
        doc = yaml.safe_load(text)
        if doc.get("entity") != entity:
            err("schema %s: entity name mismatch" % path.name)
        schemas[entity] = doc["fields"]
        if entity == "relationship":
            schemas["_rel_types"] = doc.get("rel_types", [])
    return schemas


def load_event_types():
    """Pull the controlled vocabulary out of EVENT_TYPES.md's table."""
    types = set()
    for line in (SCHEMA_DIR / "EVENT_TYPES.md").read_text().splitlines():
        m = re.match(r"^\|\s*([A-Z][A-Z_]+)\s*\|", line)
        if m:
            types.add(m.group(1))
    return types


# ---------------------------------------------------------------- data

# A value like `headline: Rumours hits US #1` silently loses everything
# from '#' onward — YAML reads it as a comment. The '#' is gone by the
# time the file is parsed, so this has to scan the raw text. It only
# looks at same-line `key: value` scalars, so block scalars (notes: >),
# where '#' is literal, never match.
_INLINE_SCALAR = re.compile(r"^\s*(?:- )?[\w-]+:\s+(?P<val>\S.*)$")


def check_raw_comment_traps(fname, text):
    for i, line in enumerate(text.splitlines(), 1):
        m = _INLINE_SCALAR.match(line)
        if not m:
            continue
        val = m.group("val")
        if val[0] in "'\"|>[{":  # quoted, block, or flow — '#' is safe
            continue
        if " #" in val:
            err("%s line %d: ' #' in an unquoted value starts a YAML "
                "comment and truncates it — quote the value: %s"
                % (fname, i, line.strip()))


def load_data():
    data = {}
    for entity, fname in DATA_FILES.items():
        path = DATA_DIR / fname
        if not path.exists():
            data[entity] = []
            continue
        text = path.read_text()
        check_raw_comment_traps(fname, text)
        doc = yaml.safe_load(text)
        if doc is None:
            doc = []
        if not isinstance(doc, list):
            err("%s: top level must be a list of records" % fname)
            doc = []
        data[entity] = doc
    return data


# ---------------------------------------------------------------- checks

def is_date(value):
    if isinstance(value, datetime.date):
        return True
    if isinstance(value, str):
        try:
            datetime.date.fromisoformat(value)
            return True
        except ValueError:
            return False
    return False


def as_date(value):
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(value)


def enum_values(spec_type):
    m = re.search(r"enum \[([^\]]*)\]", spec_type)
    if not m:
        return None
    return [v.strip() for v in m.group(1).split(",")]


def check_ref(value, target_entity, ids_by_entity, where):
    if value not in ids_by_entity.get(target_entity, set()):
        err("%s: reference '%s' does not resolve to a %s" % (where, value, target_entity))


def check_field(entity, rec_id, fname, value, spec, ids_by_entity, event_types, rel_types):
    where = "%s '%s' field '%s'" % (entity, rec_id, fname)
    t = spec.get("type", "")

    if t == "slug":
        if not (isinstance(value, str) and SLUG_RE.match(value)):
            err("%s: not a valid slug: %r" % (where, value))
    elif t == "date":
        if not is_date(value):
            err("%s: not an ISO date: %r" % (where, value))
    elif t.startswith("enum"):
        allowed = enum_values(t)
        if allowed is None:
            # bare "enum": event_type -> EVENT_TYPES.md, rel_type -> rel_types
            allowed = event_types if fname == "event_type" else rel_types
        if value not in allowed:
            err("%s: %r not in allowed values %s" % (where, value, sorted(allowed)))
    elif t == "boolean":
        if not isinstance(value, bool):
            err("%s: expected boolean, got %r" % (where, value))
    elif t.startswith("integer OR"):
        if not (isinstance(value, int) and not isinstance(value, bool)) and value != "none":
            err("%s: expected integer or \"none\", got %r" % (where, value))
    elif t == "integer":
        if not (isinstance(value, int) and not isinstance(value, bool)):
            err("%s: expected integer, got %r" % (where, value))
    elif t == "url":
        if not (isinstance(value, str) and value.startswith("http")):
            err("%s: expected URL, got %r" % (where, value))
    elif t in ("string", "text"):
        if not isinstance(value, str):
            err("%s: expected string, got %r" % (where, value))
    elif t == "map":
        if not isinstance(value, dict):
            err("%s: expected map, got %r" % (where, value))
    elif t == "entity ref":
        if not (isinstance(value, str) and ":" in value):
            err("%s: expected 'entity:id', got %r" % (where, value))
        else:
            ref_entity, ref_id = value.split(":", 1)
            if ref_entity not in DATA_FILES:
                err("%s: unknown entity '%s'" % (where, ref_entity))
            else:
                check_ref(ref_id, ref_entity, ids_by_entity, where)
    elif t == "list of strings":
        if not (isinstance(value, list) and all(isinstance(v, str) for v in value)):
            err("%s: expected list of strings, got %r" % (where, value))
    elif "OR strings" in t:  # e.g. "list of ids -> person OR strings"
        if not (isinstance(value, list) and all(isinstance(v, str) for v in value)):
            err("%s: expected list of ids/strings, got %r" % (where, value))
    elif t.startswith("list of ids ->"):
        target = t.split("->", 1)[1].strip()
        if not isinstance(value, list) or not value:
            err("%s: expected non-empty list of ids" % where)
        else:
            for v in value:
                check_ref(v, target, ids_by_entity, where)
    elif t.startswith("id ->"):
        target = t.split("->", 1)[1].strip()
        check_ref(value, target, ids_by_entity, where)
    elif t.startswith("list of"):  # legs, periods — nested item_fields
        item_fields = spec.get("item_fields", {})
        if not isinstance(value, list):
            err("%s: expected a list" % where)
            return
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                err("%s[%d]: expected a mapping" % (where, i))
                continue
            item_where = "%s '%s' %s[%d]" % (entity, rec_id, fname, i)
            for ifname, ispec in item_fields.items():
                if ispec.get("required") and ifname not in item:
                    err("%s: missing required field '%s'" % (item_where, ifname))
            for ifname, ivalue in item.items():
                if ifname not in item_fields:
                    err("%s: unknown field '%s'" % (item_where, ifname))
                    continue
                check_field(entity, "%s.%s[%d]" % (rec_id, fname, i), ifname,
                            ivalue, item_fields[ifname], ids_by_entity,
                            event_types, rel_types)
            check_date_precision_pairs(item, item_fields, item_where)
    else:
        warn("%s: no validator for schema type '%s'" % (where, t))


def check_date_precision_pairs(record, fields, where):
    """Every date field present needs its precision partner, and vice versa."""
    for fname in fields:
        if fname == "date":
            partner = "date_precision"
        elif fname.endswith("_date"):
            partner = fname[:-5] + "_precision"
        else:
            continue
        if partner not in fields:
            continue
        if fname in record and partner not in record:
            err("%s: '%s' present but '%s' missing — precision is part of the fact"
                % (where, fname, partner))
        if partner in record and fname not in record:
            err("%s: '%s' present without '%s'" % (where, partner, fname))


def truncated_dates_equal(date_a, prec_a, date_b, prec_b):
    """Compare two dated facts at the coarser of their precisions."""
    a, b = as_date(date_a), as_date(date_b)
    coarsest = min(PRECISIONS.index(prec_a), PRECISIONS.index(prec_b))
    if a.year != b.year:
        return False
    if coarsest >= 1 and a.month != b.month:
        return False
    if coarsest >= 2 and a.day != b.day:
        return False
    return True


# ---------------------------------------------------------------- main

def main():
    schemas = load_schemas()
    rel_types = schemas.pop("_rel_types", [])
    event_types = load_event_types()
    data = load_data()

    # -- collect ids, check uniqueness (globally: ids never collide)
    ids_by_entity = {}
    seen = {}
    for entity, records in data.items():
        ids_by_entity[entity] = set()
        for rec in records:
            if not isinstance(rec, dict) or "id" not in rec:
                err("%s: record without an id: %r" % (entity, rec))
                continue
            rid = rec["id"]
            if rid in seen:
                err("duplicate id '%s' (%s and %s)" % (rid, seen[rid], entity))
            seen[rid] = entity
            ids_by_entity[entity].add(rid)

    # -- per-record field validation
    for entity, records in data.items():
        fields = schemas[entity]
        for rec in records:
            if not isinstance(rec, dict):
                continue
            rid = rec.get("id", "<no id>")
            where = "%s '%s'" % (entity, rid)
            for fname, spec in fields.items():
                if spec.get("required") and fname not in rec:
                    err("%s: missing required field '%s'" % (where, fname))
            for fname, value in rec.items():
                if fname not in fields:
                    err("%s: unknown field '%s'" % (where, fname))
                    continue
                check_field(entity, rid, fname, value, fields[fname],
                            ids_by_entity, event_types, rel_types)
            check_date_precision_pairs(rec, fields, where)

    # -- person: dead people don't have a current residence
    for rec in data["person"]:
        if "death_date" in rec and "current_residence" in rec:
            err("person '%s': has both death_date and current_residence" % rec["id"])

    # -- membership stints must not overlap for one person+artist
    by_pair = {}
    for m in data["membership"]:
        key = (m.get("person_id"), m.get("artist_id"))
        by_pair.setdefault(key, []).append(m)
    for (pid, aid), stints in by_pair.items():
        dated = [m for m in stints if "start_date" in m]
        dated.sort(key=lambda m: str(m["start_date"]))
        for prev, nxt in zip(dated, dated[1:]):
            if "end_date" not in prev:
                warn("membership '%s': open-ended stint precedes '%s' for %s in %s"
                     % (prev["id"], nxt["id"], pid, aid))
            elif str(prev["end_date"]) > str(nxt["start_date"]):
                warn("memberships '%s' and '%s' overlap for %s in %s"
                     % (prev["id"], nxt["id"], pid, aid))

    # -- events: generated types rejected; membership events must agree
    for ev in data["event"]:
        eid = ev.get("id", "<no id>")
        etype = ev.get("event_type")
        if etype in GENERATED_EVENT_TYPES:
            err("event '%s': %s events are generated by build scripts, never hand-entered"
                % (eid, etype))
        if etype in ("MEMBER_JOIN", "MEMBER_RETURN", "MEMBER_EXIT"):
            boundary = "end" if etype == "MEMBER_EXIT" else "start"
            for pid in ev.get("person_ids", []):
                for aid in ev.get("artist_ids", []):
                    matches = [
                        m for m in by_pair.get((pid, aid), [])
                        if boundary + "_date" in m and truncated_dates_equal(
                            ev["date"], ev["date_precision"],
                            m[boundary + "_date"], m[boundary + "_precision"])
                    ]
                    if not matches:
                        err("event '%s' (%s): no membership record for %s in %s "
                            "with a matching %s date" % (eid, etype, pid, aid, boundary))

    # -- MARRIAGE/DIVORCE events agree with MARRIED_TO relationships
    married = [r for r in data["relationship"] if r.get("rel_type") == "MARRIED_TO"]
    for ev in data["event"]:
        etype = ev.get("event_type")
        if etype not in ("MARRIAGE", "DIVORCE"):
            continue
        pids = ev.get("person_ids", [])
        if len(pids) < 2:
            continue  # spouse outside the dataset — nothing to cross-check
        pair = set("person:%s" % p for p in pids[:2])
        rels = [r for r in married if set([r.get("from"), r.get("to")]) == pair]
        if not rels:
            warn("event '%s' (%s): no MARRIED_TO relationship between %s"
                 % (ev.get("id"), etype, sorted(pids)))
            continue
        boundary = "start" if etype == "MARRIAGE" else "end"
        ok = any(
            boundary + "_date" in r and truncated_dates_equal(
                ev["date"], ev["date_precision"],
                r[boundary + "_date"], r[boundary + "_precision"])
            for r in rels)
        if not ok:
            err("event '%s' (%s): MARRIED_TO relationship %s date does not agree"
                % (ev.get("id"), etype, boundary))

    # -- web sources need accessed_date
    for s in data["source"]:
        if s.get("source_type") in WEB_SOURCE_TYPES and "accessed_date" not in s:
            err("source '%s': web sources require accessed_date" % s.get("id"))

    # -- orphan venues, unused sources
    used_venues = set(ev.get("venue_id") for ev in data["event"])
    for v in data["venue"]:
        if v["id"] not in used_venues:
            warn("venue '%s': no event references it (no orphan venues)" % v["id"])
    used_sources = set()
    for entity, records in data.items():
        for rec in records:
            for sid in rec.get("source_ids", []):
                used_sources.add(sid)
    for s in data["source"]:
        if s.get("id") not in used_sources:
            warn("source '%s': nothing cites it" % s.get("id"))

    # -- report
    count = sum(len(v) for v in data.values())
    for w in warnings:
        print("WARN  %s" % w)
    for e in errors:
        print("ERROR %s" % e)
    print("\n%d records checked: %d errors, %d warnings"
          % (count, len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
