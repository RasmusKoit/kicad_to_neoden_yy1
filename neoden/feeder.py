import re
from dataclasses import dataclass
from kicad import KicadComponent, ComponentInfo


# a body size like "5x5mm" or "2.6x1.6x0.5mm" embedded in a footprint/description
DIM_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)(?:\s*[xX*]\s*\d+(?:\.\d+)?)?\s*mm",
    re.IGNORECASE,
)


def eia481_width(edge_mm: float) -> int | None:
    # smallest standard carrier tape (mm) for a body whose larger edge is edge_mm
    # (EIA-481; anchored on SOT-23 2.9->8, QFN 5x5->12, 8x8 module->16)
    if edge_mm <= 4.0:
        return 8
    if edge_mm <= 7.0:
        return 12
    if edge_mm <= 11.0:
        return 16
    if edge_mm <= 15.0:
        return 24
    return None


def width_from_dimensions(text: str) -> int | None:
    # derive a feeder width from a body size found in a footprint name or description
    match = DIM_RE.search(text or "")
    if not match:
        return None
    edge = max(float(match.group(1)), float(match.group(2)))
    return eia481_width(edge)


@dataclass
class Feeder:
    feederNo: int
    width: int
    available: bool = True
    refs: list[str] = None


class Feeders:
    # packages that fit on each feeder tape width (mm)
    PACKAGE_WIDTHS = [
        {
            "packages": [
                "0201",
                "0402",
                "0603",
                "0805",
                "1206",
                "1210",
                "1812",
                "SOD-523",
                "SOD-323",
                "SOD-123",
                "SOT-23",
                "SOT-323",
                "SOT-523",
            ],
            "width": 8,
        }
    ]

    def __init__(self):
        self.feeders = [
            *(Feeder(i, width=8) for i in range(1, 18)),
            *(Feeder(i, width=12) for i in range(18, 22)),
            *(Feeder(i, width=16) for i in range(22, 23)),
            *(Feeder(i, width=8) for i in range(23, 44)),
            *(Feeder(i, width=16) for i in range(44, 46)),
            *(Feeder(i, width=12) for i in range(46, 48)),
            *(Feeder(i, width=8) for i in range(48, 51)),
        ]
        # (package, value) -> feederNo for parts already loaded by existing projects
        self.preloaded = {}
        # feederNo -> (package, value) to detect conflicting existing projects
        self.feeder_parts = {}
        # ref -> feeder width (mm) derived from the KiCad PCB footprint geometry
        self.width_overrides = {}

    def get_feeder_by_width(self, width: int):
        # return feederNo for available feeders with the specified width
        for f in self.feeders:
            if f.width == width and f.available:
                return f.feederNo

    def get_available_feeders(self):
        return [feeder for feeder in self.feeders if feeder.available]

    def get_feeder_by_no(self, feeder_no: int):
        for feeder in self.feeders:
            if feeder.feederNo == feeder_no:
                return feeder
        return None

    def get_feeder_by_ref(self, ref: str):
        for feeder in self.feeders:
            if feeder.refs and ref in feeder.refs:
                return feeder
        return None

    def get_width_by_package(self, package: str):
        # based on package, get feeder width
        width = None
        for entry in self.PACKAGE_WIDTHS:
            if package.upper() in entry["packages"]:
                width = entry["width"]
        return width

    def toggle_feeder_availability(self, feeder_no: int):
        feeder = self.get_feeder_by_no(feeder_no)
        if feeder is None:
            raise ValueError(f"Feeder {feeder_no} not found.")
        feeder.available = not feeder.available

    def skip_feeders(self, feeder_nos: list[int]):
        # mark feeders as unavailable so they are not assigned, useful when
        # sharing a machine across projects with feeders already loaded
        for feeder_no in feeder_nos:
            feeder = self.get_feeder_by_no(feeder_no)
            if feeder is None:
                raise ValueError(f"Feeder {feeder_no} not found.")
            feeder.available = False

    def load_existing(self, entries: list[dict]):
        # reserve feeders already used by an existing project and remember which
        # part sits on each, so matching components reuse the same feeder
        info = ComponentInfo()
        for entry in entries:
            feeder_no = entry["feederNo"]
            if feeder_no <= 0:  # feeder 0 means unmapped, ignore
                continue
            feeder = self.get_feeder_by_no(feeder_no)
            if feeder is None:
                continue
            package = info.get_package(entry["package"]) or entry["package"]
            key = (package, entry["value"])
            # one feeder cannot physically hold two different reels
            loaded = self.feeder_parts.get(feeder_no)
            if loaded is not None and loaded != key:
                raise ValueError(
                    f"Feeder {feeder_no} is used by both {loaded[1]} {loaded[0]} and "
                    f"{key[1]} {key[0]} across existing projects."
                )
            # same part recorded on a different feeder, warn and keep the latest
            previous = self.preloaded.get(key)
            if previous is not None and previous != feeder_no:
                print(
                    f"Warning: {key[1]} {key[0]} is on feeders {previous} and {feeder_no} "
                    f"across existing projects, using {feeder_no}."
                )
            self.preloaded[key] = feeder_no
            self.feeder_parts[feeder_no] = key
            feeder.available = False

    def add_refs_to_feeder(self, feeder_no: int, refs: list[str]):
        feeder = self.get_feeder_by_no(feeder_no)
        if feeder:
            if feeder.refs is None:
                feeder.refs = []
            feeder.refs.extend(refs)
        else:
            raise ValueError(f"Feeder {feeder_no} not found.")

    def show_feeders(self):
        for feeder in self.feeders:
            print(feeder)

    def set_feeders(self, components: set[KicadComponent]):
        info = ComponentInfo()
        groups = []
        # Group components by (package, value); sort first so feeder numbers are
        # assigned deterministically (components is an unordered set)
        ordered = sorted(
            components, key=lambda c: (str(c.package), str(c.val), str(c.ref))
        )
        for component in ordered:
            package = info.get_package(component.package)
            if not package:
                package = component.package
            # Check if this group already exists
            exists = any(
                group["package"] == package and group["value"] == component.val
                for group in groups
            )
            if not exists:
                groups.append(
                    {
                        "package": package,
                        "value": component.val,
                        "refs": [component.ref],
                        "components": [component],  # Track components in this group
                    }
                )
            else:
                for group in groups:
                    if group["package"] == package and group["value"] == component.val:
                        group["refs"].append(component.ref)
                        group["components"].append(component)
                        break

        # Assign each group to a feeder and set feeder_no on each component
        for group in groups:
            # reuse the feeder an existing project already loaded this part on
            feeder_no = self.preloaded.get((group["package"], group["value"]))
            if feeder_no is not None:
                self.add_refs_to_feeder(feeder_no, group["refs"])
                for comp in group["components"]:
                    comp.set_feeder(feeder_no)
                continue
            width = self.get_width_by_package(group["package"])
            if width is None and self.width_overrides:
                # body size measured from the KiCad PCB footprint geometry
                for ref in group["refs"]:
                    if ref in self.width_overrides:
                        width = self.width_overrides[ref]
                        break
            if width is None:
                # fall back to a body size in the footprint name (e.g. "...5x5mm...")
                width = width_from_dimensions(group["components"][0].package)
            if width is None:
                # unknown package width, leave unassigned to place by hand
                print(
                    f"Warning: no known feeder width for {group['package']} {group['value']} "
                    f"({len(group['refs'])} parts): {', '.join(group['refs'])}"
                )
                continue
            feeder_no = self.get_feeder_by_width(width)
            if feeder_no is None:
                raise ValueError(
                    f"Not enough free {width}mm feeders to place {group['package']} "
                    f"{group['value']} ({len(group['refs'])} parts): {', '.join(group['refs'])}."
                )
            self.add_refs_to_feeder(feeder_no, group["refs"])
            self.toggle_feeder_availability(feeder_no)  # Mark as used
            # Set feeder_no for each component in this group
            for comp in group["components"]:
                comp.set_feeder(feeder_no)


if __name__ == "__main__":
    feeders = Feeders()
    print(feeders.get_available_feeders())
    feeders.toggle_feeder_availability(1)
    print(feeders.get_available_feeders())
    feeders.add_refs_to_feeder(1, ["R1", "R2"])
    print(feeders.get_feeder_by_no(1))
    print(feeders.get_feeder_by_ref("R1"))
    print(feeders.get_feeder_by_width(8))
    print(feeders.get_feeder_by_width(12))
    print(feeders.get_feeder_by_width(16))
