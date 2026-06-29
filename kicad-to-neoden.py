from argparse import ArgumentParser
from pathlib import Path
import csv
from kicad import KicadParser, read_footprint_bodies
from neoden import Feeders, Writer, eia481_width, write_feeder_pdf


def main():
    parser = ArgumentParser(
        description="Convert KiCad csv position files to Neoden YY1 format."
    )
    parser.add_argument(
        "--pos",
        "-p",
        type=Path,
        required=True,
        help="Input file path (KiCad csv position file)",
    )
    parser.add_argument(
        "--bom",
        "-b",
        type=Path,
        required=True,
        help="Input file path (KiCad BOM file)",
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        required=False,
        help="Output file path (Neoden YY1 format file)",
        default=Path("output.csv"),
    )
    parser.add_argument(
        "--output-dir",
        "-d",
        type=Path,
        required=False,
        help="Output directory path (Neoden YY1 format file)",
        default=Path("outputs")
    )
    parser.add_argument(
        "--pcb",
        type=Path,
        required=False,
        help=(
            "Optional KiCad .kicad_pcb file. Body sizes are read from the footprint "
            "geometry to derive feeder widths for packages not in the 8mm catalog."
        ),
        default=None,
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help=(
            "Also write a printable, single-page feeder loading sheet next to the "
            "output file (same name, .pdf extension)."
        ),
    )
    parser.add_argument(
        "--existing",
        "-e",
        type=str,
        nargs="*",
        required=False,
        help=(
            "Existing project output file(s) and/or feeder ranges (e.g. '1-10,15') to reserve. "
            "Feeders used by an existing project are skipped, and parts matching that project "
            "(same package and value) reuse its feeders. Useful when sharing a machine across projects."
        ),
        default=[],
    )
    args = parser.parse_args()
    # check if arg is required
    pos_file = validate_file(args.pos, is_input=True, is_required=True)
    bom_file = validate_file(args.bom, is_input=True, is_required=False)
    output_file = validate_file(args.out, is_input=False, is_required=True)
    output_dir = validate_file(args.output_dir, is_input=False, is_required=True, is_dir=True)
    kicadParser = KicadParser(pos_file=pos_file, bom_file=bom_file)
    components = kicadParser.components
    feeders = Feeders()
    if args.pcb is not None:
        feeders.width_overrides = read_pcb_widths(args.pcb)
    for token in args.existing:
        if token.lower().endswith(".csv") or Path(token).is_file():
            existing_file = validate_file(Path(token), is_input=True, is_required=True)
            feeders.load_existing(read_neoden_output(existing_file))
        else:
            feeders.skip_feeders(parse_feeder_list(token))
    feeders.set_feeders(components)
    sorted_components = sorted(
        components, key=lambda c: (getattr(c, "feederNo", 0), str(c.ref))
    )
    writer = Writer(components=sorted_components, output=output_file, output_dir=output_dir)
    writer.create_file()
    if args.pdf:
        write_feeder_pdf(sorted_components, output_dir / output_file.with_suffix(".pdf"))


def read_pcb_widths(pcb_path: Path) -> dict:
    # read footprint body sizes from a .kicad_pcb and map each ref to a feeder
    # width (mm) via the EIA-481 body-size rule
    if not pcb_path.is_file():
        print(f"Error: {pcb_path} does not exist.")
        exit(1)
    bodies = read_footprint_bodies(pcb_path)
    if not bodies:
        print(f"Warning: no footprints found in {pcb_path}; is it a .kicad_pcb file?")
    widths = {}
    for ref, (length, _) in bodies.items():
        width = eia481_width(length)
        if width is not None:
            widths[ref] = width
    return widths


def read_neoden_output(path: Path) -> list[dict]:
    # parse a previously generated Neoden YY1 file into {value, package, feederNo}
    # entries, so the loaded feeders of an existing project can be reused
    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header_idx = next(
        (i for i, row in enumerate(rows) if row and row[0] == "Designator"),
        None,
    )
    if header_idx is None:
        print(f"Error: {path} is not a valid Neoden output file (no component table).")
        exit(1)
    # map by column name so the reader survives any column reordering
    columns = {name.strip(): i for i, name in enumerate(rows[header_idx])}
    try:
        value_col = columns["Comment"]
        package_col = columns["Footprint"]
        feeder_col = columns["FeederNo"]
    except KeyError as missing:
        print(f"Error: {path} is missing the {missing} column.")
        exit(1)
    last_col = max(value_col, package_col, feeder_col)
    entries = []
    for row in rows[header_idx + 1:]:
        if len(row) <= last_col or not row[0].strip():
            continue
        try:
            feeder_no = int(row[feeder_col])
        except ValueError:
            continue
        entries.append(
            {
                "value": row[value_col].strip(),
                "package": row[package_col].strip(),
                "feederNo": feeder_no,
            }
        )
    return entries


def parse_feeder_list(spec: str) -> list[int]:
    # parse a spec like "1-10,15,20-22" into a list of feeder numbers
    feeders = set()
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            if "-" in token:
                start, end = token.split("-", 1)
                feeders.update(range(int(start), int(end) + 1))
            else:
                feeders.add(int(token))
        except ValueError:
            print(f"Error: invalid feeder '{token}' in --existing.")
            exit(1)
    return sorted(feeders)


def validate_file(file_path: Path, is_input: bool, is_required: bool, is_dir: bool = False) -> Path:
    if not file_path.exists() and is_input and is_required:
        print(f"Error: {file_path} does not exist.")
        exit(1)
    if not file_path.suffix == ".csv" and not is_dir:
        print(f"Error: {file_path} must be a CSV file.")
        exit(1)
    if not file_path.is_file() and is_input and is_required:
        print(f"Error: {file_path} is not a valid file.")
        exit(1)
    if not file_path.parent.exists():
        print(f"Error: Output directory {file_path.parent} does not exist.")
        exit(1)
    if is_dir and not file_path.is_dir():
        print(f"Error: {file_path} is not a valid directory.")
        exit(1)
    return file_path


if __name__ == "__main__":
    main()
