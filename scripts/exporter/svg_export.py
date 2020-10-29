from typing import Iterable, Optional, Text, TextIO, Tuple

import os
import math
from line_reader import RMDocument, RMStroke, RMPoint

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
        17: 'pen',
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
        if self.kind == 'pen':
            max_width = [1, 2, 3][stroke_size]
            
        elif self.kind == 'highlighter':
            width = [15, 20, 25][stroke_size]
            opacity = 0.4

            points = " ".join([f"{p.x},{p.y}" for p in stroke.points])
            self.output.write(f'<polyline points="{points}" style="fill:none;stroke:{color};stroke-width:{width};opacity:{opacity}" />\n')
        elif self.kind == 'calligraphy':
            max_width = [5, 10, 15][stroke_size]
            opacity = 1.0

            width = lambda p: ((-math.cos(p.direction) + 1) * .9 / 2.0 + .1) * max_width
            
            points = [(p.x, p.y, width(p), opacity, color) for p in stroke.points]

            self.draw_combined(points)
    
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
            self.output.write(f'<polyline points="{int(last_p[0])},{int(last_p[1])} {int(p[0])},{int(p[1])} {int(next_p[0])},{int(next_p[1])}" style="fill:none;stroke:{p[4]};stroke-width:{w};opacity:{p[3]}" />')
            last_p = p


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

    def write(self, out_name: Optional[Text] = None):
        out_name = out_name if out_name is not None else f"{self.doc.metadata['visibleName']}.svg"
        os.makedirs(out_name, exist_ok=True)
        for i, page in enumerate(self.doc.pages):
            with open(os.path.join(out_name, f"p{i+1}.svg"), 'w+') as output:
                output.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}">\n')

                for layer in page.layers:
                    for stroke in layer.strokes:
                        self.draw_stroke(stroke, output)

                output.write('</svg>')

    def draw_stroke(self, stroke: RMStroke, output: TextIO):
        pen = RMPen(stroke.pen_type, output, self.colormap)
        pen.draw(stroke)

def to_svg(path, name, out_name=None):
    doc = RMDocument(path, name)
    svg = RMToSVG(doc)
    svg.write(out_name)

if __name__ == "__main__":
    to_svg('sample_files/CalligraphyTest', 'a4e0a733-41d6-4f1a-b5eb-c6c066be990b', 'out/test')
