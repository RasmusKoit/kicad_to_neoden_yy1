class ComponentInfo:
    """
    ComponentInfo provides a mapping between common electronic component packages, their types, and typical heights (in millimeters).
    Attributes:
        data (dict): Nested dictionary mapping package names (str) to component types (str) and their heights (float).
        prefix_map (dict): Maps common schematic designators/prefixes (e.g., 'R', 'C', 'D') to component type strings.
    Methods:
        get_height(descriptor: str = None, component_type: str = None, package: str = None) -> float | None:
            Returns the height (in mm) for a given component, specified either by a descriptor string (e.g., "R_0603")
            or by providing both component_type and package. Returns None if not found.
        list_packages() -> list[str]:
            Returns a sorted list of all known package names.
        list_components(package: str) -> dict[str, float]:
            Returns a dictionary of component types and their heights for a given package. Returns an empty dict if the package is unknown.
        list_component_types() -> list[str]:
            Returns a sorted list of all unique component types across all packages.
        list_components_by_type(component_type: str) -> dict[str, float]:
            Returns a dictionary mapping package names to heights for a given component type.
    """

    def __init__(self):
        self.data = {
            # Chip packages
            "0201": {
                "resistor": 0.25,
                "capacitor": 0.30,
                "inductor": 0.30,
                "ferrite_bead": 0.35,
                "led": 0.40,
            },
            "0402": {
                "resistor": 0.35,
                "capacitor": 0.50,
                "inductor": 0.50,
                "ferrite_bead": 0.55,
                "led": 0.50,
            },
            "0603": {
                "resistor": 0.45,
                "capacitor": 0.65,
                "inductor": 0.80,
                "ferrite_bead": 0.70,
                "filter": 0.75,
                "led": 0.60,
            },
            "0805": {
                "resistor": 0.55,
                "capacitor": 0.85,
                "inductor": 1.00,
                "ferrite_bead": 0.90,
                "filter": 1.00,
                "led": 0.90,
            },
            "1206": {
                "resistor": 0.70,
                "capacitor": 1.00,
                "led": 1.10,
            },
            "1210": {"capacitor": 1.25},
            "1812": {"capacitor": 1.50},
            "2010": {"resistor": 0.75},
            "2512": {"resistor": 0.85},
            # Ferrites, filters, inductors (generic chip sizes)
            "0808": {"ferrite_bead": 1.10, "filter": 1.20, "inductor": 1.30},
            # Diode packages
            "SOD-523": {"diode": 0.80},
            "SOD-323": {"diode": 1.10},
            "SOD-123": {"diode": 1.80},
            "SMA": {"diode": 2.60},
            "SMB": {"diode": 2.75},
            "SMC": {"diode": 2.85},
            # Transistors & small signal
            "SOT-23": {"transistor": 1.20, "diode": 1.20, "regulator": 1.20},
            "SOT-323": {"transistor": 1.10},
            "SOT-523": {"transistor": 0.80},
            "SOT-223": {"regulator": 1.80},
            "TO-220": {"transistor": 4.50, "regulator": 4.50},
            # IC packages
            "SOIC-8": {"ic": 1.75},
            "SOIC-14": {"ic": 1.75},
            "TSSOP-8": {"ic": 1.20},
            "TSSOP-14": {"ic": 1.20},
            "QFN-16": {"ic": 1.00},
            "QFN-32": {"ic": 1.00},
            "DFN-6": {"ic": 0.80},
            "DFN-8": {"ic": 0.80},
            "QFP-64": {"ic": 2.00},
            "LQFP-64": {"ic": 1.40},
            # Power packages
            "DPAK": {"mosfet": 2.50},
            "D2PAK": {"mosfet": 2.70},
            # Hotswap socket
            "KHS": {"hotswap_socket": 1.80},
            "HS": {"hotswap_socket": 1.80},  # fallback for Kailh sockets
            "MIKEHOLSCHER": {"cpg1316s01d02": 2.40},  # specific laptop switch
        }

        self.prefix_map = {
            "R": "resistor",
            "C": "capacitor",
            "FB": "ferrite_bead",
            "L": "inductor",
            "F": "filter",
            "D": "diode",
            "Z": "zener",
            "S": "schottky",
            "Q": "transistor",
            "U": "ic",
            "U?": "ic",  # fallback if unknown
            "IC": "ic",
            "M": "mosfet",
            "VR": "regulator",
            "LED": "led",
            "KHS": "hotswap_socket",
            "KAILH": "hotswap_socket",  # for hotswap sockets
            "CPG1316S01D02": "cpg1316s01d02",  # specific hotswap socket
        }

    def get_height(
        self, *, descriptor: str = None, component_type: str = None, package: str = None
    ) -> float | None:
        """
        Get the height (in mm) for a given component.

        Args:
            descriptor (str, optional): A string like "R_0603" to infer type and package.
            component_type (str, optional): The type of component (e.g., "resistor").
            package (str, optional): The package name (e.g., "0603").

        Returns:
            float | None: The height in millimeters if found, otherwise None.
        """
        if descriptor:
            # Ex: R_0402_1005Metric
            parts = descriptor.split("_")
            if len(parts) < 2:
                return None
            prefix = parts[0]
            package = parts[1]
            component_type = self.prefix_map.get(prefix.upper(), prefix.lower())
        if component_type and package:
            #
            return self.data.get(package.upper(), {}).get(component_type.lower())
        return None

    def list_packages(self) -> list[str]:
        """
        Returns a sorted list of all known package names.

        Returns:
            list[str]: Sorted list of package names.
        """
        return sorted(self.data.keys())

    def list_components(self, package: str) -> dict[str, float]:
        """
        Returns a dictionary of component types and their heights for a given package.

        Args:
            package (str): The package name.

        Returns:
            dict[str, float]: Mapping of component types to heights for the package, or empty dict if unknown.
        """
        package = package.upper()
        if package not in self.data:
            return {}
        return {k: v for k, v in self.data[package].items() if v is not None}

    def list_component_types(self) -> list[str]:
        """
        Returns a sorted list of all unique component types across all packages.

        Returns:
            list[str]: Sorted list of component types.
        """
        component_types = set()
        for package in self.data.values():
            component_types.update(package.keys())
        return sorted(component_types)

    def list_components_by_type(self, component_type: str) -> dict[str, float]:
        """
        Returns a dictionary mapping package names to heights for a given component type.

        Args:
            component_type (str): The component type (e.g., "resistor").

        Returns:
            dict[str, float]: Mapping of package names to heights for the given component type.
        """
        component_type = component_type.lower()
        components = {}
        for package, types in self.data.items():
            if component_type in types:
                components[package] = types[component_type]
        return components
    
    def get_package(self, descriptor: str) -> str | None:
        """
        Get the package name from a descriptor string.

        Args:
            descriptor (str): A string like "R_0603" to infer the package.

        Returns:
            str | None: The package name if found, otherwise None.
        """
        parts = descriptor.split("_")
        if len(parts) < 2:
            return None
        return parts[1].upper()


class KicadComponent:
    """
    Represents a KiCad component with its attributes.

    Attributes:
        ref (str): Reference designator of the component.
        val (str): Value or part number of the component.
        package (str): Package type of the component.
        pos_x (float): X position of the component in mm.
        pos_y (float): Y position of the component in mm.
        rot (float): Rotation angle of the component in degrees.
        side (str): Side of the board where the component is placed ('top' or 'bottom').
        height (float): Height of the component in mm.
    """

    def __init__(
        self,
        ref: str,
        val: str = None,
        package: str = None,
        pos_x: float = None,
        pos_y: float = None,
        rot: float = None,
        side: str = None,
        height: float = None,
        feederNo: int = 0,
        head: int = 0,
    ):

        self.ref = ref
        self.val = val
        self.package = package
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.rot = rot
        self.side = side
        self.height = height
        self.feederNo = feederNo
        self.head = head
        # If height is provided, set it; otherwise, calculate it using ComponentInfo first by descriptor and then by package and type
        if height is None:
            heights = ComponentInfo()
            self.height = heights.get_height(descriptor=package)
            if self.height is None:
                self.height = heights.get_height(
                    component_type=self.val, package=self.package
                )

    def __repr__(self):
        return (
            f"KicadComponent(ref={self.ref}, val={self.val}, package={self.package}, "
            f"pos_x={self.pos_x}, pos_y={self.pos_y}, rot={self.rot}, side={self.side}, height={self.height}, feederNo={self.feederNo}, head={self.head})"
        )

    def set_feeder(self, feederNo: int):
        """
        Set the feeder number for the component.

        Args:
            feederNo (int): The feeder number to set.
        """
        self.feederNo = feederNo

    def set_head(self, headNo: int):
        """
        Set the head number for the component.

        Args:
            headNo (int): The head number to set.
        """
        if headNo < 1 or headNo > 4:
            raise ValueError("Head number must be between 1 and 4.")
        self.head = headNo
    
    


if __name__ == "__main__":
    # Example usage
    comp = KicadComponent(
        ref="R1", val="10k", package="0603", pos_x=1.0, pos_y=2.0, rot=0.0, side="top"
    )
    print(comp)
    heights = ComponentInfo()
    print("Height of R_0603:", heights.get_height(descriptor="R_0603"))
    print(
        "Height of 0603 resistor:",
        heights.get_height(component_type="resistor", package="0603"),
    )
    print("List of all packages:", heights.list_packages())
    print("Components in 0603 package:", heights.list_components("0603"))
    print("All component types:", heights.list_component_types())
    print("Components by type 'resistor':", heights.list_components_by_type("resistor"))
    print(
        "Adding component by descriptor 'C_0402':",
        heights.get_height(descriptor="C_0402"),
    )
    print(
        "Adding component by type 'capacitor' and package '0402':",
        heights.get_height(component_type="capacitor", package="0402"),
    )
    print("Height of unknown component:", heights.get_height(descriptor="X_9999"))
    print(heights.get_height(descriptor="CPG1316S01D02_mikeholscher"))
    print(heights.get_height(component_type="CPG1316S01D02", package="MIKEHOLSCHER"))
    print("Package from descriptor 'R_0603':", heights.get_package("R_0603"))
    print("Package from descriptor 'C_0402':", heights.get_package("C_0402"))
    print("Package from descriptor 'D_0805':", heights.get_package("D_0805"))
    print("Package from descriptor 'D_SOD-523':", heights.get_package("D_SOD-523"))