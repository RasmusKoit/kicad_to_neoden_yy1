from kicad import KicadComponent
from pathlib import Path
import csv


class Writer:
    # static NEODEN YY1 header rows written above the component table
    PREAMBLE = [
        ["NEODEN", "YY1", "P&P FILE"],
        [],
        ["PanelizedPCB", "UnitLength", "0", "UnitWidth", "0", "Rows", "1", "Columns", "1"],
        [],
        ["Fiducial", "1-X", "13.09", "1-Y", "55.01", "OverallOffsetX", "0", "OverallOffsetY", "0"],
        [],
        ["NozzleChange", "OFF", "BeforeComponent", "1", "Head1", "Drop", "Station2", "PickUp", "Station1"],
        ["NozzleChange", "OFF", "BeforeComponent", "2", "Head2", "Drop", "Station3", "PickUp", "Station2"],
        ["NozzleChange", "OFF", "BeforeComponent", "1", "Head1", "Drop", "Station1", "PickUp", "Station1"],
        ["NozzleChange", "OFF", "BeforeComponent", "1", "Head1", "Drop", "Station1", "PickUp", "Station1"],
        [],
    ]

    COLUMNS = [
        "Designator", "Comment", "Footprint", "Mid X(mm)", "Mid Y(mm)", "Rotation",
        "Head", "FeederNo", "Mount Speed(%)", "Pick Height(mm)", "Place Height(mm)",
        "Mode", "Skip",
    ]

    def __init__(
        self,
        components: list[KicadComponent],
        output: Path,
        output_dir: Path,
    ):
        self.components = components
        self.output = output
        self.output_dir = output_dir

    def create_file(self):
        output_path = self.output_dir / self.output
        with open(output_path, "w", newline="") as outfile:
            writer = csv.writer(outfile)
            for row in self.PREAMBLE:
                writer.writerow(self.pad(row))
            writer.writerow(self.COLUMNS)
            for component in self.components:
                writer.writerow(self.component_row(component))

    def pad(self, row: list) -> list:
        # every Neoden row shares the column count; pad shorter header rows with blanks
        return row + [""] * (len(self.COLUMNS) - len(row))

    def component_row(self, component: KicadComponent) -> list:
        # mount speed 100%, pick height 0, place height = component height, mode 1, no skip
        return [
            component.ref,
            component.val,
            component.package,
            component.pos_x,
            component.pos_y,
            component.rot,
            component.head,
            component.feederNo,
            100,
            0,
            component.height,
            1,
            0,
        ]
