from kicad import KicadComponent
from pathlib import Path
import csv


class Writer:
    def __init__(
        self,
        components: list[KicadComponent],
        output: Path,
    ):
        self.components = components
        self.output = output

    def create_file(self):
        with open(self.output, "w", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(
                ["NEODEN", "YY1", "P&P FILE", "", "", "", "", "", "", "", ""]
            )
            writer.writerow(["", "", "", "", "", "", "", "", "", "", ""])
            writer.writerow(
                [
                    "PanelizedPCB",
                    "UnitLength",
                    "0",
                    "UnitWidth",
                    "0",
                    "Rows",
                    "1",
                    "Columns",
                    "1",
                    "",
                    "",
                    "",
                    "",
                ]
            )
            writer.writerow(["", "", "", "", "", "", "", "", "", "", ""])
            writer.writerow(
                [
                    "Fiducial",
                    "1-X",
                    "0.00",
                    "1-Y",
                    "0.00",
                    "OverallOffsetX",
                    "0",
                    "OverallOffsetY",
                    "0",
                    "",
                    "",
                    "",
                ]
            )
            writer.writerow(["", "", "", "", "", "", "", "", "", "", ""])
            writer.writerow(
                [
                    "NozzleChange",
                    "OFF",
                    "BeforeComponent",
                    "1",
                    "Head1",
                    "Drop",
                    "Station1",
                    "PickUp",
                    "Station1",
                    "",
                    "",
                    "",
                ]
            )
            writer.writerow(
                [
                    "NozzleChange",
                    "OFF",
                    "BeforeComponent",
                    "1",
                    "Head1",
                    "Drop",
                    "Station1",
                    "PickUp",
                    "Station1",
                    "",
                    "",
                    "",
                ]
            )
            writer.writerow(
                [
                    "NozzleChange",
                    "OFF",
                    "BeforeComponent",
                    "1",
                    "Head1",
                    "Drop",
                    "Station1",
                    "PickUp",
                    "Station1",
                    "",
                    "",
                    "",
                ]
            )
            writer.writerow(
                [
                    "NozzleChange",
                    "OFF",
                    "BeforeComponent",
                    "1",
                    "Head1",
                    "Drop",
                    "Station1",
                    "PickUp",
                    "Station1",
                    "",
                    "",
                    "",
                ]
            )
            writer.writerow(["", "", "", "", "", "", "", "", "", "", ""])
            writer.writerow(
                [
                    "Designator",
                    "Comment",
                    "Footprint",
                    "Mid X(mm)",
                    "Mid Y(mm)",
                    "Rotation",
                    "Head",
                    "FeederNo",
                    "Mount Speed(%)",
                    "Pick Height(mm)",
                    "Place Height(mm)",
                    "Mode",
                    "Skip",
                ]
            )
            for c in self.components:
                writer.writerow(
                    [
                        c.ref,
                        c.val,
                        c.package,
                        c.pos_x,
                        c.pos_y,
                        c.rot,
                        c.head,
                        c.feederNo,
                        100,
                        0,
                        c.height,
                        1,
                        0,
                    ]
                )
