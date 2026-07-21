# Rock Almanac Schema Conventions

These rules apply to every entity file in this folder.

## IDs
- Every record has a unique `id`, written as a lowercase slug: `fleetwood-mac`, `stevie-nicks`, `rumours-1977`.
- IDs never change once assigned. Names can change; IDs cannot.
- Cross-references always use IDs, never names.

## Dates
- ISO 8601: `1977-02-04`. 
- When only partial information is known, use `date_precision` to say how much
  of the date is trustworthy: `day`, `month`, or `year`.
  Example: `date: 1967-07-01` + `date_precision: month` means "July 1967, day unknown."
- Never guess a day to fill out a date. Precision is part of the fact.

## Sources
- Every entity carries `source_ids` pointing to records in `source.yaml`.
- A fact without a source is a draft, not a fact.
- When sources disagree, record the disagreement in `notes` rather than silently picking one.

## Required vs optional
- Fields marked `required` must be present for a record to be valid.
- Optional fields are omitted when unknown — never filled with "unknown", "N/A", or empty strings.

## One fact, one place
- A person's birth date lives in their `person` record only.
- An album's release date lives in its `album` record only.
- Events reference these records; they do not restate their contents.
