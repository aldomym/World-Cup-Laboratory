# World Cup Lab

A dependency-free full-stack FIFA World Cup simulator.

## What it includes

- **215 available national teams**
  - all **211 FIFA member associations**
  - Greenland
  - Northern Mariana Islands
  - Tuvalu
  - Marshall Islands
- **48-team final tournament**
- Host selection with automatic qualification
- Confederation qualifying campaigns
- Six-team intercontinental playoff for the last two places
- Every qualifier result persisted
- Four draw pots of 12 based on the **20 July 2026 FIFA men's ranking**
- Non-FIFA additions are treated as **unranked** and sort after all ranked FIFA members for pot seeding
- Confederation-aware random group draw
  - maximum two UEFA teams per group
  - maximum one team from every other confederation per group
- 12 groups of four
- Top two in each group + eight best third-placed teams advance
- Round of 32, Round of 16, quarterfinals, semifinals, third-place playoff and final
- Multiple saved simulations in SQLite

## Run it

Requires Python 3.11+ and no third-party packages.

```bash
cd world-cup-simulator
python app.py
```

Then open:

```text
http://localhost:8000
```

The database file `worldcups.sqlite3` is created automatically beside `app.py`.

To change the port:

```bash
PORT=9000 python app.py
```

To put the SQLite database somewhere else:

```bash
WC_DB_PATH=/path/to/worldcups.sqlite3 python app.py
```

## Simulator format

This is a **custom generic 48-team World Cup cycle**, not a clone of one edition's exact regional qualifier schedules.

The final-slot allocation follows the 48-team allocation shape:

| Confederation | Direct | Intercontinental playoff |
|---|---:|---:|
| AFC | 8 | 1 |
| CAF | 9 | 1 |
| CONCACAF | 6 | 2 |
| CONMEBOL | 6 | 1 |
| OFC | 1 | 1 |
| UEFA | 16 | 0 |

The selected host consumes one direct place from its confederation. The six playoff entrants compete for two remaining final-tournament places.

Qualifying uses seeded regional groups (CONMEBOL uses one league table). It is intentionally designed for repeatable simulation rather than reproducing the exact historical regulations of a specific cycle.

## July 2026 seeding

The ranking order is locked to the FIFA men's ranking update dated **20 July 2026**.

The four additional non-FIFA teams do not have an official FIFA ranking. If one qualifies, the draw engine places it after the 211 FIFA-ranked members for pot ordering.

## Data model

Each save stores a complete JSON state in SQLite, including:

- host and simulation seed
- every qualifying match
- confederation standings
- direct qualifiers
- intercontinental playoff matches
- 48 qualified teams
- pots
- group draw
- all final-tournament group matches
- group standings
- knockout rounds
- champion

## Project structure

```text
world-cup-simulator/
├── app.py
├── data.py
├── engine.py
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests/
│   └── test_engine.py
└── README.md
```

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Ranking sources

The app's July 2026 ordering was checked against FIFA's 20 July 2026 ranking update and the full July 2026 table surfaced by FotMob. FIFA also states that it has 211 member associations.
