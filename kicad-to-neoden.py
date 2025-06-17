from argparse import ArgumentParser
from pathlib import Path
from kicad import KicadParser, KicadComponent
from neoden import Feeders, Writer


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
        default=Path("examples/example-top-pos.csv"),
    )
    parser.add_argument(
        "--bom",
        "-b",
        type=Path,
        required=True,
        help="Input file path (KiCad BOM file)",
        default=Path("examples/example-top-bom.csv"),
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        required=False,
        help="Output file path (Neoden YY1 format file)",
        default=Path("output.csv"),
    )
    args = parser.parse_args()
    # check if arg is required
    pos_file = validate_file(args.pos, is_input=True, is_required=True)
    bom_file = validate_file(args.bom, is_input=True, is_required=False)
    output_file = validate_file(args.out, is_input=False, is_required=True)
    kicadParser = KicadParser(pos_file=pos_file, bom_file=bom_file)
    components = kicadParser.components
    feeders = Feeders()
    feeders.set_feeders(components)
    sorted_components = sorted(
        components, key=lambda c: (getattr(c, "feederNo", 0), str(c.ref))
    )
    feeders.show_feeders()
    writer = Writer(components=sorted_components, output=output_file)
    writer.create_file()
    
    

def validate_file(file_path: Path, is_input: bool, is_required: bool):
    if not file_path.exists() and is_input and is_required:
        print(f"Error: {file_path} does not exist.")
        exit(1)
    if not file_path.suffix == ".csv":
        print(f"Error: {file_path} must be a CSV file.")
        exit(1)
    if not file_path.is_file() and is_input and is_required:
        print(f"Error: {file_path} is not a valid file.")
        exit(1)
    if not file_path.parent.exists():
        print(f"Error: Output directory {file_path.parent} does not exist.")
        exit(1)
    return file_path


if __name__ == "__main__":
    main()
