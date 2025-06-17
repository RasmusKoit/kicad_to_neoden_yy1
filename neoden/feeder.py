from dataclasses import dataclass
from kicad import KicadComponent, ComponentInfo


@dataclass
class Feeder:
    feederNo: int
    width: int
    available: bool = True
    refs: list[str] = None


class Feeders:
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
        data = [
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
                ],
                "width": 8,
            }
        ]
        # based on package, get feeder width
        width = None
        for entry in data:
            if package.upper() in entry.get("packages"):
                width = entry.get("width")
        return width

    def toggle_feeder_availability(self, feeder_no: int):
        feeder = self.get_feeder_by_no(feeder_no)
        feeder.available = not feeder.available

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
        # Group components by (package, value)
        for component in components:
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
            width = self.get_width_by_package(group["package"])
            feeder_no = self.get_feeder_by_width(width)
            if feeder_no is not None:
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
