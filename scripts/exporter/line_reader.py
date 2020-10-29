from typing import BinaryIO, Iterable, Text

import json
import os
import glob
import struct

class RMDocument:
    def __init__(self, path: os.PathLike, name: Text):
        self.path = path
        self.name = name

        self.content_dir = os.path.join(self.path, self.name)

        with open(os.path.join(self.path, f"{self.name}.metadata")) as f:
            self.metadata = json.loads(f.read())

        with open(os.path.join(self.path, f"{self.name}.content")) as f:
            self.content_data = json.loads(f.read())

        with open(os.path.join(self.path, f"{self.name}.pagedata")) as f:
            self.pagedata = f.readlines()

        self.pages: Iterable[RMPage] = [RMPage(self.content_dir, page)
                      for page in self.content_data['pages']]


class RMPage:
    def __init__(self, path: os.PathLike, pagename: Text):
        if os.path.exists(os.path.join(path, f"{pagename}-metadata.json")):
            with open(os.path.join(path, f"{pagename}-metadata.json")) as f:
                self.metadata = json.loads(f.read())
        else:
            self.metadata = {}

        with open(os.path.join(path, f"{pagename}.rm"), 'rb') as f:
            title = str(f.read(43))
            self.version = float(title.rsplit("=")[-1].split()[0])

            [self.n_layers] = struct.unpack('<i', f.read(4))
            if self.metadata and self.n_layers != len(self.metadata["layers"]):
                raise ValueError(
                    "Layer mismatch between metadata and .rm file!")

            self.layers: Iterable[RMLayer] = [RMLayer(
                f, self.metadata['layers'][i] if self.metadata else f"layer {i}") for i in range(self.n_layers)]


class RMLayer:
    def __init__(self, f: BinaryIO, name: Text):
        self.name = name
        [self.n_strokes] = struct.unpack('<i', f.read(4))
        self.strokes: Iterable[RMStroke] = [RMStroke(f) for _ in range(self.n_strokes)]


class RMStroke:
    def __init__(self, f: BinaryIO):
        [self.pen_type] = struct.unpack('<i', f.read(4))
        [self.color] = struct.unpack('<i', f.read(4))
        [self.unknown1] = struct.unpack('<i', f.read(4))
        [self.base_size] = struct.unpack('<f', f.read(4))
        [self.unknown2] = struct.unpack('<f', f.read(4))
        [self.n_points] = struct.unpack('<i', f.read(4))
        # print([self.pen_type, self.color, self.unknown1, self.base_size, self.unknown2, self.n_points])
        self.points: Iterable[RMPoint] = [RMPoint(f) for _ in range(self.n_points)]

class RMPoint:
    def __init__(self, f):
        [self.x] = struct.unpack('<f', f.read(4))
        [self.y] = struct.unpack('<f', f.read(4))
        [self.speed] = struct.unpack('<f', f.read(4))
        [self.direction] = struct.unpack('<f', f.read(4)) # Direction in radians
        [self.width] = struct.unpack('<f', f.read(4))
        [self.pressure] = struct.unpack('<f', f.read(4))



if __name__ == "__main__":
    doc = RMDocument('sample_files/CalligraphyTest',
                     'a4e0a733-41d6-4f1a-b5eb-c6c066be990b')
