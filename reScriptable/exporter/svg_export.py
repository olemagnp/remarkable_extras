from typing import Iterable, Optional, Text, TextIO, Tuple, Union

import os
import math
from .line_reader import RMDocument, RMStroke, RMPoint, RMPage

class Colors:
    YELLOW = 'rgb(255, 255, 0)'
    LIGHT_GRAY = 'rgb(190, 190, 190)'
    GRAY = 'rgb(120, 120, 120)'
    DARK_GRAY = 'rgb(80, 80, 80)'
    BLACK = 'rgb(0, 0, 0)'
    WHITE = 'rgb(255, 255, 255)'

class RMPen:
    PEN_TYPES = {
        0: 'brush',
        1: 'pencil-tilt',
        2: 'pen',
        3: 'marker',
        4: 'fineliner',
        5: 'highlighter',
        6: 'eraser',
        7: 'pencil-sharp',
        8: 'erase-area',
        12: 'paint',
        13: 'mechanical pencil',
        14: 'pencil',
        15: 'ballpoint',
        16: 'marker',
        17: 'fineliner',
        18: 'highlighter',
        21: 'calligraphy',
    }

    def __init__(self, idx, output: TextIO, cmap):
        try:
            self.kind = RMPen.PEN_TYPES[idx]
        except KeyError:
            raise ValueError(f"Found unknown pen type: '{idx}'")

        self.cmap = cmap
        self.output = output

    def draw(self, stroke: RMStroke):
        if len(stroke.points) <= 2:
            return

        if abs(stroke.base_size - 1.875) < 1e-8:
            stroke_size = 0
        elif abs(stroke.base_size - 2.0) < 1e-8:
            stroke_size = 1
        else:
            stroke_size = 2

        color = self.cmap[self.kind if self.kind in self.cmap else stroke.color]
        if self.kind == 'ballpoint':
            max_width = [2, 4, 6][stroke_size]
            opacity = 1

            width = lambda p: max_width * (p.pressure * .6 + .4)

            points = [(p.x, p.y, width(p), opacity, color) for p in stroke.points]
            self.draw_combined(points)

        elif self.kind == 'fineliner':
            width = [2, 3, 5][stroke_size]
            opacity = 1

            points = [(p.x, p.y) for p in stroke.points]
            self.draw_single(points, color, width, opacity)

        elif self.kind == 'paint':
            # TODO texture
            max_width = [5, 10, 15][stroke_size]
            opacity = 1

            width = lambda p: max_width * ((p.pressure * 1) - (p.speed * .2 / 50))

            points = [(p.x, p.y, width(p), opacity, color) for p in stroke.points]
            self.draw_combined(points)

        elif self.kind == 'highlighter':
            width = [15, 20, 25][stroke_size]
            opacity = 0.4

            points = [(p.x, p.y) for p in stroke.points]
            self.draw_single(points, color, width, opacity)
            # points = " ".join([f"{p.x},{p.y}" for p in stroke.points])
            # self.output.write(f'<polyline points="{points}" style="fill:none;stroke:{color};stroke-width:{width};opacity:{opacity}" />\n')
        elif self.kind == 'calligraphy':
            max_width = [5, 10, 15][stroke_size]
            opacity = 1.0

            width = lambda p: ((-math.cos(p.direction) + 1) * .9 / 2.0 + .1) * max_width

            points = [(p.x, p.y, width(p), opacity, color) for p in stroke.points]
            self.draw_combined(points)
        else:
            print(f"Unknown pen type: {self.kind}")

    def draw_single(self, points: Iterable[Tuple[float, float]], color: Text, width: float, opacity: float):
        points = " ".join([f"{round(p[0])},{round(p[1])}" for p in points])
        self.output.write(f'<polyline points="{points}" style="fill:none;stroke:{color};stroke-width:{width};opacity:{opacity}" />\n')

    def draw_combined(self, points: Iterable[Tuple[float, float, float, float, Text]],eps: float = 1e-8):
        """
        Draw a line combined of segments between points.

        Args:
            points: An array of points. Each point should contain the following values: (x, y, width, opacity, color)
        """
        for i, p in enumerate(points[1:-1]):
            last_p = points[i]
            next_p = points[i+2]
            w = sum([last_p[2], p[2], next_p[2]]) / 3.
            self.output.write(f'<polyline points="{round(last_p[0])},{round(last_p[1])} {round(p[0])},{round(p[1])} {round(next_p[0])},{round(next_p[1])}" style="fill:none;stroke:{p[4]};stroke-width:{w};opacity:{p[3]}" />')
            last_p = p

    def side_of_line(self, lineA, lineB, p):
        return ((lineB[0] - lineA[0]) * (p[1] - lineA[1]) - (lineB[1] - lineA[1]) * (p[0] - lineA[0])) >= 0

    def draw_combined2(self, points: Iterable[Tuple[float, float, float, float, Text]], eps: float = 1e-8, min_dist_sq: float = 2.5):
        last_point = points[0]
        last_p1 = None
        last_p2 = None

        for i, p in enumerate(points[1:-1]):
            if (last_point[0] - p[0]) ** 2 + (last_point[1] - p[1]) ** 2 < min_dist_sq:
                continue
            next_point = points[i+2]

            m1 = (p[1] - last_point[1]) / (p[0] - last_point[0] + eps)
            m2 = (next_point[1] - p[1]) / (next_point[0] - p[0] + eps)

            tanA = (m2 - m1) / (1 + m1 * m2 + eps)

            alpha_1 = math.atan(m1)
            alpha = math.atan(tanA)

            midpoint = alpha_1 + .5 * alpha

            dx = p[2] * math.cos(midpoint)
            dy = p[2] * math.sin(midpoint)

            p1 = (p[0] + dx, p[1] + dy)
            p2 = (p[0] - dx, p[1] - dy)

            if last_p1 is None:
                last_p1 = last_point[0] + dx, last_point[1] + dy
                last_p2 = last_point[0] - dx, last_point[1] - dy

            order = [last_p1, p1, p2, last_p2]
            nums = [1, 2, 3, 4]

            if self.side_of_line(last_point, p, order[0]) != self.side_of_line(last_point, p, order[1]):
                order[1:3] = order[1:3][::-1]
                nums[1:3] = nums[1:3][::-1]

            if self.side_of_line(last_point, p, order[1]) != self.side_of_line(last_point, p, order[2]):
                order[2:] = order[2:][::-1]
                nums[2:] = nums[2:][::-1]
            # print(nums)

            colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'darksalmon']
            self.output.write(f'<polygon points="')
            self.output.write(" ".join([f'{round(c[0])},{round(c[1])}' for c in order]))
            # self.output.write(f'" style="fill:{p[4]};stroke:none;opacity:{p[3]}" />\n')
            self.output.write(f'" style="fill:{p[4]};stroke:{colors[i % len(colors)]};opacity:{p[3]}" />\n')
            # for j, c in enumerate(order):
            #     self.output.write(f'<circle cx="{round(c[0])}" cy="{round(c[1])}" r="1" fill="{colors[j]}" />\n')
            last_p1, last_p2, last_point = p1, p2, p
            # if i >= 1:
            #     print(i)
            #     return


class RMToSVG:
    def __init__(self, doc: RMDocument, width: int = 1404, height: int = 1872):
        self.doc = doc
        self.width = width
        self.height = height

        self.colormap = {
            0: Colors.BLACK,
            1: Colors.GRAY,
            2: Colors.WHITE,
            'highlighter': Colors.YELLOW,
        }

    def _write_page_to_textio(self, page: RMPage, output: TextIO, fill_bg: bool = True):
        output.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}">\n')

        if fill_bg:
            # TODO Add support for templates
            output.write('<rect width="100%" height="100%" fill="white" />')

        for layer in page.layers:
            for stroke in layer.strokes:
                self.draw_stroke(stroke, output)

        output.write('</svg>')

    def write(self, out: Optional[Union[Text, Iterable[TextIO]]] = None, fill_bg: bool = True):
        out = out if out is not None else f"{self.doc.metadata['visibleName']}.svg"
        if isinstance(out, (str, os.PathLike)):
            os.makedirs(out, exist_ok=True)
        for i, page in enumerate(self.doc.pages):
            if isinstance(out, str):
                with open(os.path.join(out, f"p{i+1}.svg"), 'w+') as output:
                    if page is None:
                        output.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}">\n')
                        if fill_bg:
                            output.write('<rect width="100%" height="100%" fill="white" />')
                        output.write('</svg>')
                    else:
                        self._write_page_to_textio(page, output, fill_bg)
            else:
                if page is None:
                    output.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}">\n')
                    if fill_bg:
                        output.write('<rect width="100%" height="100%" fill="white" />')
                    output.write('</svg>')
                else:
                    self._write_page_to_textio(page, out[i], fill_bg)

    def draw_stroke(self, stroke: RMStroke, output: TextIO):
        pen = RMPen(stroke.pen_type, output, self.colormap)
        pen.draw(stroke)

def to_svg(path, name, out_name=None):
    doc = RMDocument(path, name)
    svg = RMToSVG(doc)
    svg.write(out_name)

if __name__ == "__main__":
    to_svg('/home/ole-magnus/Documents/RemarkableBackup/.raw/latest/xochitl/', '2746c0ac-8c66-4241-8fbe-4c8bfb8ece7b', 'out/test')
