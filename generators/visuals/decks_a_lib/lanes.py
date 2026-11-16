"""Swimlane helper: lane rectangles carry the team/role names; step boxes sit inside lanes and
never name their owner. ``grouped=True`` puts each lane (body, header and steps) in a group shape
named 'Lane: <name>'."""
from __future__ import annotations

EMU = 914400.0


class Lane:
    def __init__(self, s, canvas, name, x, y, w, h, header_w):
        self.s = s
        self.canvas = canvas
        self.name = name
        self.x, self.y, self.w, self.h = x, y, w, h
        self.header_w = header_w
        self.steps = {}

    @property
    def group_name(self):
        return f"Lane: {self.name}"

    def step(self, x, text, w=1.3, h=0.78, style="step", row=0, rows=1, size=10, bold=False, **kw):
        band = self.h / rows
        y = self.y + row * band + (band - h) / 2
        shp = self.canvas.box(x, y, w, h, text, style=style, size=size, bold=bold, **kw)
        self.steps[text] = shp
        return shp

    def geometry_note(self, shp) -> str:
        sx, sy = shp.left / EMU, shp.top / EMU
        sw, sh = shp.width / EMU, shp.height / EMU
        return (f"geometry (inches): step box x={sx:.2f}-{sx + sw:.2f}, y={sy:.2f}-{sy + sh:.2f} lies inside "
                f"lane '{self.name}' band x={self.x:.2f}-{self.x + self.w:.2f}, y={self.y:.2f}-{self.y + self.h:.2f}")


def swimlane(s, names, x=0.5, y=1.45, w=12.33, heights=None, header_w=1.75, grouped=False,
             header_fill="navy2", header_size=11):
    heights = heights or [1.2] * len(names)
    lanes = []
    yy = y
    for i, (name, h) in enumerate(zip(names, heights)):
        canvas = s.group(f"Lane: {name}") if grouped else s
        canvas.rect(x, yy, w, h, fill="grey_l" if i % 2 == 0 else "white", line="grey_m",
                    name=f"Lane body {i + 1}")
        canvas.box(x, yy, header_w, h, name, style="tile", fill=header_fill, color="white",
                   size=header_size, bold=True, name=f"Lane header {i + 1}")
        lanes.append(Lane(s, canvas, name, x, yy, w, h, header_w))
        yy += h
    return lanes
