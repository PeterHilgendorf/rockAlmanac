# Rock Almanac

A structured, sourced chronicle of rock history — the bands, the people,
the albums, the exits and reunions — built as data first, so that
timelines, posters, and website views are all generated from one
canonical record rather than written by hand.

## How it works

Everything is data. An artist, a person, one stint of one person in one
band, an album, a dated event — each is a record with an ID, dates with
explicit precision, and a source for every fact. Build scripts turn
those records into output: a poster shows the 20 major events, the
website shows all 400, and both are correct because they read the same
data.

## The repository

| Folder | What it is |
|---|---|
| [schema/](schema/) | The contract with the data: ten entity definitions, conventions, and the event-type vocabulary. Start here. |

Data, importers, and build scripts will land in their own folders as
they take shape.

## Reference dataset

Fleetwood Mac is the planned first dataset — a band whose lineup
changes, intertwined personal lives, and long arc exercise every part
of the schema.

## Ground rules

1. **Memberships are stints.** Leave-and-return means two records.
2. **Precision is part of every date.** "July 1967" is a month-precision
   fact, never a fake specific day.
3. **Events reference, they don't restate.** Fix a fact once, and every
   generated output is correct on the next build.
4. **Everything is sourced.** A fact without a source is a draft.
5. **Significance is a field.** Editorial judgment lives in the data,
   not in the output scripts.

The full rules live in [schema/CONVENTIONS.md](schema/CONVENTIONS.md).
