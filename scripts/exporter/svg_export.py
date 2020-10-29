from typing import Optional, Text, TextIO

import os
from line_reader import RMDocument, RMStroke, RMPoint

class Colors:
    YELLOW = 'rgb(0, 255, 255)'
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

    def __init__(self, idx, overwrite_color: bool = True):
        try:
            self.kind = RMPen.PEN_TYPES[idx]
        except KeyError:
            raise ValueError(f"Found unknown pen type: '{idx}'")

        self.overwrite_color = overwrite_color
        if self.kind == 'highlighter':
            self.width = 15.0
            self.opacity = 0.4
            self.pressure_sensitive = False
            self.direction_sensitive = False
            self.angle_sensitive = False
            self.speed_sensitive = False
            self.color = Colors.YELLOW
        if self.kind == 'calligraphy':
            self.width = 2.0
            self.opacity = 1.0
            self.pressure_sensitive = True
            self.direction_sensitive = True
            self.angle_sensitive = True
            self.speed_sensitive = False
            self.color = None

    def draw(self, stroke: RMStroke, output: TextIO):
        if abs(stroke.base_size - 1.875) < 1e-8:
            stroke_size = 0
        elif abs(stroke.base_size - 2.0) < 1e-8:
            stroke_size = 1
        else:
            stroke_size = 2
        if self.kind == 'highlighter':
            width = [15, 20, 25][stroke_size]
            opacity = 0.4
            color = Colors.YELLOW if self.overwrite_color else stroke.color

            points = " ".join([f"{p.x},{p.y}" for p in stroke.points])
            output.write(f'<polyline points="{points}" style="fill:none;stroke:{color};stroke-width:{width};opacity:{opacity}" />\n')


class RMToSVG:
    def __init__(self, doc: RMDocument, width: int = 1404, height: int = 1872):
        self.doc = doc
        self.width = width
        self.height = height

        self.colormap = {
            0: Colors.BLACK,
            1: Colors.GRAY,
            2: Colors.WHITE,
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
        pen = RMPen(stroke.pen_type)
        pen.draw(stroke, output)

def to_svg(path, name, out_name=None):
    doc = RMDocument(path, name)
    svg = RMToSVG(doc)
    svg.write(out_name)

if __name__ == "__main__":
    to_svg('sample_files/CalligraphyTest', 'a4e0a733-41d6-4f1a-b5eb-c6c066be990b', 'out/test')
