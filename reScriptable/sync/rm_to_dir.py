
import os
import json

from glob import glob

from ..exporter.pdf_export import RMToPDF
from ..exporter.line_reader import RMDocument


class RMFileTypes:
    DOCUMENT = 'DocumentType'
    FOLDER = 'CollectionType'

    ALL_TYPES = (DOCUMENT, FOLDER)


class RMFileName:
    def __init__(self, uuid, rmdata):
        self.uuid = uuid
        self.name = rmdata['visibleName']
        self.type = rmdata['type']
        self.last_modified = rmdata['lastModified']
        self.parent = rmdata['parent'] if rmdata.get(
            'parent', '') != '' else None

    def __repr__(self):
        return self.uuid

    def __str__(self):
        return self.name


class RMDirectory:
    def __init__(self, rm_path):
        self.rm_path = rm_path
        paths = glob(os.path.join(rm_path, '*.metadata'))

        trash = RMFileName('trash', {
            'visibleName': 'trash',
            'type': RMFileTypes.FOLDER,
            'lastModified': '0',
        })

        self.rmfiles = {'trash': trash}

        self.structure = {}

        for p in paths:
            uuid = p.rsplit("/")[-1].rsplit(".")[0]
            with open(p) as f:
                data = json.loads(f.read())

            self.rmfiles[uuid] = RMFileName(uuid, data)
            if self.rmfiles[uuid].type not in RMFileTypes.ALL_TYPES:
                raise ValueError(
                    f"Unknown file type: {self.rmfiles[uuid].type}")

        handled = ['trash']
        elems = list(self.rmfiles.values())
        while elems:
            cur_elem = elems.pop(0)
            if cur_elem == trash:
                continue
            if cur_elem.parent is None:
                uuid = cur_elem.uuid
                if cur_elem.type == RMFileTypes.FOLDER:
                    element = {}
                elif cur_elem.type == RMFileTypes.DOCUMENT:
                    element = cur_elem.name
                self.structure[uuid] = element
                handled.append(uuid)

            elif cur_elem.parent in handled:
                cur_folder = self.rmfiles[cur_elem.parent]
                placement = [cur_elem.parent]
                while cur_folder.parent is not None:
                    cur_folder = self.rmfiles[cur_folder.parent]
                    placement.append(cur_folder)

                if cur_folder == trash:
                    continue

                structure_choice = self.structure
                for par in placement[::-1]:
                    structure_choice = structure_choice[par]

                uuid = cur_elem.uuid
                if cur_elem.type == RMFileTypes.FOLDER:
                    element = {}
                elif cur_elem.type == RMFileTypes.DOCUMENT:
                    element = cur_elem.name
                structure_choice[uuid] = element
                handled.append(uuid)

            else:
                elems.append(cur_elem)

    def print_structure(self, tree=None, start=''):
        tree = tree if tree is not None else self.structure
        for uuid, elem in tree.items():
            if isinstance(elem, str):
                print(f"{start}{elem}")
            else:
                print(f"{start}{self.rmfiles[uuid].name}:")
                self.print_structure(elem, start + '\t')

    def to_readable(self, out_dir='out', tree=None, only_update=True):
        os.makedirs(out_dir, exist_ok=True)
        first = False
        if isinstance(only_update, bool):
            first = True
            if only_update and os.path.exists(os.path.join(out_dir, 'last_modified.json')):
                with open(os.path.join(out_dir, 'last_modified.json')) as f:
                    only_update = json.loads(f.read())
            else:
                only_update = {}

        if tree is None:
            tree = self.structure

        for uuid, elem in tree.items():
            f = self.rmfiles[uuid]
            if f.type == RMFileTypes.FOLDER:
                only_update[uuid] = f.last_modified
                new_dir = os.path.join(out_dir, f.name)
                os.makedirs(new_dir, exist_ok=True)
                self.to_readable(new_dir, elem, only_update)
            elif f.type == RMFileTypes.DOCUMENT:
                if uuid in only_update and only_update[uuid] == f.last_modified:
                    continue
                only_update[uuid] = f.last_modified
                doc = RMDocument(self.rm_path, uuid)
                to_pdf = RMToPDF(doc)
                out_name = os.path.join(out_dir, f"{f.name}.pdf")
                to_pdf.write(out_name)
            else:
                raise ValueError(f"Unknown document type: {f.type}")

        if first:
            with open(os.path.join(out_dir, 'last_modified.json'), 'w+') as f:
                json.dump(only_update, f)


if __name__ == "__main__":
    path = '/home/ole-magnus/Documents/RemarkableBackup/.raw/latest/xochitl'

    direc = RMDirectory(path)
    direc.print_structure()
    # direc.to_readable('/home/ole-magnus/Documents/RemarkableBackup/content')
