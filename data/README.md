# Rock Almanac — data

The dataset. One YAML file per entity, each a list of records conforming
to the definitions in [../schema/](../schema/). Validate with:

```
python3 scripts/validate.py
```

| File | Entity |
|---|---|
| sources.yaml | source |
| people.yaml | person |
| artists.yaml | artist |
| memberships.yaml | membership |
| albums.yaml | album |
| tracks.yaml | track |
| events.yaml | event (hand-entered only — generated types are rejected) |
| tours.yaml | tour |
| venues.yaml | venue |
| relationships.yaml | relationship |

## Status: draft

The initial Fleetwood Mac records were drafted from general reference
knowledge and cited to the Wikipedia pages listed in sources.yaml.
**A verification pass against those pages has not happened yet.** Dates
carry honest precision (year/month where the day isn't certain), but
until each record has been checked against its cited source, treat this
dataset as a working draft. Upgrading key facts to primary/secondary
sources (band memoirs, liner notes) is the step after that.
