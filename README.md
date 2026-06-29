# kicad_to_neoden_yy1

A simple Python tool to convert KiCad position and BOM files into Neoden YY1 pick-and-place CSV format, with automatic feeder assignment and component height handling.

---

## Features

- **Converts KiCad position files** (`.csv`) to Neoden YY1 format.
- **Supports BOM files** for accurate component height assignment.
- **Automatic feeder assignment** based on package size (e.g., 8mm for passives).
- **Component grouping** by value and package for efficient feeder usage.
- **Customizable and extensible** Python codebase.

---

## Requirements

- Python 3.10 or newer

---

## Installation

Clone this repository and install dependencies (if any):

```sh
git clone https://github.com/RasmusKoit/kicad_to_neoden_yy1.git
cd kicad_to_neoden_yy1
python3 kicad-to-neoden.py -h
```

---

## Sharing one machine across projects

When several boards run on the same machine, use `--existing` / `-e` to avoid
re-using feeders that are already loaded. Each value is either a feeder range to
reserve or a previously generated output file:

```sh
# Reserve specific feeders (no auto-assignment to them)
python3 kicad-to-neoden.py -p board.csv -b bom.csv -o projectB.csv -e "1-10,15"

# Reserve the feeders an earlier project already uses, and reuse its reels for
# matching parts (same package + value, e.g. a 0603 5.1k resistor)
python3 kicad-to-neoden.py -p board.csv -b bom.csv -o projectB.csv -e outputs/projectA.csv

# Both forms can be combined
python3 kicad-to-neoden.py -p board.csv -b bom.csv -o projectB.csv -e outputs/projectA.csv "20-22"
```

Parts that match a loaded feeder reuse it; everything else is assigned to the
remaining free feeders.

---

## Feeder widths for larger parts (`--pcb`)

Passives auto-assign from a built-in 8mm package table, but larger parts
(QFNs, modules, connectors) have no fixed package→width mapping. Pass the KiCad
PCB and the tool reads each footprint's body size from its geometry and derives
the carrier-tape width (8/12/16/24mm) via the EIA-481 size rule:

```sh
python3 kicad-to-neoden.py -p board.csv -b bom.csv -o out.csv --pcb board.kicad_pcb
```

Resolution order per part: 8mm package catalog → PCB body size → a size embedded
in the footprint name (e.g. `..._5x5mm_...`) → otherwise left at feeder 0 to place
by hand. The derived width is a conservative estimate (it uses the larger body
edge); verify boundary cases.

---

## Printable feeder sheet (`--pdf`)

Add `--pdf` to also write a single-page feeder-loading sheet next to the output
CSV (same name, `.pdf` extension). Each feeder is listed with its value,
footprint and the designators that go on it:

```sh
python3 kicad-to-neoden.py -p board.csv -b bom.csv -o out.csv --pdf   # -> out.pdf
```

This requires `reportlab` (`pip install -r requirements.txt`); the converter
itself has no dependencies.