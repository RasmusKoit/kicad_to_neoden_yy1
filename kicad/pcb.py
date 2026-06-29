import re
from pathlib import Path

# tokens of a KiCad s-expression: quoted strings, parens, or bare atoms
TOKEN_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+')


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def parse_sexpr(tokens: list[str]):
    # build the first complete nested list from the token stream
    root = []
    stack = [root]
    for token in tokens:
        if token == "(":
            node = []
            stack[-1].append(node)
            stack.append(node)
        elif token == ")":
            if len(stack) > 1:
                stack.pop()
        else:
            if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
                token = token[1:-1]
            stack[-1].append(token)
    return root[0] if root else []


def find_all(node, name):
    # yield every nested list whose first element is name
    if isinstance(node, list):
        if node and node[0] == name:
            yield node
        for child in node:
            if isinstance(child, list):
                yield from find_all(child, name)


def footprint_reference(footprint) -> str | None:
    for prop in find_all(footprint, "property"):
        if len(prop) >= 3 and prop[1] == "Reference":
            return prop[2]
    for txt in find_all(footprint, "fp_text"):  # older KiCad
        if len(txt) >= 3 and txt[1] == "reference":
            return txt[2]
    return None


def points_on_layer(footprint, layer: str) -> list[tuple[float, float]]:
    # collect graphic coordinates of fp_* items drawn on the given layer
    points = []
    for node in footprint:
        if not isinstance(node, list) or not node:
            continue
        if node[0] not in ("fp_line", "fp_rect", "fp_poly", "fp_circle"):
            continue
        node_layer = next(
            (c[1] for c in node if isinstance(c, list) and c and c[0] == "layer"),
            None,
        )
        if node_layer != layer:
            continue
        for tag in ("start", "end", "center", "mid", "xy"):
            for sub in find_all(node, tag):
                try:
                    points.append((float(sub[1]), float(sub[2])))
                except (IndexError, ValueError):
                    pass
    return points


def pad_points(footprint) -> list[tuple[float, float]]:
    # last-resort body estimate: bounding box of pad extents
    points = []
    for pad in find_all(footprint, "pad"):
        at = next((c for c in pad if isinstance(c, list) and c and c[0] == "at"), None)
        size = next((c for c in pad if isinstance(c, list) and c and c[0] == "size"), None)
        if not at or not size:
            continue
        try:
            x, y, sx, sy = float(at[1]), float(at[2]), float(size[1]), float(size[2])
        except (IndexError, ValueError):
            continue
        points.append((x - sx / 2, y - sy / 2))
        points.append((x + sx / 2, y + sy / 2))
    return points


def bounding_box(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return max(xs) - min(xs), max(ys) - min(ys)


def read_footprint_bodies(pcb_path: Path) -> dict[str, tuple[float, float]]:
    """
    Parse a .kicad_pcb and return {reference: (length_mm, width_mm)}.

    The body size is the bounding box of the fabrication outline (F.Fab/B.Fab),
    falling back to the courtyard and then to the pad extents.
    """
    root = parse_sexpr(tokenize(Path(pcb_path).read_text(encoding="utf-8")))
    bodies = {}
    for footprint in find_all(root, "footprint"):
        ref = footprint_reference(footprint)
        if not ref:
            continue
        points = (
            points_on_layer(footprint, "F.Fab")
            or points_on_layer(footprint, "B.Fab")
            or points_on_layer(footprint, "F.CrtYd")
            or points_on_layer(footprint, "B.CrtYd")
            or pad_points(footprint)
        )
        if len(points) < 2:
            continue
        w, h = bounding_box(points)
        bodies[ref] = (max(w, h), min(w, h))
    return bodies
