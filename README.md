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