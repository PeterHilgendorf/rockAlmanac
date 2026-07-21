# Rock Almanac — Schema

This folder is the contract with the data. Every importer, build script,
visualization, and AI prompt depends on the definitions here.

## The ten entities

| File | What it is |
|---|---|
| artist.yaml | A band or solo act |
| person.yaml | A human being |
| membership.yaml | One stint of one person in one artist |
| album.yaml | One release |
| track.yaml | One track on an album (optional depth) |
| event.yaml | A dated moment — the backbone of every timeline |
| tour.yaml | A named tour |
| venue.yaml | A physical place |
| relationship.yaml | Typed links between entities (the graph) |
| source.yaml | Where every fact came from |

Plus:
- **CONVENTIONS.md** — IDs, dates, precision, sourcing rules
- **EVENT_TYPES.md** — controlled vocabulary for events

## How to read a schema file

Each file defines the fields for one entity: type, whether it's required,
and what it references. Each ends with a small worked example. The examples
use Fleetwood Mac because it's the planned reference dataset — they are
illustrations, not data. No data lives in this folder.

## Design decisions worth knowing

1. **Memberships are stints.** Leave-and-return means two records.
   This single choice is what makes personnel timelines generatable.
2. **Precision is part of every date.** "July 1967" is stored as a month-
   precision fact, never fudged into a fake specific day.
3. **Events reference, they don't restate.** Fix an album's release date
   once, and every generated timeline is correct on the next build.
4. **Everything is sourced.** A fact without a source_id is a draft.
5. **Significance is a field.** Tagging events major/notable/minor lets a
   poster show 20 events while the website shows 400 — same data.
