import csv
from pathlib import Path
from kicad import KicadComponent


class KicadParser:
    REQUIRED_HEADERS_POS = {"Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side"}
    REQUIRED_HEADERS_BOM = {"Reference", "Value", "Qty", "Height", "package"}

    def __init__(self, pos_file: Path, bom_file: Path | None = None):
        self.pos_file = pos_file
        self.bom_file = bom_file
        self.components = set[KicadComponent]()
        self.parse()

    def valid_component(self, component: KicadComponent) -> bool:
        # check for val and package if its not part of ignore list
        ignore_words = {
            "Fiducial",
            "SwitchHoles",
            "TestPoint",
            "TestPad",
            "TestPadSMD",
            "SwitchHole",
            "MouseBite",
        }
        if any(word in component.val for word in ignore_words) or any(
            word in component.package for word in ignore_words
        ):
            return False

        return True

    def __read_csv(self, headers: set[str]):
        file_to_read = (
            self.pos_file if headers == self.REQUIRED_HEADERS_POS else self.bom_file
        )
        with file_to_read.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not headers.issubset(set(reader.fieldnames or [])):
                raise ValueError(
                    f"Input file missing required headers. Required: {headers}, found: {set(reader.fieldnames or [])}"
                )
            return list(reader)

    def __parse_pos_file(self, reader: csv.DictReader) -> set[KicadComponent]:
        components = set()
        for row in reader:
            ref = row["Ref"].strip()
            val = row["Val"].strip()
            package = row["Package"].strip()
            pos_x = row["PosX"].strip()
            pos_y = row["PosY"].strip()
            rot = row["Rot"].strip()
            side = row["Side"].strip().lower()
            if side not in {"top", "bottom"}:
                raise ValueError(f"Invalid side '{side}' in row: {row}")
            if not ref or not val or not package:
                raise ValueError(f"Ref, Val, or Package cannot be empty in row: {row}")
            if ref in (c.ref for c in components):
                raise ValueError(f"Duplicate Ref '{ref}' found in the file.")
            try:
                pos_x = round(float(pos_x), 2)
                pos_y = round(float(pos_y), 2)
                rot = round(float(rot), 1)
            except ValueError as e:
                raise ValueError(f"Invalid numeric value in row: {row}") from e
            component = KicadComponent(
                ref=ref,
                val=val,
                package=package,
                pos_x=pos_x,
                pos_y=pos_y,
                rot=rot,
                side=side,
                height=None,  # Height will be set from BOM if available
            )
            if self.valid_component(component):
                components.add(component)
        return components

    def __parse_bom_file(self, reader: csv.DictReader) -> set[KicadComponent]:
        components = set()
        # each row can have multiple references, so we need to iterate over each row
        for row in reader:
            refs = row["Reference"].split(",")
            val = row.get("Value", None)
            package = row.get("package", None)
            height = row.get("Height", None)
            for ref in refs:
                ref = ref.strip()
                if not ref:
                    raise ValueError(f"Ref cannot be empty in row: {row}")
                component = KicadComponent(
                    ref=ref,
                    val=val,
                    package=package,
                    height=height,
                )
                if self.valid_component(component):
                    components.add(component)
        return components

    def __combine_components(
        self,
        pos_components: set[KicadComponent],
        bom_components: set[KicadComponent],
    ) -> set[KicadComponent]:
        combined_components = set[KicadComponent]()
        match_bom = False
        if bom_components:
            match_bom = True
        for pos in pos_components:
            bom = next((b for b in bom_components if b.ref == pos.ref), None)
            if not match_bom:
                combined_components.add(pos)
            else:
                if bom:
                    combined_components.add(
                        KicadComponent(
                            ref=pos.ref,
                            val=pos.val,
                            package=pos.package,
                            pos_x=pos.pos_x,
                            pos_y=pos.pos_y,
                            rot=pos.rot,
                            side=pos.side,
                            height=bom.height if bom.height != "" else 0,
                        )
                    )
        return combined_components

    def parse(self):
        pos_reader = self.__read_csv(self.REQUIRED_HEADERS_POS)
        bom_reader = (
            self.__read_csv(self.REQUIRED_HEADERS_BOM) if self.bom_file else None
        )
        bom_comp = self.__parse_bom_file(bom_reader) if bom_reader else None
        pos_comp = self.__parse_pos_file(pos_reader)
        self.components = self.__combine_components(pos_comp, bom_comp)
        
if __name__ == "__main__":
    pos_path = Path("examples/rev3.2-top-pos.csv")  # Change to your input file path
    bos_path = Path("examples/rev3.2.csv")  # Change to your BOM file path if needed
    parser = KicadParser(pos_file=pos_path, bom_file=bos_path)
    for comp in parser.components:
        print(comp)
